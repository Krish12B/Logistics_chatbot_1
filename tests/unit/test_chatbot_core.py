"""Tests for the shipment chatbot.

Run from the project folder with:
    python3 -m unittest -v test_chatbot

These tests need no internet access, no Groq key and no Supabase project.
The database and the embedding model are replaced by small in-memory fakes
that are built from the same data files the real system loads
(data/shipments_seed.json and data/kb.csv).
test_supabase_integration.py runs the real SQL against a Postgres database.
"""
import csv
import hashlib
import json
import math
import os
import re
import sys
import unittest
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import groq
import httpx
import numpy as np

from logistics_chatbot.core import config
from logistics_chatbot.infrastructure.database import repository as database
from logistics_chatbot.infrastructure.embeddings import sentence_transformer as embeddings
from logistics_chatbot.application.ingestion import kb_loader as ingest
from logistics_chatbot.infrastructure.vector_store import pgvector_store as knowledge_base
from logistics_chatbot.application.chatbot.orchestrator import rag_chat as chat, detect_shipment_id
from logistics_chatbot.core.errors import (
    DatabaseError,
    InvalidShipmentIdError,
    KnowledgeBaseError,
    LLMAuthError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from logistics_chatbot.infrastructure.llm.groq_client import call_llm

HELP_SNIPPET = "I can help with shipment status"
UNREACHABLE_URL = "postgresql://user:pw@127.0.0.1:1/shipments?connect_timeout=2"

# The stand-in embedder below scores lower than the real model does, so the
# tests use a lower cut-off. The real default lives in config.py.
TEST_MIN_SCORE = 0.2

# -------------------------------------------------------------------------
# Fakes
# -------------------------------------------------------------------------

STOP_WORDS = {"the", "a", "an", "of", "to", "is", "and", "or", "in", "on", "for", "my", "me",
              "what", "how", "do", "does", "i", "it", "be", "this", "that", "with", "by", "at",
              "as", "are", "was", "can", "will", "if", "your", "our", "we", "you"}


def fake_embed(text):
    """Stand-in for the embedding model: counts word stems into 384 slots.

    Texts that share words get a higher score. It is deterministic, so the
    tests always get the same result. It does not understand meaning.
    """
    vector = [0.0] * config.EMBEDDING_DIM
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if word in STOP_WORDS:
            continue
        slot = int(hashlib.md5(word[:5].encode()).hexdigest(), 16) % config.EMBEDDING_DIM
        vector[slot] += 1.0
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]


def sparse_embed(text):
    """Exact word-stem counts, normalised. The unit tests use this one because it has no
    hash collisions, so a word can never accidentally match an unrelated word.
    The dense fake_embed above is still used by the integration tests, which need 384 dims."""
    counts = Counter(word[:5] for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP_WORDS)
    norm = math.sqrt(sum(v * v for v in counts.values())) or 1.0
    return {stem: v / norm for stem, v in counts.items()}


class FakeShipmentStore:
    """Serves shipment rows the way the Supabase shipments table does."""

    def __init__(self):
        self._rows = {row["shipment_id"]: row for row in ingest.load_shipment_rows()}

    def fetch_shipment_row(self, shipment_id):
        row = self._rows.get(shipment_id)
        return dict(row) if row else None


class FakeKnowledgeStore:
    """Runs the similarity search in memory, the way match_knowledge does in Supabase."""

    def __init__(self):
        self._rows = ingest.load_kb_rows()
        self._vectors = [sparse_embed(ingest.knowledge_embedding_text(row)) for row in self._rows]

    def fetch_matches(self, query_vector, top_k, min_score):
        scored = []
        for row, vector in zip(self._rows, self._vectors):
            score = sum(weight * vector.get(stem, 0.0) for stem, weight in query_vector.items())
            if score >= min_score:
                scored.append({
                    "doc_id": row["doc_id"],
                    "category": row["category"],
                    "section_title": row["section_title"],
                    "content": row["content"],
                    "score": score,
                })
        scored.sort(key=lambda match: match["score"], reverse=True)
        return scored[:top_k]


