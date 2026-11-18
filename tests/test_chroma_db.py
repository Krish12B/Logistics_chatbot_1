"""Comprehensive verification tests for ChromaDB Vector Database integration.

Verifies:
  1. ChromaDB PersistentClient initialization and configuration
  2. Health check and heartbeat monitoring
  3. Collection creation with cosine distance metric ('hnsw:space': 'cosine')
  4. Upsert of knowledge chunks adhering to 12-item schema
  5. Upsert idempotency (updating without duplication)
  6. Semantic vector search and distance-to-similarity conversion
  7. Metadata filtering (e.g. category, doc_type)
  8. Ingest from knowledge base (kb_long.csv / legacy FAQs)
  9. Persistence across client restarts
  10. Server (HTTP) mode configuration and error handling
  11. Retrieval layer integration with ChromaDB as primary vector store
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import chromadb

from logistics_chatbot.core import config
from logistics_chatbot.core.errors import KnowledgeBaseError, VectorDBError
from logistics_chatbot.rag import embeddings
from logistics_chatbot.vectorstores import chroma_db


class ChromaDBConnectionTests(unittest.TestCase):
    """Verifies ChromaDB connection, initialization, and health checks."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="chroma_test_")
        self.original_persist_dir = config.CHROMA_PERSIST_DIRECTORY
        self.original_mode = config.CHROMA_MODE
        self.original_col = config.CHROMA_COLLECTION_NAME

        config.CHROMA_PERSIST_DIRECTORY = Path(self.temp_dir)
        config.CHROMA_MODE = "persistent"
        config.CHROMA_COLLECTION_NAME = "test_logistics_chunks"
        chroma_db.close()

    def tearDown(self):
        chroma_db.close()
        config.CHROMA_PERSIST_DIRECTORY = self.original_persist_dir
        config.CHROMA_MODE = self.original_mode
        config.CHROMA_COLLECTION_NAME = self.original_col
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_persistent_client_initialization(self):
        """Verifies PersistentClient creates directory and returns live client."""
        client = chroma_db.get_chroma_client()
        self.assertIsNotNone(client)
        self.assertTrue(Path(self.temp_dir).exists())
        self.assertIsInstance(client, chromadb.api.ClientAPI)

    def test_heartbeat_and_health_check(self):
        """Verifies health check reports status=healthy and a valid heartbeat."""
        health = chroma_db.check_chroma_health()
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["mode"], "persistent")
        self.assertGreater(health["heartbeat"], 0)
        self.assertEqual(health["collection_name"], "test_logistics_chunks")
        self.assertEqual(health["record_count"], 0)

    def test_singleton_client_reuse(self):
        """Verifies get_chroma_client() reuses the cached client unless reset=True."""
        client1 = chroma_db.get_chroma_client()
        client2 = chroma_db.get_chroma_client()
        self.assertIs(client1, client2)

        client3 = chroma_db.get_chroma_client(reset=True)
        self.assertIsNotNone(client3)

    def test_unsupported_mode_raises_error(self):
        """Verifies an invalid CHROMA_MODE raises VectorDBError."""
        config.CHROMA_MODE = "invalid_mode"
        with self.assertRaises(VectorDBError) as ctx:
            chroma_db.get_chroma_client(reset=True)
        self.assertIn("Unsupported CHROMA_MODE", str(ctx.exception.detail))

    @patch("chromadb.HttpClient")
    def test_http_mode_configuration(self, mock_http):
        """Verifies HTTP mode initializes chromadb.HttpClient with configured host/port."""
        mock_instance = MagicMock()
        mock_instance.heartbeat.return_value = 12345
        mock_http.return_value = mock_instance

        config.CHROMA_MODE = "http"
        config.CHROMA_HOST = "remote-chroma.internal"
        config.CHROMA_PORT = 9000
        config.CHROMA_SSL = True
        config.CHROMA_API_KEY = "test-token-xyz"

        client = chroma_db.get_chroma_client(reset=True)
        mock_http.assert_called_once()
        kwargs = mock_http.call_args[1]
        self.assertEqual(kwargs["host"], "remote-chroma.internal")
        self.assertEqual(kwargs["port"], 9000)
        self.assertTrue(kwargs["ssl"])
        self.assertEqual(kwargs["headers"], {"X-Chroma-Token": "test-token-xyz"})


