"""Tests for GET /shipment/{id} endpoint."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fastapi.testclient import TestClient
from logistics_chatbot.main import app

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


class TestShipmentEndpoint(unittest.TestCase):
    """Test suite for GET /shipment/{id}."""

    @patch("logistics_chatbot.application.services.shipment_service.lookup_shipment_by_id")
    def test_existing_shipment_success(self, mock_get):
        mock_get.return_value = SAMPLE_SHIPMENT
        response = client.get("/shipment/SHP-10001")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Shipment retrieved successfully")
        self.assertEqual(data["data"]["shipment_id"], "SHP-10001")
        self.assertEqual(data["data"]["status"], "In Transit")

    @patch("logistics_chatbot.application.services.shipment_service.lookup_shipment_by_id")
    def test_missing_shipment_returns_404(self, mock_get):
        mock_get.return_value = None
        response = client.get("/shipment/SHP-99999")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Shipment Not Found")
        self.assertIsNone(data["data"])

    @patch("logistics_chatbot.application.services.shipment_service.lookup_shipment_by_id")
    def test_database_error_returns_500(self, mock_get):
        from logistics_chatbot.core.errors import DatabaseError
        mock_get.side_effect = DatabaseError("Connection refused")
        response = client.get("/shipment/SHP-10001")
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("Database query failure", data["message"])


if __name__ == "__main__":
    unittest.main()