def offline_llm(messages):
    """Stand-in for Groq. It echoes the CONTEXT it received, so the tests can
    check that the right facts were retrieved and passed to the model."""
    prompt = messages[-1]["content"]
    context = prompt.split("\n\nUSER QUESTION:")[0]
    return "OFFLINE TEST REPLY\n" + context


# -------------------------------------------------------------------------
# Chatbot behaviour
# -------------------------------------------------------------------------

class ChatbotBehaviourTests(unittest.TestCase):

    def setUp(self):
        self.shipments = FakeShipmentStore()
        self.knowledge = FakeKnowledgeStore()

        self.shipment_fake = patch.object(
            database, "fetch_shipment_row", side_effect=self.shipments.fetch_shipment_row
        )
        self.shipment_fake.start()
        patch.object(knowledge_base, "fetch_matches", side_effect=self.knowledge.fetch_matches).start()
        patch.object(embeddings, "embed_query", side_effect=sparse_embed).start()
        patch.object(config, "RETRIEVAL_MIN_SCORE", TEST_MIN_SCORE).start()
        self.llm = patch("logistics_chatbot.application.chatbot.orchestrator.call_llm", side_effect=offline_llm).start()
        self.addCleanup(patch.stopall)

    # ---- The five required query types -------------------------------------

    def test_shipment_status(self):
        reply = chat("What is the status of SHP-10001?")
        self.assertIn("Status: In Transit", reply)
        self.assertIn("Current location: Dubai Hub, UAE", reply)
        self.assertIn("Last updated: 2026-11-15 18:30", reply)
        self.llm.assert_called_once()

    def test_shipment_delay(self):
        reply = chat("Why is SHP-10002 delayed?")
        self.assertIn("Delay reason: Port congestion at Jebel Ali", reply)
        self.assertIn("[FAQ-LEGACY-DELAY]", reply)

    def test_customs_query(self):
        reply = chat("Has SHP-10003 cleared customs?")
        self.assertIn("Customs status: Held - awaiting commercial invoice", reply)
        self.assertIn("[FAQ-LEGACY-CUSTOMS]", reply)

    def test_delivery_route_query(self):
        reply = chat("What is the delivery route for SHP-10001?")
        self.assertIn("Route: Mumbai Hub -> Dubai Hub -> London Heathrow Hub", reply)

    def test_unknown_shipment_id(self):
        reply = chat("Where is SHP-99999?")
        self.assertIn("I couldn't find shipment SHP-99999", reply)
        self.llm.assert_not_called()

    # ---- Extra behaviour ---------------------------------------------------

    def test_malformed_shipment_id(self):
        reply = chat("Track SHP-12 for me")
        self.assertIn("doesn't look like a valid shipment ID", reply)
        self.llm.assert_not_called()

    def test_general_question_uses_knowledge_base_only(self):
        reply = chat("What causes shipment delays?")
        self.assertIn("[FAQ-LEGACY-DELAY]", reply)
        self.assertNotIn("SHIPMENT RECORD", reply)

    def test_off_topic_message_gets_help_text(self):
        reply = chat("Tell me a joke")
        self.assertIn(HELP_SNIPPET, reply)
        self.llm.assert_not_called()

    # ---- Error handling ----------------------------------------------------

    def test_empty_message(self):
        reply = chat("     ")
        self.assertIn("Please type a question", reply)
        self.llm.assert_not_called()

    def test_api_timeout(self):
        self.llm.side_effect = LLMTimeoutError(detail="simulated timeout")
        reply = chat("Status of SHP-10001")
        self.assertIn("took too long to respond", reply)

    def test_invalid_api_key(self):
        self.llm.side_effect = LLMAuthError(detail="simulated 401")
        reply = chat("Status of SHP-10001")
        self.assertIn("not set up correctly", reply)

    def test_database_connection_failure(self):
        # Let the real database code run, pointed at a port nothing listens on.
        self.shipment_fake.stop()
        try:
            with patch.object(config, "SUPABASE_DB_URL", UNREACHABLE_URL), \
                    patch.object(database, "_connection", None):
                reply = chat("Status of SHP-10001")
        finally:
            self.shipment_fake.start()
        self.assertIn("can't reach our shipment database", reply)
        self.llm.assert_not_called()

    def test_embedding_failure_is_reported_to_the_customer(self):
        with patch.object(embeddings, "embed_query",
                          side_effect=KnowledgeBaseError(detail="model download failed")), \
                patch("logistics_chatbot.application.rag.retriever._offline_keyword_search",
                      side_effect=KnowledgeBaseError(detail="offline index unavailable")):
            reply = chat("What causes shipment delays?")
        self.assertIn("having trouble loading our help articles", reply)
        self.llm.assert_not_called()

    def test_unexpected_exception_is_caught(self):
        self.llm.side_effect = RuntimeError("something nobody planned for")
        reply = chat("Status of SHP-10001")
        self.assertIn("unexpected", reply)


