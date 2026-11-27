"""Comprehensive integration tests for New Data (5 PDFs + 14-table Excel dataset).

Covers Phase 9 Test A (PDF/ChromaDB), Test B (Relational DB), Test C (Hybrid SQL + ChromaDB),
and Test D (Multi-turn Memory, Context Switching, & Idempotency).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest


class TestPhaseAPDFAndChromaDBRetrieval:
    """Test A: Verify all 5 new PDFs are indexed in ChromaDB and retrieve relevant chunks + metadata."""

    @pytest.mark.parametrize(
        "query,expected_doc_id,expected_terms",
        [
            ("Explain the Incoterms 2020 rules", "PDF-INCOTERMS", ["incoterms"]),
            ("What is the difference between EXW and DDP?", "PDF-INCOTERMS", ["exw", "ddp"]),
            ("What documents are required for international shipping?", "PDF-EXIM-CUSTOMS", ["bill of lading", "invoice"]),
            ("What are the major reasons for shipment delays?", "PDF-DELAY-RISK", ["delay"]),
            ("Explain bonded warehousing", "PDF-WAREHOUSING", ["bonded"]),
            ("How can customers track shipments using ECU360?", "PDF-CUST-SUPPORT", ["track", "ecu360"]),
            ("What is the customs clearance process?", "PDF-EXIM-CUSTOMS", ["customs", "clearance"]),
        ],
    )
    def test_pdf_semantic_retrieval_and_metadata(self, query, expected_doc_id, expected_terms):
        from logistics_chatbot.application.rag.hybrid_search import search_knowledge

        hits = search_knowledge(query, top_k=5)
        assert len(hits) >= 1, f"No ChromaDB matches for query: {query}"
        matching_docs = [h.get("document_id") or h.get("doc_id") for h in hits]
        assert expected_doc_id in matching_docs, f"Expected {expected_doc_id} in {matching_docs} for {query!r}"

        combined_text = " ".join((h.get("content") or "").lower() for h in hits)
        assert any(t in combined_text for t in expected_terms), f"Expected one of {expected_terms} in retrieved chunks"

        pdf_hits = [h for h in hits if (h.get("document_id") or h.get("doc_id")) == expected_doc_id]
        meta = pdf_hits[0]
        assert meta.get("page_number") is not None and int(meta["page_number"]) >= 1
        assert meta.get("section_name") or meta.get("section_title")
        assert meta.get("source_file") or meta.get("source")


class TestPhaseBRelationalExcelDatabase:
    """Test B: Verify 14 Excel tables, 79,000 rows, FK joins, and derived delayed status."""

    def test_enterprise_tables_populated_and_no_delayed_column(self):
        from logistics_chatbot.core import config
        from logistics_chatbot.infrastructure.database import repository as database

        summary = database.get_enterprise_summary_counts()
        expected_counts = {
            "enterprise_customers": 3000,
            "products": 5000,
            "carriers": 5000,
            "warehouses": 5000,
            "routes": 3000,
            "vehicles": 5000,
            "weather": 3000,
            "customs": 5000,
            "ai_model_registry": 5000,
            "enterprise_shipments": 5000,
            "shipment_delivery_history": 5000,
            "ai_feature_store": 10000,
            "ai_inference_log": 10000,
            "ai_monitoring_alerts": 10000,
        }
        assert summary["tables"] == expected_counts
        assert summary["derived_delivery_status"] == {"Delayed": 1191, "Delivered": 3809}

        # Confirm special README rule: enterprise_shipments must NOT store 'delayed'
        db_path = config.DB_PATH if config.DB_PATH.exists() else (config.PROJECT_ROOT / "data" / "raw" / "shipments.db")
        with sqlite3.connect(str(db_path)) as conn:
            cols = [r[1].lower() for r in conn.execute("PRAGMA table_info(enterprise_shipments)").fetchall()]
        assert "delayed" not in cols and "is_delayed" not in cols

    def test_booking_reference_lookup_joins_all_dimensions(self):
        from logistics_chatbot.infrastructure.database import repository as database

        ent_ontime = database.get_enterprise_shipment("ALC-2025-100000")
        assert ent_ontime is not None
        assert ent_ontime["booking_id"] == "ALC-2025-100000"
        assert ent_ontime["derived_status"] == "Delivered"
        assert ent_ontime["is_delayed"] is False
        assert ent_ontime["carrier_name"]
        assert ent_ontime["customer_name"]
        assert ent_ontime["warehouse_name"]
        assert ent_ontime["origin_port"] and ent_ontime["destination_port"]
        assert ent_ontime["weather_condition"]
        assert "customs_required" in ent_ontime
        assert len(ent_ontime["alerts"]) >= 1

        ent_delayed = database.get_enterprise_shipment("ALC-2025-100001")
        assert ent_delayed is not None
        assert ent_delayed["derived_status"] == "Delayed"
        assert ent_delayed["is_delayed"] is True
        assert ent_delayed["delay_days"] >= 1

    def test_standalone_dimension_entity_chat_lookups(self, test_client):
        from logistics_chatbot.infrastructure.database import repository as database

        sample_ent = database.get_enterprise_shipment("ALC-2025-100000")
        assert sample_ent is not None

        for query, expected_substr in [
            (f"Show customer details for {sample_ent['customer_name']}", sample_ent["customer_name"]),
            (f"Show carrier details for {sample_ent['carrier_name']}", sample_ent["carrier_name"]),
            (f"Show warehouse info for {sample_ent['warehouse_name']}", sample_ent["warehouse_name"]),
            (f"Show route from {sample_ent['origin_city']} to {sample_ent['destination_city']}", sample_ent["origin_port"]),
        ]:
            resp = test_client.post("/chat", json={"message": query})
            assert resp.status_code == 200
            body = resp.json()
            assert expected_substr in body["data"]["response"], f"Missing {expected_substr!r} in {body}"

    def test_legacy_shipment_10k_and_rest_api_preserved(self, test_client):
        resp_shp = test_client.get("/shipment/SHP-10001")
        assert resp_shp.status_code == 200
        assert resp_shp.json()["data"]["shipment_id"] == "SHP-10001"

        resp_alc = test_client.get("/shipment/ALC-2025-100000")
        assert resp_alc.status_code == 200
        assert resp_alc.json()["data"]["booking_id"] == "ALC-2025-100000"


class TestPhaseCHybridRetrievalAndMemory:
    """Test C & D: Hybrid SQL + ChromaDB synthesis, multi-turn memory, and context switching."""

    def test_hybrid_delay_query_combines_sql_and_chromadb(self, test_client):
        from logistics_chatbot.application.chatbot.orchestrator import get_conversation_store

        session_id = "hybrid-delay-test"
        get_conversation_store().delete(session_id)

        with patch("logistics_chatbot.application.chatbot.orchestrator._invoke_llm") as mock_llm:
            mock_llm.return_value = (
                "### Shipment Information\n"
                "- Booking Reference: ALC-2025-100001 (Delayed +5 days)\n\n"
                "### Operational Information\n"
                "- Derived directly from shipment_delivery_history and route/weather telemetry.\n\n"
                "### Knowledge-Based Explanation\n"
                "- Per Shipment Delay Causes & Route Risk Reference, port congestion and weather disruptions extend transit.\n\n"
                "### Summary\n"
                "Monitor carrier alerts and reschedule receiving."
            )
            resp = test_client.post(
                "/chat",
                json={
                    "message": "Why is shipment ALC-2025-100001 delayed, and what can be done?",
                    "session_id": session_id,
                },
            )

        assert resp.status_code == 200
        mock_llm.assert_called_once()
        prompt_sent = mock_llm.call_args[0][0][-1]["content"]
        assert "ENTERPRISE SHIPMENT DATABASE RECORD:" in prompt_sent
        assert "ALC-2025-100001" in prompt_sent
        assert "KNOWLEDGE BASE:" in prompt_sent
        assert "Delayed" in prompt_sent

        data = resp.json()["data"]
        assert data["shipment_id"] == "ALC-2025-100001"
        assert any("Enterprise Shipment Database (ALC-2025-100001)" in s for s in data["sources"])
        assert any("PDF-" in s or "Reference" in s or "Policy" in s or "Guid" in s for s in data["sources"])

    def test_hybrid_customs_and_absent_incoterm_grounding(self, test_client):
        with patch("logistics_chatbot.application.chatbot.orchestrator._invoke_llm") as mock_llm:
            mock_llm.return_value = (
                "### Shipment Information\n- ALC-2025-100000\n"
                "### Knowledge-Based Explanation\n- Incoterm is not stored on this shipment booking; see Incoterms 2020 guidance."
            )
            resp = test_client.post(
                "/chat",
                json={"message": "Explain the customs requirements and Incoterm responsibilities for ALC-2025-100000."},
            )
        assert resp.status_code == 200
        prompt_sent = mock_llm.call_args[0][0][-1]["content"]
        assert "Customs: Required=" in prompt_sent
        assert "Incoterm Field: Not stored on this shipment booking record." in prompt_sent
        assert "KNOWLEDGE BASE:" in prompt_sent

    def test_multiturn_enterprise_memory_and_context_switching(self, test_client):
        from logistics_chatbot.infrastructure.database import repository as database

        sid = "enterprise-memory-switch"
        test_client.post("/chat/new", json={"session_id": sid})
        ent0 = database.get_enterprise_shipment("ALC-2025-100000")

        # Turn 1: Find shipment ALC-2025-100000
        r1 = test_client.post("/chat", json={"message": "Find shipment ALC-2025-100000.", "session_id": sid})
        assert r1.status_code == 200
        assert "ALC-2025-100000" in r1.json()["data"]["response"]

        # Turn 2: Who is its carrier?
        r2 = test_client.post("/chat", json={"message": "Who is its carrier?", "session_id": sid})
        assert r2.status_code == 200
        assert ent0["carrier_name"] in r2.json()["data"]["response"]

        # Turn 3: What is its destination?
        r3 = test_client.post("/chat", json={"message": "What is its destination?", "session_id": sid})
        assert r3.status_code == 200
        assert ent0["destination_city"] in r3.json()["data"]["response"]

        # Turn 4: Switch context back to SHP-10001
        r4 = test_client.post("/chat", json={"message": "Now track SHP-10001", "session_id": sid})
        assert r4.status_code == 200
        assert "SHP-10001" in r4.json()["data"]["response"]

        # Turn 5: Follow-up resolves to SHP-10001 (NOT ALC-2025-100000)
        r5 = test_client.post("/chat", json={"message": "What is its current location?", "session_id": sid})
        assert r5.status_code == 200
        assert "SHP-10001" in r5.json()["data"]["response"]
