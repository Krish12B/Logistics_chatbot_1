"""End-to-end integration workflows combining API, DB, isolated ChromaDB, and mocked LLM."""
from __future__ import annotations

import io
from unittest.mock import patch

import pytest


class TestEndToEndIntegration:
    def test_health_chat_shipment_sequence(self, test_client, clean_sessions, unique_session_id):
        """TC-INT-01: Sequential health -> chat -> follow-up -> shipment lookup flow."""
        assert test_client.get("/health").status_code == 200

        c1 = test_client.post("/chat", json={"message": "Track SHP-10001", "session_id": unique_session_id})
        assert c1.status_code == 200
        assert "SHP-10001" in c1.json()["data"]["response"]

        c2 = test_client.post("/chat", json={"message": "When will it arrive?", "session_id": unique_session_id})
        assert c2.status_code == 200
        assert "20 November 2026" in c2.json()["data"]["response"]

        s1 = test_client.get("/shipment/SHP-10001")
        assert s1.status_code == 200
        assert s1.json()["data"]["origin"] == "Mumbai, India"

    def test_upload_to_isolated_chroma_and_rag_chat(self, test_client, isolated_chroma, unique_session_id):
        """TC-INT-02: Upload doc -> isolated ChromaDB indexing -> RAG retrieval -> mocked LLM grounded response."""
        doc_bytes = (
            b"FleetHarbor Special Protocol X-RAY-900:\n\n"
            b"All lithium batteries shipped via Tokyo hub must include UN3480 form and X-RAY-900 clearance stamp.\n"
        )
        fake_vec = [0.42] * 384

        with patch("logistics_chatbot.application.rag.hybrid_search.embed_texts", return_value=[fake_vec]):
            up_resp = test_client.post(
                "/upload-doc",
                files={"file": ("xray900_protocol.txt", io.BytesIO(doc_bytes), "text/plain")},
            )
        assert up_resp.status_code == 200
        assert up_resp.json()["data"]["chunks_created"] >= 1

        with patch("logistics_chatbot.infrastructure.embeddings.sentence_transformer.embed_query", return_value=fake_vec), \
             patch("logistics_chatbot.application.chatbot.orchestrator.stream_llm") as m_stream, \
             patch("logistics_chatbot.application.chatbot.orchestrator.call_llm", return_value="Protocol X-RAY-900 requires UN3480 form at Tokyo hub.") as m_llm:
            q_resp = test_client.post("/chat", json={
                "message": "What does protocol X-RAY-900 require at Tokyo hub?",
                "session_id": unique_session_id,
            })

        assert q_resp.status_code == 200
        body = q_resp.json()
        assert body["success"] is True
        assert "X-RAY-900" in body["data"]["response"] or "UN3480" in body["data"]["response"]
        m_llm.assert_called_once()
        m_stream.assert_not_called()