# -------------------------------------------------------------------------
# Shipment ID detection
# -------------------------------------------------------------------------

class ShipmentIdDetectionTests(unittest.TestCase):

    def test_standard_id(self):
        self.assertEqual(detect_shipment_id("Track SHP-10001"), "SHP-10001")

    def test_lower_case_and_missing_dash_are_normalised(self):
        self.assertEqual(detect_shipment_id("track shp10002 please"), "SHP-10002")

    def test_no_id_returns_none(self):
        self.assertIsNone(detect_shipment_id("What are your customs rules?"))

    def test_wrong_length_raises(self):
        with self.assertRaises(InvalidShipmentIdError):
            detect_shipment_id("SHP-123456")


# -------------------------------------------------------------------------
# Supabase connection and schema checks (no real database needed)
# -------------------------------------------------------------------------

class SupabaseConnectionTests(unittest.TestCase):

    def test_missing_supabase_url_is_reported(self):
        with patch.object(config, "SUPABASE_DB_URL", ""), patch.object(database, "_connection", None):
            with self.assertRaises(DatabaseError) as ctx:
                database.init_database()
        self.assertIn("SUPABASE_DB_URL is not set", ctx.exception.detail)

    def test_init_reports_missing_schema_parts(self):
        status_row = {"shipments_table": True, "knowledge_table": False, "match_function": False}
        with patch.object(database, "run_query", return_value=[status_row]):
            with self.assertRaises(DatabaseError) as ctx:
                database.init_database()
        self.assertIn("knowledge_base table", ctx.exception.detail)
        self.assertIn("match_knowledge function", ctx.exception.detail)
        self.assertIn("schema.sql", ctx.exception.detail)

    def test_init_passes_when_schema_exists(self):
        status_row = {"shipments_table": True, "knowledge_table": True, "match_function": True}
        with patch.object(database, "run_query", return_value=[status_row]):
            database.init_database()  # no exception

    def test_shipment_dates_are_formatted_like_before(self):
        with patch.object(database, "fetch_shipment_row", return_value={
            "shipment_id": "SHP-1", "origin": "A", "destination": "B", "status": "Delivered",
            "current_location": "B", "route": "A -> B", "estimated_delivery": date(2026, 11, 10),
            "delay_reason": None, "customs_status": "Cleared",
            "last_updated": datetime(2026, 11, 10, 14, 45),
        }):
            shipment = database.get_shipment("SHP-1")
        self.assertEqual(shipment["estimated_delivery"], "2026-11-10")
        self.assertEqual(shipment["last_updated"], "2026-11-10 14:45")


# -------------------------------------------------------------------------
# Embeddings and vector format
# -------------------------------------------------------------------------

