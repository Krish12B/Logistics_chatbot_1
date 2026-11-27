"""Error handling, resilience, and failure simulation tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestAPIStructuredErrors:
    def test_404_unknown_route(self, test_client):
        resp = test_client.get("/does-not-exist")
        assert resp.status_code == 404

    def test_405_invalid_method(self, test_client):
        resp = test_client.get("/chat")
        assert resp.status_code == 405

    def test_422_malformed_json(self, test_client):
        resp = test_client.post("/chat", content="{bad_json", headers={"Content-Type": "application/json"})
        assert resp.status_code == 422
        assert resp.json()["success"] is False

    def test_null_message_rejected(self, test_client):
        resp = test_client.post("/chat", json={"message": None})
        assert resp.status_code == 422


class TestFailureModesMocked:
    def test_database_connection_failure_shipment_endpoint(self, test_client):
        """TC-ERR-05: DatabaseError in GET /shipment/{id} returns safe 500 JSON without credentials."""
        from logistics_chatbot.core.errors import DatabaseError

        with patch("logistics_chatbot.application.services.shipment_service.lookup_shipment_by_id", side_effect=DatabaseError(detail="secret_db_password leaked")):
            resp = test_client.get("/shipment/SHP-10001")
        assert resp.status_code == 500
        body = resp.json()
        assert body["success"] is False
        assert "secret_db_password" not in body["message"]

    def test_llm_timeout_returns_500_friendly_message(self, test_client):
        """TC-ERR-06: LLMTimeoutError during /chat returns safe friendly unavailability error."""
        from logistics_chatbot.core.errors import LLMTimeoutError

        fake_ctx = MagicMock(
            knowledge_articles=[{"doc_id": "DOC-001", "section_title": "Customs", "content": "Details"}],
            shipment=None,
            source_doc_ids=["DOC-001"],
        )
        with patch("logistics_chatbot.application.chatbot.orchestrator.retrieve", return_value=fake_ctx), \
             patch("logistics_chatbot.application.chatbot.orchestrator.call_llm", side_effect=LLMTimeoutError(detail="timed out 30s")):
            resp = test_client.post("/chat", json={"message": "What special tariff applies to cocoa beans?"})
        assert resp.status_code == 500
        body = resp.json()
        assert body["success"] is False
        assert "temporarily unavailable" in body["message"].lower()

    def test_llm_api_failure_rate_limit(self, test_client):
        """TC-ERR-07: LLMRateLimitError during /chat returns safe structured error."""
        from logistics_chatbot.core.errors import LLMRateLimitError

        fake_ctx = MagicMock(
            knowledge_articles=[{"doc_id": "DOC-001", "section_title": "Customs", "content": "Details"}],
            shipment=None,
            source_doc_ids=["DOC-001"],
        )
        with patch("logistics_chatbot.application.chatbot.orchestrator.retrieve", return_value=fake_ctx), \
             patch("logistics_chatbot.application.chatbot.orchestrator.call_llm", side_effect=LLMRateLimitError(detail="429 quota")):
            resp = test_client.post("/chat", json={"message": "What special tariff applies to cocoa beans?"})
        assert resp.status_code == 500
        assert "busy" in resp.json()["message"].lower()

    def test_unexpected_exception_no_stack_trace_leak(self, test_client):
        """TC-ERR-08: Unexpected RuntimeError never leaks stack traces to API callers."""
        with patch("logistics_chatbot.application.chatbot.orchestrator.generate_response", side_effect=RuntimeError("INTERNAL_SECRET_KEY_12345")):
            resp = test_client.post("/chat", json={"message": "Track SHP-10001"})
        assert resp.status_code == 500
        body = resp.json()
        assert body["success"] is False
        assert "INTERNAL_SECRET_KEY_12345" not in str(body)
