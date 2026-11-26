"""Live integration test runner across PDF ChromaDB, Enterprise SQLite, and Groq LLM (Phase 9).

Runs real non-mocked queries when GROQ_API_KEY is available and saves measured JSON results
to tests/reports/new_data_integration_live_results.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
for p in (str(_SRC), str(_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from api.main import app
from logistics_chatbot.core import config
from logistics_chatbot.database import database
from rag.search import search_knowledge

client = TestClient(app)


def main() -> int:
    results = {
        "groq_configured": bool(config.GROQ_API_KEY),
        "groq_model": config.GROQ_MODEL,
        "supabase_db_url_configured": bool(config.SUPABASE_DB_URL),
        "test_a_chromadb": [],
        "test_b_database": {},
        "test_c_hybrid": [],
        "test_d_memory_and_regression": [],
    }

    # Test A: Knowledge Base & ChromaDB + Live Chatbot
    test_a_queries = [
        "Explain the Incoterms 2020 rules.",
        "What is the difference between EXW and DDP?",
        "What documents are required for international shipping?",
        "What are the major reasons for shipment delays?",
        "Explain bonded warehousing.",
        "How can customers track shipments using ECU360?",
        "What is the customs clearance process?",
    ]
    for q in test_a_queries:
        t0 = time.perf_counter()
        hits = search_knowledge(q, top_k=3)
        r = client.post("/chat", json={"message": q})
        dt = round((time.perf_counter() - t0) * 1000, 1)
        time.sleep(1.5)
        body = r.json() if r.status_code == 200 else {}
        data = body.get("data") or {}
        results["test_a_chromadb"].append({
            "query": q,
            "http_status": r.status_code,
            "latency_ms": dt,
            "top_hit": {
                "chunk_id": hits[0].get("chunk_id") if hits else None,
                "document_name": hits[0].get("document_name") if hits else None,
                "page_number": hits[0].get("page_number") if hits else None,
                "score": hits[0].get("similarity_score") if hits else None,
            },
            "sources": data.get("sources", []),
            "response_preview": (data.get("response") or "")[:320],
        })

    # Test B: Enterprise Relational Records (SQLite mirror of Data_attach2.xlsx)
    ent0 = database.get_enterprise_shipment("ALC-2025-100000")
    ent1 = database.get_enterprise_shipment("ALC-2025-100001")
    results["test_b_database"] = {
        "summary": database.get_enterprise_summary_counts(),
        "alc_100000_derived_status": ent0.get("derived_status") if ent0 else None,
        "alc_100000_carrier": ent0.get("carrier_name") if ent0 else None,
        "alc_100000_customer": ent0.get("customer_name") if ent0 else None,
        "alc_100000_warehouse": ent0.get("warehouse_name") if ent0 else None,
        "alc_100000_weather": ent0.get("weather_condition") if ent0 else None,
        "alc_100001_derived_status": ent1.get("derived_status") if ent1 else None,
        "alc_100001_delay_days": ent1.get("delay_days") if ent1 else None,
        "customer_lookup_ok": len(database.search_enterprise_entity("customer", ent0["customer_name"])) > 0,
        "carrier_lookup_ok": len(database.search_enterprise_entity("carrier", ent0["carrier_name"])) > 0,
        "warehouse_lookup_ok": len(database.search_enterprise_entity("warehouse", ent0["warehouse_name"])) > 0,
        "route_lookup_ok": len(database.search_enterprise_entity("route", ent0["origin_city"])) > 0,
    }

    # Test C: Hybrid SQL + ChromaDB + Live Groq LLM Queries
    hybrid_queries = [
        "Explain why shipment ALC-2025-100001 might be delayed using its shipment record and the knowledge base.",
        "Explain the customs requirements relevant to shipment ALC-2025-100000.",
        "Explain the shipping responsibilities using the shipment's Incoterm for ALC-2025-100000.",
        "Provide operational guidance for handling shipment ALC-2025-100001.",
    ]
    for hq in hybrid_queries:
        t0 = time.perf_counter()
        r = client.post("/chat", json={"message": hq})
        dt = round((time.perf_counter() - t0) * 1000, 1)
        time.sleep(5.0)
        data = (r.json().get("data") or {}) if r.status_code == 200 else {}
        results["test_c_hybrid"].append({
            "query": hq,
            "http_status": r.status_code,
            "latency_ms": dt,
            "response_type": data.get("response_type"),
            "shipment_id": data.get("shipment_id"),
            "sources": data.get("sources", []),
            "response_preview": (data.get("response") or "")[:400],
        })

    # Test D: Multi-turn Enterprise Memory + Context Switch + Legacy SHP-10001 Preservation
    from logistics_chatbot.chatbot.chatbot import get_conversation_store

    mem_sid = f"live-verify-{int(time.time())}"
    get_conversation_store().delete(mem_sid)
    for msg in [
        "Find shipment ALC-2025-100000.",
        "Who is its carrier?",
        "What is its destination?",
        "Why might it be delayed?",
        "Track shipment SHP-10001",
        "Where is it now?",
    ]:
        r = client.post("/chat", json={"message": msg, "session_id": mem_sid})
        data = (r.json().get("data") or {}) if r.status_code == 200 else {}
        results["test_d_memory_and_regression"].append({
            "query": msg,
            "http_status": r.status_code,
            "shipment_id": data.get("shipment_id"),
            "response_type": data.get("response_type"),
            "response_preview": (data.get("response") or "")[:240],
        })

    out_path = _ROOT / "tests" / "reports" / "new_data_integration_live_results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Live verification completed. Results saved to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
