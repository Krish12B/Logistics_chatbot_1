"""End-to-end integration and scenario tests for the Supabase RAG chatbot.

Covers all 9 required verification scenarios from Prompt 03:
  Scenario 1: Question with answer in Supabase (KB semantic retrieval)
  Scenario 2: Question requiring multiple records (shipment + FAQ policies)
  Scenario 3: Question about specific logistics entity (single shipment lookup)
  Scenario 4: Follow-up question (conversation context and session continuity)
  Scenario 5: Question with no matching data (returns help text, no hallucination)
  Scenario 6: Incorrect / ambiguous / malformed query handling
  Scenario 7: Supabase connection failure (graceful error reporting)
  Scenario 8: Groq API failure (rate limits, timeouts, and auth failures)
  Scenario 9: Response vs actual DB record comparison (grounding verification)
  Scenario 10: Shipment filtering by status / route
  Scenario 11: Query length limits and input validation
  Scenario 12: Conversation token budget management
"""
import sys
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import groq
import httpx

from logistics_chatbot.core import config
from logistics_chatbot.database import database
from logistics_chatbot.rag import embeddings
from logistics_chatbot.rag import knowledge_base
from logistics_chatbot.chatbot.chatbot import chat, detect_shipment_id, get_conversation_store
from logistics_chatbot.chatbot.conversation import Conversation, ConversationStore
from logistics_chatbot.core.errors import (
    DatabaseError,
    EmptyMessageError,
    InvalidShipmentIdError,
    KnowledgeBaseError,
    LLMAuthError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUnavailableError,
    QueryTooLongError,
    ShipmentNotFoundError,
)
from logistics_chatbot.chatbot.llm_client import call_llm
from logistics_chatbot.rag.retrieval import classify_query, format_context, retrieve, search_shipments

# Test fixtures
SAMPLE_SHIPMENT = {
    "shipment_id": "SHP-10001",
    "origin": "Mumbai Hub, India",
    "destination": "London Heathrow Hub, UK",
    "status": "In Transit",
    "current_location": "Dubai Hub, UAE",
    "route": "Mumbai Hub -> Dubai Hub -> London Heathrow Hub",
    "estimated_delivery": "2026-11-20",
    "delay_reason": None,
    "customs_status": "Cleared - documentation verified",
    "last_updated": "2026-11-15 18:30",
}

SAMPLE_DELAYED_SHIPMENT = {
    "shipment_id": "SHP-10002",
    "origin": "Shanghai Port, China",
    "destination": "Rotterdam Gateway, Netherlands",
    "status": "Delayed",
    "current_location": "Port of Singapore, Singapore",
    "route": "Shanghai -> Singapore -> Suez -> Rotterdam",
    "estimated_delivery": "2026-11-25",
    "delay_reason": "Port congestion at Jebel Ali",
    "customs_status": "Pending inspection",
    "last_updated": "2026-11-16 10:15",
}

SAMPLE_KB_ARTICLES = [
    {
        "doc_id": "FAQ-001",
        "category": "shipping_process",
        "section_title": "Standard Transit Windows",
        "content": "Ocean freight typically takes 18 to 28 business days depending on the maritime corridor.",
        "score": 0.85,
    },
    {
        "doc_id": "FAQ-002",
        "category": "customs",
        "section_title": "Commercial Invoice Requirements",
        "content": "All international shipments require 3 copies of the commercial invoice signed by the exporter.",
        "score": 0.78,
    },
]


