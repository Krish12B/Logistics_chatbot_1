"""Enterprise Logistics Query Intent Classifier and Intelligent Data Source Router.

Classifies incoming employee and customer queries into 10 domain-specific categories:
  1. SHIPMENT_TRACKING: Specific location/tracking requests for a shipment.
  2. SHIPMENT_INFO: General shipment attributes (route, origin, destination, cargo).
  3. DELIVERY_UPDATES: Expected delivery dates, arrival status, ETAs, delays.
  4. COMPANY_POLICY: Company regulations, SLAs, customer claims, liability, returns.
  5. LOGISTICS_PROCESS: Shipment lifecycle, warehouse SOPs, cold-chain protocols, container specs.
  6. DOCUMENTATION: Waybills (BOL/AWB), commercial invoices, customs paperwork, e-POD.
  7. EMPLOYEE_SUPPORT: Personnel roster lookup (EMP-xxxxx), hub dispatch, workplace safety.
  8. OPERATIONAL_ISSUES: Exception handling (customs holds, delays, demurrage, damaged goods).
  9. GENERAL_CONVERSATION: Greetings, capabilities, identity, help instructions.
  10. UNSUPPORTED_OFFTOPIC: Off-domain questions (quantum physics, recipes, unrelated math).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from logistics_chatbot.core.errors import InvalidShipmentIdError

logger = logging.getLogger("logistics_chatbot.classifier")

LOOSE_SHIPMENT_ID_PATTERN = re.compile(r"\bSHP[-\s]?(\d{3,6})\b", re.IGNORECASE)
VALID_SHIPMENT_ID_PATTERN = re.compile(r"^SHP-\d{5}$")
EMPLOYEE_ID_PATTERN = re.compile(r"\bEMP[-\s]?(\d{5})\b", re.IGNORECASE)

PRONOUN_FOLLOWUP_PATTERN = re.compile(
    r"\b(it|this|that|its|the shipment|the package|the order|the cargo|the container|where is it|when will it|is it)\b",
    re.IGNORECASE,
)


class LogisticsIntent(str, Enum):
    SHIPMENT_TRACKING = "shipment_tracking"
    SHIPMENT_INFO = "shipment_info"
    DELIVERY_UPDATES = "delivery_updates"
    COMPANY_POLICY = "company_policy"
    LOGISTICS_PROCESS = "logistics_process"
    DOCUMENTATION = "documentation"
    EMPLOYEE_SUPPORT = "employee_support"
    OPERATIONAL_ISSUES = "operational_issues"
    GENERAL_CONVERSATION = "general_conversation"
    UNSUPPORTED_OFFTOPIC = "unsupported_offtopic"


INTENT_SOURCE_MAP = {
    LogisticsIntent.SHIPMENT_TRACKING: "shipment_database",
    LogisticsIntent.SHIPMENT_INFO: "shipment_database",
    LogisticsIntent.DELIVERY_UPDATES: "shipment_database",
    LogisticsIntent.COMPANY_POLICY: "rag_knowledge_base",
    LogisticsIntent.LOGISTICS_PROCESS: "rag_knowledge_base",
    LogisticsIntent.DOCUMENTATION: "rag_knowledge_base",
    LogisticsIntent.EMPLOYEE_SUPPORT: "employee_directory",
    LogisticsIntent.OPERATIONAL_ISSUES: "rag_knowledge_base",
    LogisticsIntent.GENERAL_CONVERSATION: "deterministic_prompt",
    LogisticsIntent.UNSUPPORTED_OFFTOPIC: "safe_fallback",
}


@dataclass
class ClassifiedIntent:
    """Detailed intent analysis result."""
    intent: LogisticsIntent
    confidence: float
    preferred_source: str
    shipment_id: Optional[str] = None
    employee_id: Optional[str] = None
    resolved_reference: bool = False
    target_attribute: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)


def extract_shipment_id(text: str) -> Optional[str]:
    """Extract and validate a shipment ID from text (e.g. 'SHP-10001')."""
    match = LOOSE_SHIPMENT_ID_PATTERN.search(text)
    if not match:
        return None
    raw = match.group(0).upper().replace(" ", "")
    digits = match.group(1)
    formatted = f"SHP-{digits}"
    if not VALID_SHIPMENT_ID_PATTERN.match(formatted):
        raise InvalidShipmentIdError(
            f"'{raw}' doesn't look like a valid shipment ID. IDs look like SHP-10001 (SHP, a dash, then 5 digits)."
        )
    return formatted


def extract_employee_id(text: str) -> Optional[str]:
    """Extract an employee ID (e.g. 'EMP-20001')."""
    match = EMPLOYEE_ID_PATTERN.search(text)
    if match:
        return f"EMP-{match.group(1)}"
    return None


# ── Pattern Dictionaries for Category Classification ─────────────────

GREETING_EXACT = {
    "hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening",
    "howdy", "sup", "welcome", "help", "help me",
    "who are you", "who r u", "what are you", "what r u",
    "tell me about yourself", "introduce yourself",
    "how can you help", "how can u help",
    "how can you help me", "how can u help me",
    "how do you help", "how do u help",
    "what can you do", "what can u do", "what do you do",
    "what can you help with", "what can u help with",
    "what can you help me with", "what can u help me with",
    "can you help me", "can u help me",
    "can you help", "can u help",
    "how does this work", "how to use this", "how to use",
    "what is fleetharbor", "what is fleetharbor ai",
    "what are your capabilities", "what services do you offer",
    "what services do you provide",
}

CONVERSATIONAL_PATTERNS = [
    r"\b(hello|hi|hey|greetings|good\s+morning|good\s+afternoon|good\s+evening)\b",
    r"\b(thank\s+you|thanks|appreciate\s+it|thx)\b",
    r"\b(bye|goodbye|see\s+you|have\s+a\s+(?:good|great)\s+(?:day|evening|night))\b",
    r"\b(who\s+are\s+you|what\s+can\s+you\s+do|what\s+do\s+you\s+do|help\s+me|what\s+(?:can\s+you\s+)?help(?:\s+me)?\s+with|how\s+can\s+you\s+help|what\s+services\s+do\s+you\s+(?:offer|provide))\b",
]

DOCUMENTATION_KEYWORDS = (
    "bill of lading", "bol", "air waybill", "awb", "commercial invoice", "packing list",
    "certificate of origin", "customs document", "shipping document", "proof of delivery",
    "pod", "e-pod", "shipper letter of instruction", "sli", "paperwork", "invoice guide",
    "export declaration", "import declaration", "customs clearance", "border clearance",
)

POLICY_KEYWORDS = (
    "policy", "claim", "claims", "compensation", "liability", "terms and conditions",
    "shipping terms", "refund", "sla", "service level", "guarantee", "cancellation policy",
    "customer rule", "payment terms", "credit limit", "claims filing", "compliance",
    "guidelines", "safety compliance", "insurance", "reverse logistics", "return shipment",
    "return policy",
)

PROCESS_KEYWORDS = (
    "lifecycle", "shipment lifecycle", "cross-docking", "consolidation", "deconsolidation",
    "hub sorting", "forklift", "cold-chain", "cold chain", "pharma", "gdp", "dry ice",
    "temperature range", "temperature-controlled", "cargo weight", "dimension limit",
    "container spec", "pallet", "iso container", "20ft", "40ft", "high cube", "reefer",
    "packaging rule", "lithium battery", "hazmat", "dangerous goods", "dg class", "intermodal",
    "inspection checklist", "checklist workflow", "inspection workflow", "dispatch routing",
    "weight distribution", "flatbed", "loading procedure", "standard operational steps",
)

OPERATIONAL_KEYWORDS = (
    "customs hold", "on hold", "demurrage", "detention", "per diem", "port congestion",
    "weather disruption", "damaged goods", "lost package", "exception", "broken seal",
    "seal was found broken", "seal broken", "tampered", "engine breakdown", "breakdown",
    "incident report", "incident", "damaged pallet", "severe weather", "blizzard",
    "weather warning", "who do we alert", "emergency alert", "highway", "strike",
)

EMPLOYEE_KEYWORDS = (
    "employee", "staff", "personnel", "worker", "shift", "hub manager", "forklift operator",
    "dispatcher", "safety equipment", "ppe", "warehouse rule", "warehouse sop",
    "speed limit", "emergency exit", "overtime", "request overtime", "reporting an injury",
    "safety incident", "vehicle inspection pre-trip", "pre-trip", "benefits", "ppe allowance",
    "hr contact", "rescheduling", "directory record",
)

OFFTOPIC_PATTERNS = [
    r"\b(quantum|black\s*hole|string\s*theory|relativity|einstein|astrophysics)\b",
    r"\b(recipe|bake|baking|cooking|ingredients?|pizza|cake|pasta|cocktail|dessert)\b",
    r"\b(movie|song|lyrics|guitar|chord|actor|celebrity)\b",
    r"\b(president|election|democrat|republican|political)\b",
    r"\b(write\s+(?:a\s+)?(?:funny\s+|short\s+|rhyming\s+)?(?:poem|story|song|essay|joke))\b",
    r"\b(fifa|world\s*cup|olympics|nfl|nba|football|soccer|cricket|tennis|championship)\b",
    r"\b(stock\s*price|nasdaq|dow\s*jones|crypto|bitcoin|ethereum|shares?\s+of)\b",
    r"\b(debug|react|javascript|python\s+code|html|css|frontend|backend\s+code|hook\s+error)\b",
]


def classify_logistics_query(
    query: str,
    session_history: Optional[List[Dict[str, str]]] = None,
    previous_shipment_id: Optional[str] = None,
) -> ClassifiedIntent:
    """Classify user query into 10 distinct logistics intents with reference resolution.

    Args:
        query: User input query text.
        session_history: Optional list of past chat turns [{"role": ..., "content": ...}].
        previous_shipment_id: Optional shipment ID actively tracked in conversation session.

    Returns:
        ClassifiedIntent dataclass with intent, preferred source, and resolved entities.
    """
    clean = re.sub(r"[?!.,;:]+", " ", query.strip().lower())
    clean = re.sub(r"\s+", " ", clean).strip()

    # 1. Check for Explicit Employee Lookup
    emp_id = extract_employee_id(query)
    if emp_id:
        return ClassifiedIntent(
            intent=LogisticsIntent.EMPLOYEE_SUPPORT,
            confidence=0.98,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.EMPLOYEE_SUPPORT],
            employee_id=emp_id,
        )

    # 2. Check for Greetings, Capabilities, and Polite Conversation
    is_conversational = clean in GREETING_EXACT or any(re.search(p, clean) for p in CONVERSATIONAL_PATTERNS)
    if is_conversational:
        # Ensure it doesn't contain freight IDs or operational questions
        if not re.search(r"\b(shp-\d+|track|customs|bol|cargo)\b", clean):
            return ClassifiedIntent(
                intent=LogisticsIntent.GENERAL_CONVERSATION,
                confidence=0.99,
                preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.GENERAL_CONVERSATION],
            )

    # 3. Check for Explicit Shipment ID in query
    direct_shipment_id = None
    try:
        direct_shipment_id = extract_shipment_id(query)
    except InvalidShipmentIdError:
        raise

    # 4. Multi-Turn Reference Resolution (Pronoun handling)
    resolved_shipment_id = direct_shipment_id
    resolved_reference = False

    if not resolved_shipment_id and previous_shipment_id:
        # Check if the query refers to the prior shipment via pronoun or contextual phrase
        has_pronoun = bool(PRONOUN_FOLLOWUP_PATTERN.search(query))
        tracking_followups = ("where", "status", "location", "arrive", "arrival", "eta", "delivered", "delay", "route", "destination", "origin")
        is_tracking_inquiry = any(w in clean for w in tracking_followups)

        # Ensure the user didn't shift to an independent documentation/policy/employee question
        has_independent_domain = any(k in clean for k in (
            "bill of lading", "commercial invoice", "customs document", "claims", "refund",
            "forklift", "pharma", "cargo weight", "dimension limit", "container spec"
        ))

        if (has_pronoun or is_tracking_inquiry) and not has_independent_domain:
            resolved_shipment_id = previous_shipment_id
            resolved_reference = True
            logger.info("Resolved pronoun reference to previous shipment: %s", previous_shipment_id)

    # 5. Routing for Shipment Inquiries
    if resolved_shipment_id:
        # Delivery updates: when, arrive, eta, delay reason, delivery status for this shipment
        if re.search(r"\b(when|arrive|arrival|eta|delivery\s+(?:date|status|schedule|update|time)|delivery|delivered|delay|delayed)\b", clean):
            return ClassifiedIntent(
                intent=LogisticsIntent.DELIVERY_UPDATES,
                confidence=0.95,
                preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.DELIVERY_UPDATES],
                shipment_id=resolved_shipment_id,
                resolved_reference=resolved_reference,
                target_attribute="eta",
            )
        # Shipment info: dimensions, weight, cargo, sender, receiver, manifest, goods, contents, route, hub
        elif re.search(r"\b(dimensions?|weight|cargo|goods|consignment|manifest|recipient|receiver|sender|consignor|consignee|hub|route|origin|destination|contents?|specs?|specification|details?|info)\b", clean):
            return ClassifiedIntent(
                intent=LogisticsIntent.SHIPMENT_INFO,
                confidence=0.95,
                preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.SHIPMENT_INFO],
                shipment_id=resolved_shipment_id,
                resolved_reference=resolved_reference,
                target_attribute="details",
            )
        # Tracking: location, where, track, position, reached, status
        else:
            return ClassifiedIntent(
                intent=LogisticsIntent.SHIPMENT_TRACKING,
                confidence=0.95,
                preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.SHIPMENT_TRACKING],
                shipment_id=resolved_shipment_id,
                resolved_reference=resolved_reference,
                target_attribute="location",
            )

    # 6. Check for Documentation Questions (Give priority to document/form queries)
    if any(k in clean for k in ("document", "documentation", "paperwork", "form", "forms")) or any(k in clean for k in DOCUMENTATION_KEYWORDS):
        return ClassifiedIntent(
            intent=LogisticsIntent.DOCUMENTATION,
            confidence=0.95,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.DOCUMENTATION],
        )

    # 7. Check for Company Policy & Claims
    if any(k in clean for k in POLICY_KEYWORDS):
        return ClassifiedIntent(
            intent=LogisticsIntent.COMPANY_POLICY,
            confidence=0.92,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.COMPANY_POLICY],
        )

    # 8. Check for Operational Exceptions (Customs holds, delays, demurrage)
    if any(k in clean for k in OPERATIONAL_KEYWORDS):
        return ClassifiedIntent(
            intent=LogisticsIntent.OPERATIONAL_ISSUES,
            confidence=0.91,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.OPERATIONAL_ISSUES],
        )

    # 9. Check for Logistics Processes & Technical Standards
    if any(k in clean for k in PROCESS_KEYWORDS):
        return ClassifiedIntent(
            intent=LogisticsIntent.LOGISTICS_PROCESS,
            confidence=0.91,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.LOGISTICS_PROCESS],
        )

    # 10. Check for Employee & Warehouse Support
    if any(k in clean for k in EMPLOYEE_KEYWORDS):
        return ClassifiedIntent(
            intent=LogisticsIntent.EMPLOYEE_SUPPORT,
            confidence=0.88,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.EMPLOYEE_SUPPORT],
        )

    # 11. Check for Clearly Off-Topic Queries
    for pat in OFFTOPIC_PATTERNS:
        if re.search(pat, clean):
            return ClassifiedIntent(
                intent=LogisticsIntent.UNSUPPORTED_OFFTOPIC,
                confidence=0.96,
                preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.UNSUPPORTED_OFFTOPIC],
            )

    # Default fallback: RAG Knowledge Search with low/moderate confidence
    return ClassifiedIntent(
        intent=LogisticsIntent.LOGISTICS_PROCESS,
        confidence=0.75,
        preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.LOGISTICS_PROCESS],
    )
