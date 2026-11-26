"""Automated API endpoint tests using FastAPI TestClient with mocked external services.

Covers: health checks, /chat, /chat/stream, /shipment/{id}, /employee/{id},
/upload-doc, /api/health, /api/shipments, /api/vector-db/health, and response contracts.
"""
from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest


class TestHealthEndpoints:
    def test_health_returns_200(self, test_client):
        """TC-API-01: GET /health returns 200 with required structure."""
        resp = test_client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "running" in body["message"].lower()

    def test_root_json_catalog(self, test_client):
        """TC-API-02: GET / with Accept: application/json returns API endpoint catalog."""
        resp = test_client.get("/", headers={"Accept": "application/json"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "chat" in body["data"]
        assert "shipment" in body["data"]
        assert "upload_doc" in body["data"]

    def test_vector_db_health_mocked(self, test_client):
        """TC-API-03: GET /api/vector-db/health returns ChromaDB status dictionary."""
        with patch("rag.search.get_vector_db_health", return_value={
            "status": "healthy", "mode": "persistent", "collection_name": "logistics_knowledge_chunks", "record_count": 946
        }):
            resp = test_client.get("/api/vector-db/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert "collection_name" in body


class TestChatEndpoints:
    def test_chat_valid_greeting(self, test_client):
        """TC-API-04: POST /chat with greeting returns 200 and chat envelope."""
        resp = test_client.post("/chat", json={"message": "Hello"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["query"] == "Hello"
        assert isinstance(body["data"]["sources"], list)
        assert body["data"]["response_type"] == "greeting"

    def test_chat_empty_message_rejected(self, test_client):
        """TC-API-05: POST /chat with empty message returns 422."""
        resp = test_client.post("/chat", json={"message": ""})
        assert resp.status_code in (400, 422)
        assert resp.json()["success"] is False

    def test_chat_whitespace_only_rejected(self, test_client):
        """TC-API-06: POST /chat with whitespace-only message returns 422."""
        resp = test_client.post("/chat", json={"message": "   \t\n  "})
        assert resp.status_code in (400, 422)
        assert resp.json()["success"] is False

    def test_chat_missing_message_parameter(self, test_client):
        """TC-API-07: POST /chat missing required 'message' returns 422 ErrorResponse."""
        resp = test_client.post("/chat", json={})
        assert resp.status_code == 422
        body = resp.json()
        assert body["success"] is False

    def test_chat_long_message_rejected(self, test_client):
        """TC-API-08: POST /chat exceeding 2000 chars returns 413 or 422."""
        long_msg = "What is shipment tracking? " * 100  # 2700 chars
        resp = test_client.post("/chat", json={"message": long_msg})
        assert resp.status_code in (413, 422)
        assert resp.json()["success"] is False

    def test_chat_rag_query_uses_mocked_llm(self, test_client, mock_llm, unique_session_id):
        """TC-API-09: POST /chat general knowledge query validates full response schema cleanly."""
        fake_ctx = MagicMock(
            knowledge_articles=[{"doc_id": "DOC-001", "section_title": "Customs", "content": "Commercial invoice required."}],
            shipment=None,
            source_doc_ids=["DOC-001"],
        )
        with patch("chatbot.bot.retrieve", return_value=fake_ctx), \
             patch("logistics_chatbot.chatbot.chatbot.retrieve", return_value=fake_ctx):
            resp = test_client.post("/chat", json={
                "message": "What invoice details are needed at border inspection?",
                "session_id": unique_session_id,
            })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "data" in body
        assert "response" in body["data"]
        assert "sources" in body["data"]
        assert isinstance(body["data"]["sources"], list)

    def test_chat_stream_endpoint_sse_format(self, test_client, unique_session_id):
        """TC-API-10: POST /chat/stream returns text/event-stream with done payload."""
        with test_client.stream("POST", "/chat/stream", json={"message": "Hello", "session_id": unique_session_id}) as resp:
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")
            raw = b"".join(resp.iter_bytes()).decode("utf-8")
        assert "data:" in raw
        assert '"done": true' in raw


class TestShipmentAndEmployeeEndpoints:
    def test_shipment_valid_id(self, test_client, sample_shipment):
        """TC-API-11: GET /shipment/SHP-10001 returns 200 with shipment payload."""
        with patch("api.routes.shipment.get_shipment_by_id", return_value=sample_shipment):
            resp = test_client.get("/shipment/SHP-10001")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["shipment_id"] == "SHP-10001"
        assert body["data"]["status"] == "In Transit"

    def test_shipment_invalid_id_returns_404(self, test_client):
        """TC-API-12: GET /shipment/INVALID-999 returns 404."""
        with patch("api.routes.shipment.get_shipment_by_id", return_value=None):
            resp = test_client.get("/shipment/INVALID-999")
        assert resp.status_code == 404
        assert resp.json()["success"] is False

    def test_employee_valid_id(self, test_client, sample_employee):
        """TC-API-13: GET /employee/EMP-20001 returns 200 with employee data."""
        with patch("api.routes.employee.get_employee_by_id", return_value=sample_employee):
            resp = test_client.get("/employee/EMP-20001")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["employee_id"] == "EMP-20001"

    def test_employee_invalid_id_returns_404(self, test_client):
        """TC-API-14: GET /employee/EMP-99999 returns 404."""
        with patch("api.routes.employee.get_employee_by_id", return_value=None):
            resp = test_client.get("/employee/EMP-99999")
        assert resp.status_code == 404
        assert resp.json()["success"] is False

    def test_api_shipments_list_mocked(self, test_client, sample_shipment):
        """TC-API-15: GET /api/shipments returns ShipmentListResponse."""
        mock_res = MagicMock(shipments=[sample_shipment], total_count=1, filter_description="status='In Transit'")
        with patch("logistics_chatbot.api.routes.shipments.search_shipments", return_value=mock_res):
            resp = test_client.get("/api/shipments?status=In%20Transit&limit=5")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_count"] == 1
        assert body["shipments"][0]["shipment_id"] == "SHP-10001"


class TestUploadEndpoint:
    def test_upload_valid_txt_mocked(self, test_client, sample_txt_content):
        """TC-API-16: POST /upload-doc with valid .txt succeeds without mutating prod ChromaDB."""
        with patch("api.routes.upload.index_document_chunks", return_value=2) as m_idx:
            resp = test_client.post(
                "/upload-doc",
                files={"file": ("test_policy.txt", io.BytesIO(sample_txt_content), "text/plain")},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["chunks_created"] == 2
        m_idx.assert_called_once()

    def test_upload_empty_file_returns_400(self, test_client):
        """TC-API-17: POST /upload-doc with empty file returns 400."""
        resp = test_client.post(
            "/upload-doc",
            files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
        )
        assert resp.status_code == 400
        assert resp.json()["success"] is False

    def test_upload_unsupported_format_returns_400(self, test_client):
        """TC-API-18: POST /upload-doc with .exe returns 400."""
        resp = test_client.post(
            "/upload-doc",
            files={"file": ("malware.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
        )
        assert resp.status_code == 400

    def test_upload_missing_file_returns_422(self, test_client):
        """TC-API-19: POST /upload-doc without file returns 422."""
        resp = test_client.post("/upload-doc")
        assert resp.status_code == 422