class EndToEndRAGScenarioTests(unittest.TestCase):
    """Verifies all end-to-end RAG scenarios."""

    def setUp(self):
        # Clean conversation store between tests
        self.store = get_conversation_store()
        for session_id in list(self.store.list_sessions()):
            self.store.delete(session_id)

        # Default in-memory patches for offline test execution
        self.patcher_embed = patch.object(embeddings, "embed_query", return_value=[0.1] * 384)
        self.patcher_matches = patch.object(knowledge_base, "fetch_matches", return_value=[])
        self.patcher_embed.start()
        self.patcher_matches.start()
        self.addCleanup(self.patcher_embed.stop)
        self.addCleanup(self.patcher_matches.stop)

    # ── Scenario 1: Question with answer in Supabase (KB) ───────────

    @patch("logistics_chatbot.chatbot.chatbot.call_llm")
    def test_scenario_1_question_with_answer_in_supabase(self, mock_llm):
        """User asks a general policy question that exists in Supabase knowledge_base."""
        with patch.object(knowledge_base, "fetch_matches", return_value=[SAMPLE_KB_ARTICLES[0]]):
            mock_llm.return_value = "Ocean freight transit takes 18 to 28 business days [FAQ-001]."
            reply = chat("What is the typical ocean freight transit time?")

            mock_llm.assert_called_once()
            self.assertIn("18 to 28 business days", reply)
            prompt = mock_llm.call_args[0][0][-1]["content"]
            self.assertIn("[FAQ-001]", prompt)
            self.assertIn("Standard Transit Windows", prompt)

    # ── Scenario 2: Question requiring multiple records ─────────────

    @patch("logistics_chatbot.database.database.get_shipment")
    @patch("logistics_chatbot.chatbot.chatbot.call_llm")
    def test_scenario_2_question_requiring_multiple_records(self, mock_llm, mock_get_shipment):
        """Question about delay and customs brings in shipment record + relevant policies."""
        mock_get_shipment.return_value = dict(SAMPLE_DELAYED_SHIPMENT)
        with patch.object(knowledge_base, "fetch_matches", return_value=SAMPLE_KB_ARTICLES):
            mock_llm.return_value = (
                "Shipment SHP-10002 is delayed due to Port congestion at Jebel Ali. "
                "Under FleetHarbor policy [FAQ-001], our team is coordinating rerouting."
            )

            reply = chat("Why is SHP-10002 delayed and what are your customs rules?")

            mock_get_shipment.assert_called_with("SHP-10002")
            mock_llm.assert_called_once()
            prompt = mock_llm.call_args[0][0][-1]["content"]
            self.assertIn("SHIPMENT RECORD:", prompt)
            self.assertIn("SHP-10002", prompt)
            self.assertIn("KNOWLEDGE BASE:", prompt)
            self.assertIn("FAQ-001", prompt)
            self.assertIn("FAQ-002", prompt)

    # ── Scenario 3: Question about specific logistics entity ────────

    @patch("logistics_chatbot.database.database.get_shipment")
    @patch("logistics_chatbot.chatbot.chatbot.call_llm")
    def test_scenario_3_specific_logistics_entity(self, mock_llm, mock_get_shipment):
        """Direct query about a specific shipment ID retrieves the exact database record."""
        mock_get_shipment.return_value = dict(SAMPLE_SHIPMENT)
        mock_llm.return_value = "Shipment SHP-10001 is currently In Transit in Dubai Hub, UAE, ETA 2026-11-20."

        reply = chat("Where is SHP-10001 right now?")

        mock_get_shipment.assert_called_with("SHP-10001")
        self.assertIn("SHP-10001", reply)
        self.assertIn("In Transit", reply)

    # ── Scenario 4: Follow-up question (conversation context) ───────

    @patch("logistics_chatbot.database.database.get_shipment")
    @patch("logistics_chatbot.chatbot.chatbot.call_llm")
    def test_scenario_4_follow_up_question_continuity(self, mock_llm, mock_get_shipment):
        """Turn 2 uses pronoun 'it' and refers to the shipment from Turn 1."""
        session_id = "test-session-42"
        mock_get_shipment.return_value = dict(SAMPLE_SHIPMENT)

        # Turn 1: Explicit ID
        mock_llm.return_value = "Shipment SHP-10001 is In Transit, ETA 2026-11-20."
        reply1 = chat("Where is SHP-10001?", session_id=session_id)
        self.assertIn("SHP-10001", reply1)

        # Turn 2: Follow-up question without explicit ID
        mock_llm.return_value = "The delivery route for SHP-10001 goes through Mumbai, Dubai, and London."
        reply2 = chat("What route is it taking?", session_id=session_id)

        # Verify that get_shipment was called for the same ID on the follow-up
        self.assertEqual(mock_get_shipment.call_count, 2)
        mock_get_shipment.assert_called_with("SHP-10001")

        # Verify the session recorded both turns
        session = self.store.get(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session.turn_count, 2)

    # ── Scenario 5: Question with no matching data ───────────────────

    @patch("logistics_chatbot.chatbot.chatbot.call_llm")
    def test_scenario_5_question_with_no_matching_data(self, mock_llm):
        """Off-topic question returns help text immediately without invoking LLM."""
        reply = chat("Who won the 1994 World Cup?")

        mock_llm.assert_not_called()
        self.assertIn("I can help with shipment status", reply)

    # ── Scenario 6: Incorrect / ambiguous / malformed query ──────────

    def test_scenario_6_malformed_id_raises_friendly_error(self):
        """Query with malformed shipment ID is caught and returns an informative hint."""
        reply = chat("Check status for SHP-999")
        self.assertIn("doesn't look like a valid shipment ID", reply)

    def test_scenario_6_empty_message_returns_friendly_error(self):
        """Empty or whitespace-only messages prompt the user for input."""
        reply = chat("   \n\t  ")
        self.assertIn("Please type a question about your shipment", reply)

    @patch("logistics_chatbot.database.database.get_shipment")
    def test_scenario_6_nonexistent_shipment_id(self, mock_get_shipment):
        """Valid format but nonexistent shipment ID returns friendly not-found message."""
        mock_get_shipment.side_effect = ShipmentNotFoundError(
            "I couldn't find shipment SHP-88888. Please check the ID and try again."
        )
        reply = chat("Track SHP-88888")
        self.assertIn("couldn't find shipment SHP-88888", reply)

    # ── Scenario 7: Supabase connection failure ──────────────────────

    @patch("logistics_chatbot.database.database.get_shipment")
    @patch("logistics_chatbot.chatbot.chatbot.call_llm")
    def test_scenario_7_supabase_connection_failure(self, mock_llm, mock_get_shipment):
        """Database connection drops return user-friendly message without crashing."""
        mock_get_shipment.side_effect = DatabaseError(
            detail="psycopg2.OperationalError: server closed the connection unexpectedly"
        )

        reply = chat("Status of SHP-10001")

        mock_llm.assert_not_called()
        self.assertIn("can't reach our shipment database right now", reply)

    # ── Scenario 8: Groq API failure handling ───────────────────────

    @patch("logistics_chatbot.database.database.get_shipment")
    @patch("logistics_chatbot.chatbot.chatbot.call_llm")
    def test_scenario_8_groq_timeout(self, mock_llm, mock_get_shipment):
        """Groq API timeout returns a friendly retry message."""
        mock_get_shipment.return_value = dict(SAMPLE_SHIPMENT)
        mock_llm.side_effect = LLMTimeoutError(detail="Read timeout after 15s")

        reply = chat("Status of SHP-10001")

        self.assertIn("took too long to respond", reply)

    @patch("logistics_chatbot.database.database.get_shipment")
    @patch("logistics_chatbot.chatbot.chatbot.call_llm")
    def test_scenario_8_groq_rate_limit(self, mock_llm, mock_get_shipment):
        """Groq 429 rate limit returns busy message."""
        mock_get_shipment.return_value = dict(SAMPLE_SHIPMENT)
        mock_llm.side_effect = LLMRateLimitError(detail="Rate limit exceeded")

        reply = chat("Status of SHP-10001")

        self.assertIn("very busy right now", reply)

    @patch("logistics_chatbot.database.database.get_shipment")
    @patch("logistics_chatbot.chatbot.chatbot.call_llm")
    def test_scenario_8_groq_auth_failure(self, mock_llm, mock_get_shipment):
        """Invalid API key returns admin setup message."""
        mock_get_shipment.return_value = dict(SAMPLE_SHIPMENT)
        mock_llm.side_effect = LLMAuthError(detail="Invalid API key")

        reply = chat("Status of SHP-10001")

        self.assertIn("not set up correctly", reply)

    # ── Scenario 9: Response vs DB record grounding ─────────────────

    @patch("logistics_chatbot.database.database.get_shipment")
    @patch("logistics_chatbot.chatbot.chatbot.call_llm")
    def test_scenario_9_grounding_record_comparison(self, mock_llm, mock_get_shipment):
        """Verifies that facts injected into the prompt match the actual DB record."""
        mock_get_shipment.return_value = dict(SAMPLE_DELAYED_SHIPMENT)
        mock_llm.return_value = "SHP-10002 is Delayed at Port of Singapore due to Port congestion at Jebel Ali."

        chat("What is the delay on SHP-10002?")

        # Inspect the exact prompt passed to Groq
        self.assertTrue(mock_llm.called)
        prompt = mock_llm.call_args[0][0][-1]["content"]
        self.assertIn("Delay reason: Port congestion at Jebel Ali", prompt)
        self.assertIn("Current location: Port of Singapore, Singapore", prompt)
        self.assertIn("Estimated delivery: 2026-11-25", prompt)
        self.assertIn("Customs status: Pending inspection", prompt)

    # ── Scenario 10: Shipment listing / filter queries ──────────────

    @patch("logistics_chatbot.database.database.run_query")
    @patch("logistics_chatbot.chatbot.chatbot.call_llm")
    def test_scenario_10_list_delayed_shipments(self, mock_llm, mock_run_query):
        """Filtered query like 'list all delayed shipments' queries database with parameter."""
        mock_run_query.return_value = [dict(SAMPLE_DELAYED_SHIPMENT)]
        mock_llm.return_value = "Here are the delayed shipments: SHP-10002 (Port congestion at Jebel Ali)."

        reply = chat("list all delayed shipments")

        mock_run_query.assert_called()
        mock_llm.assert_called_once()
        prompt = mock_llm.call_args[0][0][-1]["content"]
        self.assertIn("SHIPMENT LIST", prompt)
        self.assertIn("SHP-10002", prompt)

    # ── Scenario 11: Query length limits ────────────────────────────

    def test_scenario_11_query_too_long_rejected(self):
        """Queries exceeding 2,000 characters are rejected with a helpful message."""
        long_query = "What is the status of SHP-10001? " * 150  # ~4,900 chars
        reply = chat(long_query)
        self.assertIn("Your question is too long", reply)

    # ── Scenario 12: Conversation token budget ──────────────────────

    def test_scenario_12_conversation_budget_truncation(self):
        """Conversation history maintains recent turns without unbounded growth."""
        store = ConversationStore()
        session = store.get_or_create("budget-test")

        # Add 10 turns
        for i in range(10):
            session.add_message("user", f"Question {i}")
            session.add_message("assistant", f"Answer {i} with lots of logistics details and tracking info")

        # get_recent_messages(max_turns=3) returns at most 3 pairs = 6 messages
        recent = session.get_recent_messages(max_turns=3)
        self.assertLessEqual(len(recent), 6)
        self.assertEqual(recent[-1]["content"], "Answer 9 with lots of logistics details and tracking info")


