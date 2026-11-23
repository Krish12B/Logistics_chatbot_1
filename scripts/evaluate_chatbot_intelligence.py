"""Comprehensive AI Intelligence and Logistics Intent Evaluation Benchmark.

Runs 55 standardized test cases across 10 logistics intent categories,
testing intent classification, data source selection, shipment ID extraction,
multi-turn pronoun reference continuity, and response latency.
"""
from __future__ import annotations

import sys
import os
import time
from typing import List, Dict, Any

# Ensure workspace is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from logistics_chatbot.chatbot.classifier import (
    LogisticsIntent,
    ClassifiedIntent,
    classify_logistics_query,
    extract_shipment_id,
)


BENCHMARK_TEST_CASES: List[Dict[str, Any]] = [
    # -------------------------------------------------------------
    # Category 1: SHIPMENT TRACKING (Target: shipment_database)
    # -------------------------------------------------------------
    {
        "id": "TC-01",
        "query": "Where is my shipment SHP-10001 right now?",
        "expected_intent": LogisticsIntent.SHIPMENT_TRACKING,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-10001",
    },
    {
        "id": "TC-02",
        "query": "Track parcel SHP-19999",
        "expected_intent": LogisticsIntent.SHIPMENT_TRACKING,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-19999",
    },
    {
        "id": "TC-03",
        "query": "Can you track tracking number SHP-14250?",
        "expected_intent": LogisticsIntent.SHIPMENT_TRACKING,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-14250",
    },
    {
        "id": "TC-04",
        "query": "Find the current location of shipment SHP-12005",
        "expected_intent": LogisticsIntent.SHIPMENT_TRACKING,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-12005",
    },
    {
        "id": "TC-05",
        "query": "Status check for package SHP-10050",
        "expected_intent": LogisticsIntent.SHIPMENT_TRACKING,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-10050",
    },
    {
        "id": "TC-06",
        "query": "Where has SHP-18420 reached?",
        "expected_intent": LogisticsIntent.SHIPMENT_TRACKING,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-18420",
    },

    # -------------------------------------------------------------
    # Category 2: SHIPMENT INFORMATION (Target: shipment_database)
    # -------------------------------------------------------------
    {
        "id": "TC-07",
        "query": "What are the dimensions and weight of cargo SHP-10045?",
        "expected_intent": LogisticsIntent.SHIPMENT_INFO,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-10045",
    },
    {
        "id": "TC-08",
        "query": "Who is the recipient and sender for order SHP-11200?",
        "expected_intent": LogisticsIntent.SHIPMENT_INFO,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-11200",
    },
    {
        "id": "TC-09",
        "query": "Show full manifest details for SHP-16500",
        "expected_intent": LogisticsIntent.SHIPMENT_INFO,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-16500",
    },
    {
        "id": "TC-10",
        "query": "What type of goods are in consignment SHP-13300?",
        "expected_intent": LogisticsIntent.SHIPMENT_INFO,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-13300",
    },
    {
        "id": "TC-11",
        "query": "Which hub is handling container SHP-17720?",
        "expected_intent": LogisticsIntent.SHIPMENT_INFO,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-17720",
    },

    # -------------------------------------------------------------
    # Category 3: DELIVERY UPDATES (Target: shipment_database)
    # -------------------------------------------------------------
    {
        "id": "TC-12",
        "query": "When is SHP-10002 expected to be delivered?",
        "expected_intent": LogisticsIntent.DELIVERY_UPDATES,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-10002",
    },
    {
        "id": "TC-13",
        "query": "What is the ETA for order SHP-10004?",
        "expected_intent": LogisticsIntent.DELIVERY_UPDATES,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-10004",
    },
    {
        "id": "TC-14",
        "query": "Has SHP-15500 been marked delivered yet?",
        "expected_intent": LogisticsIntent.DELIVERY_UPDATES,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-15500",
    },
    {
        "id": "TC-15",
        "query": "Why is the delivery delayed for SHP-14900?",
        "expected_intent": LogisticsIntent.DELIVERY_UPDATES,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-14900",
    },
    {
        "id": "TC-16",
        "query": "Expected arrival schedule for package SHP-10888",
        "expected_intent": LogisticsIntent.DELIVERY_UPDATES,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-10888",
    },

    # -------------------------------------------------------------
    # Category 4: COMPANY POLICY (Target: rag_knowledge_base)
    # -------------------------------------------------------------
    {
        "id": "TC-17",
        "query": "What is FleetHarbor policy on hazardous materials and dangerous goods?",
        "expected_intent": LogisticsIntent.COMPANY_POLICY,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-18",
        "query": "What is the compensation and claim policy for lost freight?",
        "expected_intent": LogisticsIntent.COMPANY_POLICY,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-19",
        "query": "Explain the cargo insurance and liability limits policy",
        "expected_intent": LogisticsIntent.COMPANY_POLICY,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-20",
        "query": "What are our safety compliance guidelines for warehouse operations?",
        "expected_intent": LogisticsIntent.COMPANY_POLICY,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-21",
        "query": "What is the return shipment and reverse logistics policy?",
        "expected_intent": LogisticsIntent.COMPANY_POLICY,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },

    # -------------------------------------------------------------
    # Category 5: LOGISTICS PROCESS (Target: rag_knowledge_base)
    # -------------------------------------------------------------
    {
        "id": "TC-22",
        "query": "What are the standard operational steps for cross-docking at the hub?",
        "expected_intent": LogisticsIntent.LOGISTICS_PROCESS,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-23",
        "query": "How is temperature-controlled cold chain cargo handled during transit?",
        "expected_intent": LogisticsIntent.LOGISTICS_PROCESS,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-24",
        "query": "Describe the container inspection checklist workflow prior to loading",
        "expected_intent": LogisticsIntent.LOGISTICS_PROCESS,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-25",
        "query": "Explain how last-mile dispatch routing is coordinated",
        "expected_intent": LogisticsIntent.LOGISTICS_PROCESS,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-26",
        "query": "What are the loading and weight distribution procedures for flatbed trucks?",
        "expected_intent": LogisticsIntent.LOGISTICS_PROCESS,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },

    # -------------------------------------------------------------
    # Category 6: DOCUMENTATION (Target: rag_knowledge_base)
    # -------------------------------------------------------------
    {
        "id": "TC-27",
        "query": "What documents are required for international customs clearance?",
        "expected_intent": LogisticsIntent.DOCUMENTATION,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-28",
        "query": "What is a Bill of Lading (BOL) and why is it needed?",
        "expected_intent": LogisticsIntent.DOCUMENTATION,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-29",
        "query": "How do I fill out a Commercial Invoice for cross-border shipping?",
        "expected_intent": LogisticsIntent.DOCUMENTATION,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-30",
        "query": "Where do I submit a Certificate of Origin for tariff exemption?",
        "expected_intent": LogisticsIntent.DOCUMENTATION,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-31",
        "query": "What paperwork is required for a dangerous goods declaration?",
        "expected_intent": LogisticsIntent.DOCUMENTATION,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },

    # -------------------------------------------------------------
    # Category 7: EMPLOYEE SUPPORT (Target: employee_directory)
    # -------------------------------------------------------------
    {
        "id": "TC-32",
        "query": "Look up employee directory record for staff EMP-20001",
        "expected_intent": LogisticsIntent.EMPLOYEE_SUPPORT,
        "expected_source": "employee_directory",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-33",
        "query": "What is the contact information for driver EMP-20050?",
        "expected_intent": LogisticsIntent.EMPLOYEE_SUPPORT,
        "expected_source": "employee_directory",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-34",
        "query": "Show warehouse supervisor assignment for EMP-20120",
        "expected_intent": LogisticsIntent.EMPLOYEE_SUPPORT,
        "expected_source": "employee_directory",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-35",
        "query": "Who is the logistics coordinator with ID EMP-20450?",
        "expected_intent": LogisticsIntent.EMPLOYEE_SUPPORT,
        "expected_source": "employee_directory",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-36",
        "query": "Find the assigned hub location for staff member EMP-20300",
        "expected_intent": LogisticsIntent.EMPLOYEE_SUPPORT,
        "expected_source": "employee_directory",
        "expected_shipment_id": None,
    },

    # -------------------------------------------------------------
    # Category 8: OPERATIONAL ISSUES (Target: rag_knowledge_base)
    # -------------------------------------------------------------
    {
        "id": "TC-37",
        "query": "There is a severe port congestion hold at JNPT terminal, what is the protocol?",
        "expected_intent": LogisticsIntent.OPERATIONAL_ISSUES,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-38",
        "query": "A delivery truck experienced an engine breakdown on highway NH48, who do we alert?",
        "expected_intent": LogisticsIntent.OPERATIONAL_ISSUES,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-39",
        "query": "Container seal was found broken upon arrival at the distribution center",
        "expected_intent": LogisticsIntent.OPERATIONAL_ISSUES,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-40",
        "query": "Severe weather blizzard warning is affecting northern freight routes",
        "expected_intent": LogisticsIntent.OPERATIONAL_ISSUES,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-41",
        "query": "Damaged pallet detected in sorting bay 4, how do we file the incident report?",
        "expected_intent": LogisticsIntent.OPERATIONAL_ISSUES,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,
    },

    # -------------------------------------------------------------
    # Category 9: GENERAL CONVERSATION (Target: deterministic_prompt)
    # -------------------------------------------------------------
    {
        "id": "TC-42",
        "query": "Hello! Good morning assistant.",
        "expected_intent": LogisticsIntent.GENERAL_CONVERSATION,
        "expected_source": "deterministic_prompt",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-43",
        "query": "Thank you so much for the assistance, that was very clear!",
        "expected_intent": LogisticsIntent.GENERAL_CONVERSATION,
        "expected_source": "deterministic_prompt",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-44",
        "query": "Who are you and what logistics tasks can you help me with?",
        "expected_intent": LogisticsIntent.GENERAL_CONVERSATION,
        "expected_source": "deterministic_prompt",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-45",
        "query": "Have a great evening, bye!",
        "expected_intent": LogisticsIntent.GENERAL_CONVERSATION,
        "expected_source": "deterministic_prompt",
        "expected_shipment_id": None,
    },

    # -------------------------------------------------------------
    # Category 10: UNSUPPORTED / OFF-TOPIC (Target: safe_fallback)
    # -------------------------------------------------------------
    {
        "id": "TC-46",
        "query": "Write a funny poem about green frogs in a pond.",
        "expected_intent": LogisticsIntent.UNSUPPORTED_OFFTOPIC,
        "expected_source": "safe_fallback",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-47",
        "query": "Who won the FIFA World Cup final in 1998?",
        "expected_intent": LogisticsIntent.UNSUPPORTED_OFFTOPIC,
        "expected_source": "safe_fallback",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-48",
        "query": "Explain the recipe for making Italian margherita pizza from scratch.",
        "expected_intent": LogisticsIntent.UNSUPPORTED_OFFTOPIC,
        "expected_source": "safe_fallback",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-49",
        "query": "What is the current stock price of Apple on NASDAQ?",
        "expected_intent": LogisticsIntent.UNSUPPORTED_OFFTOPIC,
        "expected_source": "safe_fallback",
        "expected_shipment_id": None,
    },
    {
        "id": "TC-50",
        "query": "Can you debug this React javascript frontend hook error?",
        "expected_intent": LogisticsIntent.UNSUPPORTED_OFFTOPIC,
        "expected_source": "safe_fallback",
        "expected_shipment_id": None,
    },

    # -------------------------------------------------------------
    # Multi-Turn Pronoun Reference Continuity Scenarios
    # -------------------------------------------------------------
    {
        "id": "TC-51",
        "query": "Where is it located right now?",
        "session_history": [{"role": "user", "content": "Track shipment SHP-10001"}],
        "expected_intent": LogisticsIntent.SHIPMENT_TRACKING,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-10001",
    },
    {
        "id": "TC-52",
        "query": "When will it arrive at destination?",
        "session_history": [{"role": "user", "content": "Tell me about SHP-10045"}],
        "expected_intent": LogisticsIntent.DELIVERY_UPDATES,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-10045",
    },
    {
        "id": "TC-53",
        "query": "What is its current delivery status?",
        "session_history": [{"role": "user", "content": "Status of SHP-19999"}],
        "expected_intent": LogisticsIntent.DELIVERY_UPDATES,
        "expected_source": "shipment_database",
        "expected_shipment_id": "SHP-19999",
    },
    {
        "id": "TC-54",
        "query": "What is the policy for hazardous materials?",
        "session_history": [{"role": "user", "content": "Track shipment SHP-10001"}],
        "expected_intent": LogisticsIntent.COMPANY_POLICY,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,  # Switched topic: pronoun NOT inherited
    },
    {
        "id": "TC-55",
        "query": "What documents are required for international customs?",
        "session_history": [{"role": "user", "content": "Where is SHP-10001?"}],
        "expected_intent": LogisticsIntent.DOCUMENTATION,
        "expected_source": "rag_knowledge_base",
        "expected_shipment_id": None,  # Switched topic: pronoun NOT inherited
    },
]


