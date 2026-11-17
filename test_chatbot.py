"""Tests for the shipment chatbot.

Run from the project folder with:
    python3 -m unittest -v test_chatbot

The tests use a fake LLM so they run without internet access or a Groq key.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import groq
import httpx

import config
from chatbot import chat, detect_shipment_id
from database import init_database
from errors import (
    InvalidShipmentIdError,
    LLMAuthError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from llm_client import call_llm

HELP_SNIPPET = "I can help with shipment status"


def offline_llm(messages):
    """Stand-in for Groq. It echoes the CONTEXT it received, so the tests can
    check that the right facts were retrieved and passed to the model."""
    prompt = messages[-1]["content"]
    context = prompt.split("\n\nUSER QUESTION:")[0]
    return "OFFLINE TEST REPLY\n" + context


class ChatbotBehaviourTests(unittest.TestCase):

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.addCleanup(patch.stopall)

        # Use a throw-away database file for every test
        patch.object(config, "DB_PATH", Path(temp_dir.name) / "test.db").start()
        init_database()

        self.llm = patch("chatbot.call_llm", side_effect=offline_llm).start()

    # ---- The five required query types -------------------------------------

    def test_shipment_status(self):
        reply = chat("What is the status of SHP-10001?")
        self.assertIn("Status: In Transit", reply)
        self.assertIn("Current location: Dubai Hub, UAE", reply)
        self.llm.assert_called_once()

    def test_shipment_delay(self):
        reply = chat("Why is SHP-10002 delayed?")
        self.assertIn("Delay reason: Port congestion at Jebel Ali", reply)
        self.assertIn("FAQ (delay)", reply)

    def test_customs_query(self):
        reply = chat("Has SHP-10003 cleared customs?")
        self.assertIn("Customs status: Held - awaiting commercial invoice", reply)
        self.assertIn("FAQ (customs)", reply)

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
        self.assertIn("FAQ (delay)", reply)
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
        bad_path = Path("/no_such_folder_for_tests/shipments.db")
        with patch.object(config, "DB_PATH", bad_path):
            reply = chat("Status of SHP-10001")
        self.assertIn("can't reach our shipment database", reply)
        self.llm.assert_not_called()

    def test_unexpected_exception_is_caught(self):
        self.llm.side_effect = RuntimeError("something nobody planned for")
        reply = chat("Status of SHP-10001")
        self.assertIn("unexpected", reply)


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