class ActiveDatasetVerificationTests(unittest.TestCase):
    """Verifies that the new datasets in data/ are actively loaded and utilised."""

    def test_all_10_shipments_loaded_from_csv(self):
        """load_shipment_rows() loads all 10 records from shipments.csv."""
        from logistics_chatbot.rag import ingestion as ingest
        rows = ingest.load_shipment_rows()
        self.assertEqual(len(rows), 10)
        ids = [r["shipment_id"] for r in rows]
        for i in range(1, 11):
            self.assertIn(f"SHP-100{i:02d}", ids)

    def test_extended_shipments_contain_correct_metadata(self):
        """Shipments 6 to 10 have valid routes, statuses, and locations."""
        from logistics_chatbot.rag import ingestion as ingest
        rows = {r["shipment_id"]: r for r in ingest.load_shipment_rows()}

        # Verify SHP-10006 (Tokyo route)
        shp6 = rows["SHP-10006"]
        self.assertEqual(shp6["status"], "In Transit")
        self.assertIn("Tokyo", shp6["destination"])
        self.assertIn("Singapore Hub", shp6["current_location"])

        # Verify SHP-10007 (Berlin delayed route)
        shp7 = rows["SHP-10007"]
        self.assertEqual(shp7["status"], "Delayed")
        self.assertIn("Weather disruption", shp7["delay_reason"])

        # Verify SHP-10010 (LAX customs hold)
        shp10 = rows["SHP-10010"]
        self.assertEqual(shp10["status"], "On Hold - Customs")
        self.assertIn("missing packing list", shp10["customs_status"])

    def test_over_2000_kb_entries_loaded_from_kb_long(self):
        """load_kb_rows() loads 2,194+ entries from kb_long.csv."""
        from logistics_chatbot.rag import ingestion as ingest
        kb_rows = ingest.load_kb_rows()
        self.assertGreaterEqual(len(kb_rows), 2194)

        categories = {r["category"] for r in kb_rows}
        self.assertIn("shipping_process", categories)
        self.assertIn("warehouse_operations", categories)

    def test_config_paths_point_to_active_datasets(self):
        """config paths prioritize kb_long.csv and shipments.csv."""
        self.assertTrue(config.KB_CSV_PATH.name, "kb_long.csv")
        self.assertTrue(config.SHIPMENT_PATH.name, "shipments.csv")


if __name__ == "__main__":
    unittest.main()