class VectorTests(unittest.TestCase):

    def test_to_pgvector_format(self):
        self.assertEqual(knowledge_base.to_pgvector([0.5, -1.0, 0.25]), "[0.5,-1.0,0.25]")

    def test_wrong_embedding_size_is_rejected(self):
        class WrongSizeModel:
            def query_embed(self, texts):
                return iter([np.zeros(10, dtype=np.float32)])

        with patch.object(embeddings, "_get_model", return_value=WrongSizeModel()):
            with self.assertRaises(KnowledgeBaseError) as ctx:
                embeddings.embed_query("anything")
        self.assertIn("expects 384", ctx.exception.detail)

    def test_correct_embedding_size_is_returned_as_list(self):
        class RightSizeModel:
            def query_embed(self, texts):
                return iter([np.ones(config.EMBEDDING_DIM, dtype=np.float32)])

        with patch.object(embeddings, "_get_model", return_value=RightSizeModel()):
            vector = embeddings.embed_query("anything")
        self.assertIsInstance(vector, list)
        self.assertEqual(len(vector), config.EMBEDDING_DIM)


# -------------------------------------------------------------------------
# Loading the source files
# -------------------------------------------------------------------------

class IngestFileTests(unittest.TestCase):

    def test_seed_dates_are_parsed(self):
        first = ingest.load_shipment_rows()[0]
        self.assertEqual(first["estimated_delivery"], date(2026, 11, 20))
        self.assertEqual(first["last_updated"], datetime(2026, 11, 15, 18, 30))

    def test_knowledge_rows_include_csv_and_legacy_faqs(self):
        rows = ingest.load_kb_rows()
        ids = [row["doc_id"] for row in rows]
        with open(config.KB_CSV_PATH, encoding="utf-8-sig", newline="") as f:
            csv_count = sum(1 for _ in csv.DictReader(f))
        with open(config.LEGACY_FAQ_PATH, encoding="utf-8") as f:
            legacy_count = len(json.load(f)["faqs"])
        txt_ids = [doc_id for doc_id in ids if doc_id.startswith("TXT-")]
        self.assertGreater(len(txt_ids), 0)
        self.assertEqual(len(rows), csv_count + len(txt_ids) + legacy_count)
        self.assertEqual(len(set(ids)), len(ids))
        self.assertIn("FAQ-LEGACY-CUSTOMS", ids)  # the CSV has no customs answer, so this one matters
        self.assertIn("SS-004", ids)

    def test_embedding_text_has_title_content_and_tags(self):
        row = next(r for r in ingest.load_kb_rows() if r["doc_id"] == "SS-004")
        text = ingest.knowledge_embedding_text(row)
        self.assertIn("Status: Delayed / On Hold", text)
        self.assertIn("reason code", text)
        self.assertIn("Tags: status;delayed;on hold;reason code", text)

    def test_empty_knowledge_load_never_deletes_existing_rows(self):
        with self.assertRaises(ValueError):
            ingest.sync_knowledge([])


# -------------------------------------------------------------------------
# Groq error mapping
# -------------------------------------------------------------------------

class GroqErrorMappingTests(unittest.TestCase):
    """Checks that real Groq SDK errors are turned into our own error types."""

    REQUEST = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    MESSAGES = [{"role": "user", "content": "hello"}]

    def _call_when_groq_fails(self, error):
        fake_client = MagicMock()
        fake_client.chat.completions.create.side_effect = error
        with patch.object(config, "GROQ_API_KEY", "gsk_test_key"), \
                patch("groq.Groq", return_value=fake_client):
            return call_llm(self.MESSAGES)

    def test_timeout_becomes_LLMTimeoutError(self):
        with self.assertRaises(LLMTimeoutError):
            self._call_when_groq_fails(groq.APITimeoutError(request=self.REQUEST))

    def test_invalid_key_becomes_LLMAuthError(self):
        response = httpx.Response(401, request=self.REQUEST)
        error = groq.AuthenticationError("Invalid API Key", response=response, body=None)
        with self.assertRaises(LLMAuthError):
            self._call_when_groq_fails(error)

    def test_no_internet_becomes_LLMUnavailableError(self):
        with self.assertRaises(LLMUnavailableError):
            self._call_when_groq_fails(groq.APIConnectionError(request=self.REQUEST))

    def test_missing_key_is_caught_before_calling_groq(self):
        with patch.object(config, "GROQ_API_KEY", ""):
            with self.assertRaises(LLMAuthError):
                call_llm(self.MESSAGES)


if __name__ == "__main__":
    unittest.main()
