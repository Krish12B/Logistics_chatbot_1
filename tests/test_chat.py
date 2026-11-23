"""Tests for POST /chat endpoint."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestChatEndpoint(unittest.TestCase):
    """Test suite for POST /chat."""

    @patch("api.routes.chat.generate_response")
    def test_valid_chat_message(self, mock_generate):
        mock_generate.return_value = (
            "International shipments generally require export declaration and customs invoice.",
            ["DOC-001", "FAQ-002"],
        )
        response = client.post(
            "/chat",
            json={"message": "What is the delivery process for international shipments?"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Response generated successfully")
        self.assertEqual(data["data"]["query"], "What is the delivery process for international shipments?")
        self.assertIn("International shipments", data["data"]["response"])
        self.assertIn("DOC-001", data["data"]["sources"])

    def test_empty_chat_message_rejected(self):
        response = client.post("/chat", json={"message": ""})
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertFalse(data["success"])

    def test_whitespace_only_chat_message_rejected(self):
        response = client.post("/chat", json={"message": "    \n\t   "})
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertFalse(data["success"])

    def test_missing_message_field_rejected(self):
        response = client.post("/chat", json={})
        self.assertEqual(response.status_code, 422)

    @patch("api.routes.chat.generate_response")
    def test_llm_failure_handled_safely(self, mock_generate):
        from logistics_chatbot.core.errors import LLMUnavailableError
        mock_generate.side_effect = LLMUnavailableError("simulated network connection drop")
        response = client.post(
            "/chat",
            json={"message": "Status of my package?"},
        )
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("AI service temporarily unavailable", data["message"])


if __name__ == "__main__":
    unittest.main()
