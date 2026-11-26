"""Evaluation metrics and scoring engine for FleetHarbor Logistics AI Chatbot.
Evaluates chatbot responses across 10 distinct quality dimensions (0 to 5 scale):
  1. Accuracy
  2. Relevance
  3. Completeness
  4. Logic
  5. Data Correctness (deterministic comparison against SQLite ground truth)
  6. Retrieval Quality (source grounding)
  7. Formatting (Markdown tables, headers, bullet points)
  8. Context Awareness (multi-turn reference resolution)
  9. Hallucination Prevention
  10. Performance / Latency
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional, Tuple


def evaluate_response(
    query: str,
    response_text: str,
    sources: List[str],
    latency_ms: float,
    expected_intent: Optional[str] = None,
    ground_truth: Optional[Dict[str, Any]] = None,
    required_shipment_id: Optional[str] = None,
    required_concepts: Optional[List[str]] = None,
    is_multi_turn: bool = False,
    turn_number: int = 1,
    status_code: int = 200,
) -> Dict[str, Any]:
    """Score a response across 10 dimensions on a scale of 0.0 to 5.0.

    Returns a detailed evaluation dictionary with scores and explanations.
    """
    scores = {}
    notes = []
    text_lower = response_text.lower() if response_text else ""

    # 1. Performance / Latency (0 to 5)
    # < 50ms: 5.0, < 250ms: 4.8, < 500ms: 4.5, < 1500ms: 4.0, < 3000ms: 3.5, < 5000ms: 3.0, >= 5000ms: 2.0
    if latency_ms < 50:
        perf_score = 5.0
    elif latency_ms < 250:
        perf_score = 4.8
    elif latency_ms < 500:
        perf_score = 4.5
    elif latency_ms < 1500:
        perf_score = 4.0
    elif latency_ms < 3000:
        perf_score = 3.5
    elif latency_ms < 6000:
        perf_score = 3.0
    else:
        perf_score = 2.0
    scores["performance"] = perf_score

    # 2. Formatting (0 to 5)
    # Check for markdown structure, headers, lists, tables, clean paragraphs
    format_points = 3.0
    if "#" in response_text:
        format_points += 0.7
    if "|" in response_text and "---" in response_text:
        format_points += 0.8  # Clean table
    if re.search(r"^\s*[-*]\s+", response_text, re.MULTILINE):
        format_points += 0.5  # Bullet lists
    # Deduct if unparsed raw tokens or JSON leaked
    if "{" in response_text and "}" in response_text and '"' in response_text:
        format_points -= 1.5
    if "[DOC-" in response_text or "[FAQ-" in response_text:
        # Raw uncleaned bracket citations inside body text
        format_points -= 0.5
    scores["formatting"] = max(1.0, min(5.0, round(format_points, 1)))

    # 3. Data Correctness (0 to 5)
    # Deterministic verification against SQLite database fields
    if ground_truth:
        correct_fields = 0
        total_fields = 0
        for field_name, expected_val in ground_truth.items():
            if not expected_val:
                continue
            total_fields += 1
            exp_str = str(expected_val).lower().strip()
            if exp_str in text_lower:
                correct_fields += 1
            else:
                # Check for parts, e.g. "Dubai Hub" in "Dubai Hub, UAE"
                parts = [p.strip() for p in exp_str.split(",") if len(p.strip()) > 3]
                if any(p in text_lower for p in parts):
                    correct_fields += 1
                else:
                    notes.append(f"Missing expected field '{field_name}': '{expected_val}'")

        if total_fields > 0:
            match_ratio = correct_fields / total_fields
            data_score = round(match_ratio * 5.0, 1)
        else:
            data_score = 5.0
    elif required_shipment_id:
        if required_shipment_id.lower() in text_lower:
            data_score = 4.5
        else:
            data_score = 2.0
            notes.append(f"Shipment ID {required_shipment_id} not explicitly referenced in response.")
    else:
        # Non-database general or edge question
        data_score = 4.5
    scores["data_correctness"] = max(0.0, min(5.0, data_score))

    # 4. Accuracy & Truthfulness (0 to 5)
    accuracy_score = 4.0
    if required_concepts:
        matched_concepts = sum(1 for c in required_concepts if c.lower() in text_lower)
        concept_ratio = matched_concepts / max(1, len(required_concepts))
        accuracy_score = round(1.0 + (concept_ratio * 4.0), 1)
        if concept_ratio < 0.5:
            notes.append(f"Matched {matched_concepts}/{len(required_concepts)} key concepts.")
    elif ground_truth:
        accuracy_score = scores["data_correctness"]

    # Check for empty response or error response
    if not response_text or len(response_text.strip()) < 10:
        accuracy_score = 0.5
        notes.append("Response is empty or too short.")
    elif "temporarily unavailable" in text_lower or "internal server error" in text_lower:
        accuracy_score = 2.0
        notes.append("System returned fallback unavailable message.")

    scores["accuracy"] = max(0.0, min(5.0, accuracy_score))

    # 5. Relevance (0 to 5)
    # Does it directly address user intent?
    relevance_score = 4.5
    if expected_intent == "clarification_request":
        # Response should ask for shipment ID or clarification, not invent an answer
        clarification_markers = ["please provide", "shipment id", "tracking number", "which shipment", "could you clarify", "format"]
        if any(cm in text_lower for cm in clarification_markers):
            relevance_score = 5.0
        else:
            relevance_score = 2.0
            notes.append("Expected clarification request, but chatbot did not prompt user.")
    elif expected_intent == "unsupported_offtopic":
        if "outside" in text_lower or "logistics domain" in text_lower or "cannot assist with" in text_lower or "support@fleetharbor.com" in text_lower:
            relevance_score = 5.0
        else:
            relevance_score = 2.0
            notes.append("Failed to decline off-topic query politely.")
    elif required_shipment_id and required_shipment_id.lower() not in text_lower and "not found" not in text_lower:
        relevance_score = 2.5
    scores["relevance"] = max(0.0, min(5.0, relevance_score))

    # 6. Completeness (0 to 5)
    completeness_score = 4.0
    if len(response_text) > 250:
        completeness_score = 4.8
    elif len(response_text) > 100:
        completeness_score = 4.0
    elif len(response_text) > 40:
        completeness_score = 3.2
    else:
        completeness_score = 2.0
    scores["completeness"] = min(5.0, completeness_score)

    # 7. Logic & Reasoning (0 to 5)
    logic_score = 4.5
    # If delayed, must have delay reason or explanation
    if "delayed" in text_lower and "delay reason" not in text_lower and "because" not in text_lower and "due to" not in text_lower:
        logic_score -= 0.5
    # If delivered, must not state in progress
    if "🟢 delivered" in text_lower and "in progress" in text_lower:
        logic_score -= 1.0
        notes.append("Contradictory status: marked Delivered but also In Progress.")
    scores["logic"] = max(1.0, min(5.0, logic_score))

    # 8. Retrieval Quality (0 to 5)
    retrieval_score = 4.0
    if sources and len(sources) > 0:
        retrieval_score = 4.8
        # Check source validity
        if any("Shipment Database" in s or "Uploaded Knowledge" in s or "Policy" in s or "Manual" in s or "Employee" in s for s in sources):
            retrieval_score = 5.0
    elif expected_intent in ("general_conversation", "clarification_request", "unsupported_offtopic", "error_handling"):
        retrieval_score = 5.0  # Intentional zero sources for conversational / guardrails
    elif "not found" in text_lower or "unavailable" in text_lower:
        retrieval_score = 4.0
    else:
        retrieval_score = 3.0
    scores["retrieval_quality"] = retrieval_score

    # 9. Context Awareness (0 to 5)
    context_score = 4.5
    if is_multi_turn:
        if turn_number > 1:
            if "i couldn't find" in text_lower or "please provide" in text_lower:
                context_score = 2.5
                notes.append("Failed to retain context across multi-turn session.")
            else:
                context_score = 5.0
    scores["context_awareness"] = context_score

    # 10. Hallucination Prevention (0 to 5)
    hallucination_score = 5.0
    if "SHP-99999" in query and "delivered" in text_lower and "not found" not in text_lower:
        hallucination_score = 0.0  # Fabricated non-existent shipment
        notes.append("Hallucinated data for non-existent shipment SHP-99999!")
    elif "EMP-99999" in query and "active" in text_lower and "could not find" not in text_lower:
        hallucination_score = 0.0
        notes.append("Hallucinated data for non-existent employee EMP-99999!")
    scores["hallucination_prevention"] = hallucination_score

    # Calculate Overall Score (weighted average out of 5.0)
    weights = {
        "accuracy": 0.20,
        "relevance": 0.15,
        "data_correctness": 0.15,
        "logic": 0.10,
        "completeness": 0.10,
        "retrieval_quality": 0.10,
        "hallucination_prevention": 0.10,
        "formatting": 0.05,
        "context_awareness": 0.05,
    }
    overall_score = sum(scores[k] * weights[k] for k in weights if k in scores)
    scores["overall"] = round(overall_score, 2)
    scores["passed"] = scores["overall"] >= 3.0 and scores["hallucination_prevention"] >= 3.0

    return {
        "scores": scores,
        "notes": notes,
        "passed": scores["passed"],
        "overall_score": scores["overall"],
    }