class ChromaDBCollectionAndStorageTests(unittest.TestCase):
    """Verifies collection creation, 12-item schema upsert, search, and persistence."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="chroma_storage_test_")
        self.original_persist_dir = config.CHROMA_PERSIST_DIRECTORY
        self.original_mode = config.CHROMA_MODE
        self.original_col = config.CHROMA_COLLECTION_NAME

        config.CHROMA_PERSIST_DIRECTORY = Path(self.temp_dir)
        config.CHROMA_MODE = "persistent"
        config.CHROMA_COLLECTION_NAME = "test_logistics_chunks"
        chroma_db.close()

    def tearDown(self):
        chroma_db.close()
        config.CHROMA_PERSIST_DIRECTORY = self.original_persist_dir
        config.CHROMA_MODE = self.original_mode
        config.CHROMA_COLLECTION_NAME = self.original_col
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_collection_creation_with_cosine_metric(self):
        """Verifies collection is created with cosine distance metadata."""
        col = chroma_db.get_or_create_collection()
        self.assertEqual(col.name, "test_logistics_chunks")
        self.assertEqual(col.metadata.get("hnsw:space"), "cosine")

    def test_upsert_12_item_schema(self):
        """Verifies chunks conforming to the 12-item schema are stored with metadata."""
        mock_embedding = [0.05] * 384
        sample_chunk = {
            "chunk_id": "DOC-101_0",
            "doc_id": "DOC-101",
            "title": "Air Freight Priority Rules",
            "content": "Perishable goods must use Priority Express Air Freight within 24 hours.",
            "embedding": mock_embedding,
            "source": "kb_long.csv",
            "doc_type": "policy",
            "category": "air_freight",
            "language": "en",
            "chunk_index": 0,
            "timestamp": "2026-11-15T12:00:00Z",
            "content_hash": "a1b2c3d4e5f60718",
        }

        count = chroma_db.upsert_knowledge_chunks([sample_chunk])
        self.assertEqual(count, 1)

        col = chroma_db.get_or_create_collection()
        self.assertEqual(col.count(), 1)

        result = col.get(ids=["DOC-101_0"], include=["documents", "metadatas"])
        self.assertEqual(result["documents"][0], sample_chunk["content"])
        meta = result["metadatas"][0]
        self.assertEqual(meta["doc_id"], "DOC-101")
        self.assertEqual(meta["title"], "Air Freight Priority Rules")
        self.assertEqual(meta["source"], "kb_long.csv")
        self.assertEqual(meta["doc_type"], "policy")
        self.assertEqual(meta["category"], "air_freight")
        self.assertEqual(meta["language"], "en")
        self.assertEqual(meta["chunk_index"], 0)
        self.assertEqual(meta["timestamp"], "2026-11-15T12:00:00Z")
        self.assertEqual(meta["content_hash"], "a1b2c3d4e5f60718")

    def test_upsert_idempotency(self):
        """Verifies re-upserting updated content with the same chunk_id replaces the record."""
        chunk = {
            "chunk_id": "DOC-202_0",
            "doc_id": "DOC-202",
            "title": "Customs Duty Threshold",
            "content": "Duty-free threshold is $800.",
            "embedding": [0.1] * 384,
            "category": "customs",
        }
        chroma_db.upsert_knowledge_chunks([chunk])
        col = chroma_db.get_or_create_collection()
        self.assertEqual(col.count(), 1)

        chunk["content"] = "Duty-free threshold updated to $1,000 for standard imports."
        chunk["embedding"] = [0.12] * 384
        chroma_db.upsert_knowledge_chunks([chunk])

        self.assertEqual(col.count(), 1)
        res = col.get(ids=["DOC-202_0"], include=["documents"])
        self.assertEqual(res["documents"][0], "Duty-free threshold updated to $1,000 for standard imports.")

    def test_semantic_search_and_similarity_scoring(self):
        """Verifies semantic query converts cosine distance to similarity score in [0.0, 1.0]."""
        vec_a = [0.2] * 384
        vec_b = [-0.2] * 384

        chunks = [
            {
                "chunk_id": "DOC-A_0",
                "doc_id": "DOC-A",
                "title": "Warehousing Pallet Dimensions",
                "content": "Standard EURO pallets measure 1200 x 800 mm with max load 1500 kg.",
                "embedding": vec_a,
                "category": "warehousing",
            },
            {
                "chunk_id": "DOC-B_0",
                "doc_id": "DOC-B",
                "title": "Maritime Cold Chain Regulations",
                "content": "Reefer containers must maintain -20C for frozen cargo at all times.",
                "embedding": vec_b,
                "category": "cold_chain",
            },
        ]
        chroma_db.upsert_knowledge_chunks(chunks)

        with patch.object(embeddings, "embed_query", return_value=vec_a):
            results = chroma_db.query_knowledge_chunks("What are the pallet sizes in warehouses?", top_k=2)

        self.assertGreaterEqual(len(results), 1)
        top = results[0]
        self.assertEqual(top["doc_id"], "DOC-A")
        self.assertEqual(top["category"], "warehousing")
        self.assertAlmostEqual(top["score"], 1.0, places=2)

    def test_metadata_filtering(self):
        """Verifies filtering by category in ChromaDB semantic search."""
        chunks = [
            {
                "chunk_id": "DOC-C1_0",
                "doc_id": "DOC-C1",
                "title": "Customs Inspection Procedure",
                "content": "Shipments marked for inspection take 24-48 business hours.",
                "embedding": [0.1] * 384,
                "category": "customs",
            },
            {
                "chunk_id": "DOC-S1_0",
                "doc_id": "DOC-S1",
                "title": "Standard Shipping Transit",
                "content": "Standard ground shipping takes 3-5 business days.",
                "embedding": [0.1] * 384,
                "category": "shipping_process",
            },
        ]
        chroma_db.upsert_knowledge_chunks(chunks)

        with patch.object(embeddings, "embed_query", return_value=[0.1] * 384):
            customs_only = chroma_db.query_knowledge_chunks(
                "How long does it take?",
                top_k=5,
                where={"category": "customs"},
            )

        self.assertEqual(len(customs_only), 1)
        self.assertEqual(customs_only[0]["category"], "customs")
        self.assertEqual(customs_only[0]["doc_id"], "DOC-C1")

    def test_persistence_across_client_reinitialization(self):
        """Verifies data persisted to disk survives client close and re-opening."""
        chunk = {
            "chunk_id": "DOC-PERSIST_0",
            "doc_id": "DOC-PERSIST",
            "title": "Dangerous Goods Certification",
            "content": "Lithium batteries require UN3480 hazard diamond labels.",
            "embedding": [0.08] * 384,
            "category": "hazmat",
        }
        chroma_db.upsert_knowledge_chunks([chunk])

        chroma_db.close()

        reopened_client = chroma_db.get_chroma_client()
        col = reopened_client.get_collection("test_logistics_chunks")
        self.assertEqual(col.count(), 1)
        res = col.get(ids=["DOC-PERSIST_0"], include=["documents", "metadatas"])
        self.assertEqual(res["documents"][0], chunk["content"])
        self.assertEqual(res["metadatas"][0]["category"], "hazmat")

    def test_ingest_from_kb_with_limit(self):
        """Verifies ingest_from_kb() loads knowledge base records and indexes them."""
        with patch.object(embeddings, "embed_texts", return_value=[[0.05] * 384] * 5):
            count = chroma_db.ingest_from_kb(limit=5)
        self.assertEqual(count, 5)

        col = chroma_db.get_or_create_collection()
        self.assertEqual(col.count(), 5)


class ChromaDBRetrievalIntegrationTests(unittest.TestCase):
    """Verifies retrieval layer integrates ChromaDB seamlessly with RAG."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="chroma_rag_test_")
        self.original_persist_dir = config.CHROMA_PERSIST_DIRECTORY
        self.original_mode = config.CHROMA_MODE
        self.original_col = config.CHROMA_COLLECTION_NAME
        self.original_vstore = getattr(config, "VECTOR_STORE", "auto")

        config.CHROMA_PERSIST_DIRECTORY = Path(self.temp_dir)
        config.CHROMA_MODE = "persistent"
        config.CHROMA_COLLECTION_NAME = "test_logistics_chunks"
        config.VECTOR_STORE = "chroma"
        chroma_db.close()

    def tearDown(self):
        chroma_db.close()
        config.CHROMA_PERSIST_DIRECTORY = self.original_persist_dir
        config.CHROMA_MODE = self.original_mode
        config.CHROMA_COLLECTION_NAME = self.original_col
        config.VECTOR_STORE = self.original_vstore
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_retrieval_service_uses_chromadb_when_populated(self):
        """Verifies retrieval.search_knowledge() returns articles from ChromaDB."""
        from logistics_chatbot.rag.retrieval import search_knowledge

        chunk = {
            "chunk_id": "FAQ-CHROMA-01_0",
            "doc_id": "FAQ-CHROMA-01",
            "title": "Chroma Vector Search Transit Policy",
            "content": "Expedited air delivery delivers within 48 hours worldwide.",
            "embedding": [0.15] * 384,
            "category": "transit_policy",
        }
        chroma_db.upsert_knowledge_chunks([chunk])

        with patch.object(embeddings, "embed_query", return_value=[0.15] * 384):
            result = search_knowledge("What is the air delivery transit policy?")

        self.assertEqual(result.source, "chroma_db")
        self.assertEqual(len(result.articles), 1)
        self.assertEqual(result.articles[0]["doc_id"], "FAQ-CHROMA-01")
        self.assertIn("Expedited air delivery", result.articles[0]["content"])


if __name__ == "__main__":
    unittest.main()
