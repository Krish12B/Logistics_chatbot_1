"""Tests for the FastAPI REST API layer (app.py).

Verifies:
  - POST /api/chat (successful turn, multi-turn session ID, validation errors)
  - GET  /api/shipments/{id} (200 success, 404 not found)
  - GET  /api/shipments (filtered queries, limits)
  - GET  /api/health (status and configuration)
  - GET  /api/vector-db/health (ChromaDB status)
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fastapi.testclient import TestClient

from logistics_chatbot.api.app import app
from logistics_chatbot.core.errors import InvalidShipmentIdError, ShipmentNotFoundError

client = TestClient(app)

SAMPLE_SHIPMENT = {
    "shipment_id": "SHP-10001",
    "origin": "Mumbai, India",
    "destination": "London, UK",
    "status": "In Transit",
    "current_location": "Dubai Hub, UAE",
    "route": "Mumbai Hub -> Dubai Hub -> London Heathrow Hub",
    "estimated_delivery": "2026-11-20",
    "delay_reason": None,
    "customs_status": "Not yet required",
    "last_updated": "2026-11-15 18:30",
}


class FastAPIApiTests(unittest.TestCase):

    # ── Health Endpoints ────────────────────────────────────────────

    def test_health_endpoint(self):
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("groq_model", data)
        self.assertGreaterEqual(data["active_dataset_shipments"], 10)
        self.assertGreaterEqual(data["active_dataset_kb_articles"], 2194)

    def test_vector_db_health_endpoint(self):
        response = client.get("/api/vector-db/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["status"], ("healthy", "unhealthy"))
        self.assertIn("mode", data)
        self.assertIn("collection_name", data)

    # ── Chat Endpoint ───────────────────────────────────────────────

    @patch("logistics_chatbot.api.app.retrieve")
    @patch("logistics_chatbot.api.app.chat")
    def test_chat_endpoint_success(self, mock_chat, mock_retrieve):
        mock_retrieve.return_value = MagicMock(source_doc_ids=["DOC-001"])
        mock_chat.return_value = "Your shipment SHP-10001 is currently in transit."

        response = client.post(
            "/api/chat",
            json={"message": "Where is my shipment SHP-10001?"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["answer"], "Your shipment SHP-10001 is currently in transit.")
        self.assertTrue(data["session_id"])
        self.assertIn("DOC-001", data["source_doc_ids"])

    @patch("logistics_chatbot.api.app.retrieve")
    @patch("logistics_chatbot.api.app.chat")
    def test_chat_endpoint_with_custom_session_id(self, mock_chat, mock_retrieve):
        mock_retrieve.return_value = MagicMock(source_doc_ids=[])
        mock_chat.return_value = "Here is the route for your shipment."

        response = client.post(
            "/api/chat",
            json={"message": "What is the route?", "session_id": "custom-session-123"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["session_id"], "custom-session-123")

    def test_chat_endpoint_empty_message_rejected(self):
        response = client.post("/api/chat", json={"message": ""})
        self.assertEqual(response.status_code, 422)

    def test_chat_endpoint_query_too_long_rejected(self):
        long_message = "Where is SHP-10001? " * 150
        response = client.post("/api/chat", json={"message": long_message})
        self.assertEqual(response.status_code, 422)

    # ── Shipment Endpoints ──────────────────────────────────────────

    @patch("logistics_chatbot.api.app.get_shipment_by_id")
    def test_get_shipment_success(self, mock_get_shipment):
        mock_get_shipment.return_value = MagicMock(shipment=SAMPLE_SHIPMENT)

        response = client.get("/api/shipments/SHP-10001")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["shipment_id"], "SHP-10001")
        self.assertEqual(data["status"], "In Transit")
        self.assertEqual(data["origin"], "Mumbai, India")

    @patch("logistics_chatbot.api.app.get_shipment_by_id")
    def test_get_shipment_not_found(self, mock_get_shipment):
        mock_get_shipment.side_effect = ShipmentNotFoundError("No row for SHP-99999")
        response = client.get("/api/shipments/SHP-99999")
        self.assertEqual(response.status_code, 404)

    @patch("logistics_chatbot.api.app.search_shipments")
    def test_search_shipments_with_filters(self, mock_search):
        mock_search.return_value = MagicMock(
            shipments=[SAMPLE_SHIPMENT],
            total_count=1,
            filter_description="status='In Transit'",
        )

        response = client.get("/api/shipments?status=In%20Transit&limit=5")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_count"], 1)
        self.assertEqual(len(data["shipments"]), 1)
        self.assertEqual(data["shipments"][0]["shipment_id"], "SHP-10001")


if __name__ == "__main__":
    unittest.main()
