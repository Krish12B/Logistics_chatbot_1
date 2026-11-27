"""Chat functionality tests: greetings, direct definitions, shipment/employee/ops routing, streaming efficiency."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestChatGreetingsAndGuardrails:
    def test_greeting_hello(self, test_client):
        """TC-CHAT-01: 'Hello' returns official welcome prompt without LLM call."""
        resp = test_client.post("/chat", json={"message": "Hello"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["response_type"] == "greeting"
        assert "fleetharbor" in body["data"]["response"].lower()

    def test_off_topic_poem_declined(self, test_client):
        """TC-CHAT-02: Off-topic poem request is declined safely."""
        resp = test_client.post("/chat", json={"message": "Can you write a poem about baking cookies?"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["response_type"] == "unsupported"
        assert "outside the fleetharbor logistics domain" in body["data"]["response"].lower()

    def test_off_topic_mars_weather_declined(self, test_client):
        """TC-CHAT-03: Off-topic general trivia ('weather on Mars') should be declined, not answered with Cold-Chain docs."""
        resp = test_client.post("/chat", json={"message": "What is the weather on Mars tomorrow?"})
        assert resp.status_code == 200
        body = resp.json()
        text_lower = body["data"]["response"].lower()
        assert body["data"]["response_type"] in ("unsupported", "unavailable")
        assert "cc-pol-9921" not in text_lower and "life sciences" not in text_lower

    def test_sql_injection_sanitized_safely(self, test_client):
        """TC-CHAT-04: SQL injection string never crashes or executes SQL."""
        resp = test_client.post("/chat", json={"message": "DROP TABLE shipments; SELECT * FROM users;"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["response_type"] in ("unsupported", "unavailable")


class TestChatDirectAnswers:
    def test_customs_clearance_definition(self, test_client):
        """TC-CHAT-05: Direct answer for customs clearance returns definition and sources."""
        resp = test_client.post("/chat", json={"message": "What is customs clearance?"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["response_type"] == "direct_answer"
        assert "customs clearance" in body["data"]["response"].lower()
        assert len(body["data"]["sources"]) >= 1

    def test_demurrage_definition(self, test_client):
        """TC-CHAT-06: Direct answer for demurrage."""
        resp = test_client.post("/chat", json={"message": "What does demurrage mean in freight shipping?"})
        assert resp.status_code == 200
        assert "demurrage" in resp.json()["data"]["response"].lower()


class TestChatEntityAndCompoundQueries:
    def test_nonexistent_shipment_returns_friendly_not_found(self, test_client):
        """TC-CHAT-07: Nonexistent shipment ID (SHP-99999) in POST /chat must NOT return HTTP 500."""
        resp = test_client.post("/chat", json={"message": "Track shipment SHP-99999"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["response_type"] == "not_found"
        assert "SHP-99999" in body["data"]["response"]
        assert body["data"]["sources"] == []

    def test_malformed_shipment_id_returns_400_guidance(self, test_client):
        """TC-CHAT-08: Malformed ID like SHP-12 returns clear guidance."""
        resp = test_client.post("/chat", json={"message": "Track SHP-12"})
        assert resp.status_code in (200, 400)
        assert "SHP-10001" in (resp.json().get("message", "") + resp.json().get("response", ""))

    def test_customs_hold_shipment_shows_customs_and_delay_reason(self, test_client, sample_shipment_customs_hold):
        """TC-CHAT-09: SHP-10003 at destination airport still reports customs_status and delay_reason."""
        with patch("logistics_chatbot.application.chatbot.orchestrator.database.get_shipment", return_value=sample_shipment_customs_hold):
            resp = test_client.post("/chat", json={"message": "Why is SHP-10003 on customs hold?"})
        assert resp.status_code == 200
        text = resp.json()["data"]["response"]
        assert "Held - awaiting commercial invoice" in text
        assert "Customs hold" in text

    def test_compound_query_includes_shipment_employee_and_terms(self, test_client, sample_shipment, sample_employee):
        """TC-CHAT-10: Compound query mentioning SHP-10001 + EMP-20001 + FOB vs CIF addresses all parts."""
        with patch("logistics_chatbot.application.chatbot.orchestrator.database.get_shipment", return_value=sample_shipment), \
             patch("logistics_chatbot.application.chatbot.orchestrator.database.get_employee", return_value=sample_employee):
            resp = test_client.post("/chat", json={
                "message": "What is the status of SHP-10001? Also tell me about EMP-20001 and FOB vs CIF shipping terms."
            })
        assert resp.status_code == 200
        text = resp.json()["data"]["response"]
        assert "SHP-10001" in text
        assert "EMP-20001" in text
        assert "FOB" in text and "CIF" in text


class TestStreamingPipelineEfficiency:
    def test_streaming_rag_calls_llm_only_once(self):
        """TC-CHAT-11: Streaming RAG query must NOT call blocking _core_chat before streaming!"""
        from logistics_chatbot.application.chatbot.orchestrator import get_conversation_store, stream_chat_response

        store = get_conversation_store()
        store.delete("stream-once-test")
        fake_ctx = MagicMock(
            knowledge_articles=[{"doc_id": "DOC-001", "section_title": "Customs", "content": "Commercial invoice required."}],
            shipment=None,
            source_doc_ids=["DOC-001"],
        )
        with patch("logistics_chatbot.application.chatbot.orchestrator.retrieve", return_value=fake_ctx) as m_ret, \
             patch("logistics_chatbot.application.chatbot.orchestrator.call_llm") as m_call, \
             patch("logistics_chatbot.application.chatbot.orchestrator.stream_llm", return_value=iter(["Customs ", "invoice ", "is required."])) as m_stream, \
             patch("logistics_chatbot.core.config.GROQ_API_KEY", "gsk_test"):
            events = list(stream_chat_response("What invoice rules apply for customs export?", session_id="stream-once-test"))

        m_call.assert_not_called()
        m_stream.assert_called_once()
        assert m_ret.call_count == 1
        sess = store.get("stream-once-test")
        assert sess is not None
        assert sess.turn_count == 1
        assert events[-1]["done"] is True
        store.delete("stream-once-test")


class TestAggregateAnalytics:
    def test_aggregate_shipments_in_transit(self, test_client):
        """TC-CHAT-12: Aggregate shipment count query returns real-time breakdown report."""
        counts = {
            "In Transit": 4279,
            "Delivered": 2961,
            "Delayed": 1294,
            "On Hold - Customs": 801,
            "Out for Delivery": 665,
        }
        with patch("logistics_chatbot.application.chatbot.orchestrator.database.get_shipment_status_counts", return_value=counts):
            resp = test_client.post("/chat", json={"message": "How many shipments are currently in transit?"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["response_type"] == "shipment_aggregate"
        assert "4,279" in body["data"]["response"]
        assert "10,000" in body["data"]["response"]

    def test_aggregate_employees_workforce(self, test_client):
        """TC-CHAT-13: Aggregate employee query returns workforce department distribution."""
        emp_counts = {
            "total": 500,
            "by_department": {
                "Warehouse Operations": 150,
                "Fleet & Linehaul Dispatch": 130,
                "Customs & Trade Compliance": 90,
                "Logistics Coordination": 75,
                "Safety & Maintenance": 55,
            },
        }
        with patch("logistics_chatbot.application.chatbot.orchestrator.database.get_employee_counts", return_value=emp_counts):
            resp = test_client.post("/chat", json={"message": "How many employees work at FleetHarbor?"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["response_type"] == "employee_aggregate"
        assert "500" in body["data"]["response"]
        assert "Warehouse Operations" in body["data"]["response"]


class TestPolicyAndHRLeaveQueries:
    def test_broad_company_policy_returns_multi_policy_overview(self, test_client):
        """TC-CHAT-14: Generic 'company policy' summarizes all FleetHarbor policies rather than only CC-POL-9921."""
        resp = test_client.post("/chat", json={"message": "company policy"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["response_type"] == "policy_overview"
        txt = body["data"]["response"]
        assert "Customer & Commercial Policies" in txt
        assert "Employee HR, Paid Leave" in txt
        assert "CC-POL-9921" in txt
        assert len(body["data"]["sources"]) >= 4

    def test_paid_leave_and_process_of_leave_retrieve_hr_policy(self):
        """TC-CHAT-15: 'paid leave?' and 'process of leave' retrieve DOC-AF885F63B95E chunks from ChromaDB."""
        from logistics_chatbot.application.rag.hybrid_search import search_knowledge

        for q in ("paid leave?", "process of leave"):
            hits = search_knowledge(q, top_k=3)
            assert len(hits) >= 1
            assert any(h.get("doc_id") == "DOC-AF885F63B95E" for h in hits), f"Expected HR policy doc for {q!r}"


class TestLocationFilteredCountsAndAntiHallucination:
    def test_shipments_in_dubai_returns_exact_filtered_sqlite_count(self, test_client):
        """Querying 'how many shipments are in dubai?' returns Dubai-specific SQLite counts (807), never global 10,000."""
        resp = test_client.post("/chat", json={"message": "how many shipments are in dubai?"})
        assert resp.status_code == 200
        body = resp.json()
        txt = body["data"]["response"]
        assert body["data"]["response_type"] == "shipment_aggregate"
        assert "807 shipments" in txt
        assert "Dubai" in txt
        assert "10,000 total real-time shipments" not in txt
        assert "20 global hub" not in txt

    def test_delayed_shipments_in_dubai_status_and_location(self, test_client):
        """Status + location combination ('how many shipments in dubai are delayed?') filters both cleanly."""
        resp = test_client.post("/chat", json={"message": "how many shipments in dubai are delayed?"})
        assert resp.status_code == 200
        txt = resp.json()["data"]["response"]
        assert "24 shipments" in txt
        assert "Delayed" in txt and "Dubai" in txt

    def test_corridor_origin_destination_count(self, test_client):
        """Corridor count ('how many shipments from Mumbai to London?') returns real filtered count."""
        resp = test_client.post("/chat", json={"message": "how many shipments from Mumbai to London?"})
        assert resp.status_code == 200
        txt = resp.json()["data"]["response"]
        assert "Mumbai" in txt and "London" in txt
        assert "10,000" not in txt

    def test_unknown_location_count_returns_zero_not_10k(self, test_client):
        """Unknown location ('how many shipments are in Atlantis?') returns 0 cleanly without fallback hallucination."""
        resp = test_client.post("/chat", json={"message": "how many shipments are in Atlantis?"})
        assert resp.status_code == 200
        txt = resp.json()["data"]["response"]
        assert "0 shipments" in txt
        assert "10,000" not in txt

    def test_employees_in_dubai_location_count(self, test_client):
        """Location-filtered employee query queries employees assigned to Dubai hubs."""
        resp = test_client.post("/chat", json={"message": "how many employees work in Dubai?"})
        assert resp.status_code == 200
        txt = resp.json()["data"]["response"]
        assert "Dubai" in txt
        assert "500 active logistics professionals" not in txt

    def test_hub_clarification_uses_real_sqlite_hub_codes(self, test_client):
        """Hub clarification lists verified DB hub codes (e.g., BOM-HUB-08), not stale hardcoded labels."""
        resp = test_client.post("/chat", json={"message": "where is the hub located"})
        assert resp.status_code == 200
        txt = resp.json()["data"]["response"]
        assert "DXB-HUB-01" in txt
        assert "BOM-HUB-08" in txt
        assert "BOM-HUB-10" not in txt

    def test_hallucinated_llm_citations_are_stripped_and_not_added_to_sources(self, test_client):
        """Fabricated [DOC-FAKE-999] tokens from LLM text never appear in text or verified sources."""
        fake_ctx = MagicMock(
            knowledge_articles=[{"doc_id": "DOC-001", "section_title": "Customs", "content": "Commercial invoice required.", "score": 0.85}],
            shipment=None,
            shipment_list=None,
            source_doc_ids=["DOC-001"],
        )
        with patch("logistics_chatbot.application.chatbot.orchestrator.retrieve", return_value=fake_ctx), \
             patch("logistics_chatbot.application.chatbot.orchestrator.call_llm", return_value="Invoices are mandatory [DOC-FAKE-999]."):
            resp = test_client.post("/chat", json={"message": "What customs invoice rule applies?"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "DOC-FAKE-999" not in data["response"]
        assert not any("DOC-FAKE-999" in s for s in data["sources"])
        assert any("DOC-001" in s for s in data["sources"])

    def test_weak_low_relevance_chunks_blocked_before_llm(self, test_client):
        """Weak (< 0.38) non-overlapping KB chunks return honest unavailability without calling LLM."""
        weak_ctx = MagicMock(
            knowledge_articles=[{"doc_id": "DOC-WEAK", "section_title": "Packaging", "content": "Cardboard box tape guidelines.", "score": 0.22}],
            shipment=None,
            shipment_list=None,
            source_doc_ids=["DOC-WEAK"],
        )
        with patch("logistics_chatbot.application.chatbot.orchestrator.retrieve", return_value=weak_ctx), \
             patch("logistics_chatbot.application.chatbot.orchestrator.call_llm") as m_llm:
            resp = test_client.post("/chat", json={"message": "What is the Arctic icebreaker transit surcharge for polar freight?"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["response_type"] == "unavailable"
        assert data["sources"] == []
        m_llm.assert_not_called()