def run_evaluation() -> Dict[str, Any]:
    print("=" * 75)
    print("FLEETHARBOR LOGISTICS AI CHATBOT - EVALUATION BENCHMARK")
    print(f"Total Test Cases: {len(BENCHMARK_TEST_CASES)}")
    print("=" * 75)

    intent_correct = 0
    source_correct = 0
    shipment_id_correct = 0
    latencies: List[float] = []

    failures: List[Dict[str, Any]] = []

    for tc in BENCHMARK_TEST_CASES:
        query = tc["query"]
        history = tc.get("session_history", [])

        # Determine prior shipment ID from history if any
        prior_id = None
        if history:
            for msg in reversed(history):
                sid = extract_shipment_id(msg.get("content", ""))
                if sid:
                    prior_id = sid
                    break

        # Start timer for classification
        t0 = time.perf_counter()
        analysis: ClassifiedIntent = classify_logistics_query(
            query,
            session_history=history,
            previous_shipment_id=prior_id,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(elapsed_ms)

        actual_shipment_id = analysis.shipment_id

        # Validate Intent
        is_intent_ok = (analysis.intent == tc["expected_intent"])
        if is_intent_ok:
            intent_correct += 1

        # Validate Source
        is_source_ok = (analysis.preferred_source == tc["expected_source"])
        if is_source_ok:
            source_correct += 1

        # Validate Shipment ID
        is_shipment_id_ok = (actual_shipment_id == tc["expected_shipment_id"])
        if is_shipment_id_ok:
            shipment_id_correct += 1

        status_str = "PASS" if (is_intent_ok and is_source_ok and is_shipment_id_ok) else "FAIL"
        if status_str == "FAIL":
            failures.append({
                "id": tc["id"],
                "query": query,
                "expected": {
                    "intent": tc["expected_intent"].value,
                    "source": tc["expected_source"],
                    "shipment_id": tc["expected_shipment_id"],
                },
                "actual": {
                    "intent": analysis.intent.value,
                    "source": analysis.preferred_source,
                    "shipment_id": actual_shipment_id,
                },
            })

    total = len(BENCHMARK_TEST_CASES)
    intent_acc = (intent_correct / total) * 100.0
    source_acc = (source_correct / total) * 100.0
    shipment_acc = (shipment_id_correct / total) * 100.0

    sorted_latencies = sorted(latencies)
    avg_lat = sum(latencies) / total
    p50_lat = sorted_latencies[int(total * 0.50)]
    p95_lat = sorted_latencies[int(total * 0.95)]

    print(f"\nRESULTS SUMMARY:")
    print(f"-------------------------------------------------------------")
    print(f"Intent Classification Accuracy:    {intent_acc:.1f}% ({intent_correct}/{total})")
    print(f"Data Source Routing Accuracy:      {source_acc:.1f}% ({source_correct}/{total})")
    print(f"Shipment ID Extraction Accuracy:   {shipment_acc:.1f}% ({shipment_id_correct}/{total})")
    print(f"-------------------------------------------------------------")
    print(f"Query Classification Latency:")
    print(f"  Average: {avg_lat:.2f} ms")
    print(f"  P50:     {p50_lat:.2f} ms")
    print(f"  P95:     {p95_lat:.2f} ms")
    print(f"-------------------------------------------------------------")

    if failures:
        print(f"\nFAILURES ({len(failures)}):")
        for f in failures:
            print(f"[{f['id']}] Query: '{f['query']}'")
            print(f"  Expected: {f['expected']}")
            print(f"  Actual:   {f['actual']}")
    else:
        print("\nALL 55 BENCHMARK EVALUATION TEST CASES PASSED WITH 100% ACCURACY!")

    return {
        "total": total,
        "intent_accuracy": intent_acc,
        "source_accuracy": source_acc,
        "shipment_id_accuracy": shipment_acc,
        "p50_latency_ms": p50_lat,
        "p95_latency_ms": p95_lat,
        "avg_latency_ms": avg_lat,
        "failures_count": len(failures),
    }


if __name__ == "__main__":
    results = run_evaluation()
    if results["failures_count"] > 0:
        sys.exit(1)
    sys.exit(0)
