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
BOOKING_ID_PATTERN = re.compile(r"\bALC[-\s]?(\d{4})[-\s]?(\d{5,7})\b", re.IGNORECASE)
UUID_PATTERN = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE)
EMPLOYEE_ID_PATTERN = re.compile(r"\bEMP[-\s]?(\d{5})\b", re.IGNORECASE)
OPERATIONAL_ID_PATTERN = re.compile(r"\bOPS[-\s]?(\d{1,6})\b", re.IGNORECASE)

PRONOUN_FOLLOWUP_PATTERN = re.compile(
    r"\b(it|this|that|its|this shipment|the shipment|the package|the order|the cargo|the container|the booking|where is it|when will it|is it)\b",
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
    OPERATIONAL_STATUS = "operational_status"
    GENERAL_CONVERSATION = "general_conversation"
    UNSUPPORTED_OFFTOPIC = "unsupported_offtopic"
    CLARIFICATION_REQUIRED = "clarification_required"


INTENT_SOURCE_MAP = {
    LogisticsIntent.SHIPMENT_TRACKING: "shipment_database",
    LogisticsIntent.SHIPMENT_INFO: "shipment_database",
    LogisticsIntent.DELIVERY_UPDATES: "shipment_database",
    LogisticsIntent.COMPANY_POLICY: "rag_knowledge_base",
    LogisticsIntent.LOGISTICS_PROCESS: "rag_knowledge_base",
    LogisticsIntent.DOCUMENTATION: "rag_knowledge_base",
    LogisticsIntent.EMPLOYEE_SUPPORT: "employee_directory",
    LogisticsIntent.OPERATIONAL_ISSUES: "rag_knowledge_base",
    LogisticsIntent.OPERATIONAL_STATUS: "operational_database",
    LogisticsIntent.GENERAL_CONVERSATION: "deterministic_prompt",
    LogisticsIntent.UNSUPPORTED_OFFTOPIC: "safe_fallback",
    LogisticsIntent.CLARIFICATION_REQUIRED: "clarification_engine",
}


@dataclass
class ClassifiedIntent:
    """Detailed intent analysis result."""
    intent: LogisticsIntent
    confidence: float
    preferred_source: str
    shipment_id: Optional[str] = None
    booking_id: Optional[str] = None
    employee_id: Optional[str] = None
    operational_id: Optional[str] = None
    resolved_reference: bool = False
    target_attribute: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)


def normalize_logistics_query(text: str) -> str:
    """Normalize user query and correct common typos while leaving identifiers untouched."""
    if not text:
        return ""
    typo_map = {
        r"\bsta[ut]{2}s\b": "status",
        r"\bstaus\b": "status",
        r"\bstauts\b": "status",
        r"\bstatuss\b": "status",
        r"\bstats\b": "status",
        r"\bloction\b": "location",
        r"\blocaton\b": "location",
        r"\bwhre\b": "where",
        r"\bdelivry\b": "delivery",
        r"\bdeleivery\b": "delivery",
        r"\bdelivary\b": "delivery",
        r"\bempolyee\b": "employee",
        r"\bemploye\b": "employee",
        r"\boprational\b": "operational",
        r"\boperatinal\b": "operational",
        r"\btrackng\b": "tracking",
        r"\btrck\b": "track",
        r"\bshpment\b": "shipment",
        r"\bshipmnt\b": "shipment",
    }
    normalized = text
    for pattern, replacement in typo_map.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    return normalized


def extract_operational_id(text: str) -> Optional[str]:
    """Extract an operational record ID (e.g. 'OPS-001', 'ops-025', 'OPS 001')."""
    match = OPERATIONAL_ID_PATTERN.search(text)
    if match:
        digits = match.group(1)
        if len(digits) < 3:
            digits = f"{int(digits):03d}"
        return f"OPS-{digits}"
    return None


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


def extract_booking_id(text: str) -> Optional[str]:
    """Extract an enterprise booking reference (e.g. 'ALC-2025-100000') or UUID."""
    match = BOOKING_ID_PATTERN.search(text or "")
    if match:
        return f"ALC-{match.group(1)}-{match.group(2)}"
    uuid_match = UUID_PATTERN.search(text or "")
    if uuid_match:
        return uuid_match.group(0).lower()
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
    "hs code", "hs codes", "tariff classification", "letter of credit", "shipping bill",
    "bill of entry", "insurance certificate", "export-import", "export import",
)

POLICY_KEYWORDS = (
    "policy", "claim", "claims", "compensation", "liability", "terms and conditions",
    "shipping terms", "refund", "sla", "service level", "guarantee", "cancellation policy",
    "customer rule", "payment terms", "credit limit", "claims filing", "compliance",
    "guidelines", "safety compliance", "insurance", "reverse logistics", "return shipment",
    "return policy", "incoterm", "incoterms",
)

INCOTERM_WORD_PATTERN = re.compile(
    r"\b(exw|fca|cpt|cip|dap|dpu|ddp|fas|fob|cfr|cif|incoterms?)\b",
    re.IGNORECASE,
)

PROCESS_KEYWORDS = (
    "lifecycle", "shipment lifecycle", "cross-docking", "consolidation", "deconsolidation",
    "hub sorting", "forklift", "cold-chain", "cold chain", "pharma", "gdp", "dry ice",
    "temperature range", "temperature-controlled", "cargo weight", "dimension limit",
    "container spec", "pallet", "iso container", "20ft", "40ft", "high cube", "reefer",
    "packaging rule", "lithium battery", "hazmat", "dangerous goods", "dg class", "intermodal",
    "inspection checklist", "checklist workflow", "inspection workflow", "dispatch routing",
    "weight distribution", "flatbed", "loading procedure", "standard operational steps",
    "bonded warehouse", "bonded warehousing", "open warehouse", "open warehousing",
    "dwell time", "contract logistics", "third-party logistics", "warehouse management system",
    "booking process", "make a booking", "ecu360", "track a shipment",
)

OPERATIONAL_KEYWORDS = (
    "customs hold", "on hold", "demurrage", "detention", "per diem", "port congestion",
    "weather disruption", "damaged goods", "lost package", "exception", "broken seal",
    "seal was found broken", "seal broken", "tampered", "engine breakdown", "breakdown",
    "incident report", "incident", "damaged pallet", "severe weather", "blizzard",
    "weather warning", "who do we alert", "emergency alert", "highway", "strike",
    "chokepoint", "vessel variance", "schedule reliability", "route risk", "delay causes",
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
    r"\b(president|election|democrat|republican|political|prime\s+minister)\b",
    r"\b(write\s+(?:a\s+)?(?:funny\s+|short\s+|rhyming\s+)?(?:poem|story|song|essay|joke))\b",
    r"\b(fifa|world\s*cup|olympics|nfl|nba|football|soccer|cricket|tennis|championship)\b",
    r"\b(stock\s*price|nasdaq|dow\s*jones|crypto|bitcoin|ethereum|shares?\s+of)\b",
    r"\b(debug|react|javascript|python\s+code|html|css|frontend|backend\s+code|hook\s+error)\b",
    r"\b(mars|jupiter|saturn|venus|neptune|uranus|pluto|moon|planet|astronomy|solar\s+system)\b",
    r"\b(capital\s+of|population\s+of|who\s+invented|translate\s+to)\b",
    r"\b(weather|forecast|rain|sunny)\b(?!.*\b(shipment|delay|delayed|route|freight|blizzard|warning|cargo|hub|vessel|port)\b)",
]

SQL_INJECTION_PATTERNS = [
    r"\b(drop\s+table|delete\s+from|insert\s+into|truncate\s+table|alter\s+table)\b",
    r"\b(select\s+\*\s+from|union\s+select|;\s*drop\s+|'\s*or\s+'1'\s*=\s*'1)\b",
]

EMPLOYEE_PRONOUN_PATTERN = re.compile(
    r"\b(he|she|his|her|him|they|their|them|this employee|that employee|the employee|staff member)\b",
    re.IGNORECASE,
)

EMPLOYEE_FOLLOWUP_ATTR_KEYWORDS = (
    "what shift", "which shift", "shift", "hub", "email", "extension", "phone",
    "department", "job title", "role", "certification", "assigned", "contact",
)


def classify_logistics_query(
    query: str,
    session_history: Optional[List[Dict[str, str]]] = None,
    previous_shipment_id: Optional[str] = None,
    previous_employee_id: Optional[str] = None,
) -> ClassifiedIntent:
    """Classify user query into distinct logistics intents with reference resolution.

    Args:
        query: User input query text.
        session_history: Optional list of past chat turns [{"role": ..., "content": ...}].
        previous_shipment_id: Optional shipment ID actively tracked in conversation session.
        previous_employee_id: Optional employee ID actively discussed in conversation session.

    Returns:
        ClassifiedIntent dataclass with intent, preferred source, and resolved entities.
    """
    normalized_query = normalize_logistics_query(query)
    clean = re.sub(r"[?!.,;:]+", " ", normalized_query.strip().lower())
    clean = re.sub(r"\s+", " ", clean).strip()

    # 0. Reject SQL injection probes before keyword matching hits 'shipments' or 'users'
    for sql_pat in SQL_INJECTION_PATTERNS:
        if re.search(sql_pat, normalized_query, re.IGNORECASE):
            return ClassifiedIntent(
                intent=LogisticsIntent.UNSUPPORTED_OFFTOPIC,
                confidence=0.99,
                preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.UNSUPPORTED_OFFTOPIC],
                entities={"security_block": "sql_injection"},
            )

    # 1. Check for Explicit Operational Case / Record Lookup (e.g. OPS-001)
    ops_id = extract_operational_id(normalized_query)
    if ops_id:
        return ClassifiedIntent(
            intent=LogisticsIntent.OPERATIONAL_STATUS,
            confidence=0.99,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.OPERATIONAL_STATUS],
            operational_id=ops_id,
            entities={"operational_id": ops_id},
        )

    # 2. Check for Explicit Employee Lookup
    emp_id = extract_employee_id(normalized_query)
    if emp_id:
        return ClassifiedIntent(
            intent=LogisticsIntent.EMPLOYEE_SUPPORT,
            confidence=0.98,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.EMPLOYEE_SUPPORT],
            employee_id=emp_id,
        )

    # 2b. Check for Greetings, Capabilities, and Polite Conversation
    is_conversational = clean in GREETING_EXACT or any(re.search(p, clean) for p in CONVERSATIONAL_PATTERNS)
    if is_conversational:
        # Ensure it doesn't contain freight IDs or operational questions
        if not re.search(r"\b(shp-\d+|track|customs|bol|cargo)\b", clean):
            return ClassifiedIntent(
                intent=LogisticsIntent.GENERAL_CONVERSATION,
                confidence=0.99,
                preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.GENERAL_CONVERSATION],
            )

    # 2c. Check for Aggregate Shipment Analytics & Count Queries
    is_shipment_count_query = (
        re.search(r"\b(how\s+many|count|total|number\s+of|breakdown|summary|overview\s+of)\b", clean) and
        re.search(r"\b(shipments?|packages?|orders?|cargo|freight|consignments?)\b", clean)
    ) or clean in ("total shipments", "all shipments count", "how many shipments", "shipment count", "shipment breakdown")

    if is_shipment_count_query:
        status_target = None
        if re.search(r"\b(in\s+transit|transit|moving)\b", clean):
            status_target = "In Transit"
        elif re.search(r"\b(delivered|completed|received)\b", clean):
            status_target = "Delivered"
        elif re.search(r"\b(delayed|delay|delays)\b", clean):
            status_target = "Delayed"
        elif re.search(r"\b(customs|customs\s+hold|on\s+hold|hold)\b", clean):
            status_target = "On Hold - Customs"
        elif re.search(r"\b(out\s+for\s+delivery)\b", clean):
            status_target = "Out for Delivery"
        elif re.search(r"\b(pending)\b", clean):
            status_target = "Pending"

        return ClassifiedIntent(
            intent=LogisticsIntent.SHIPMENT_INFO,
            confidence=0.98,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.SHIPMENT_INFO],
            target_attribute="aggregate_count",
            entities={"status_filter": status_target},
        )

    # 2d. Check for Aggregate Employee Count Queries
    is_employee_count_query = (
        re.search(r"\b(how\s+many|count|total|number\s+of|breakdown|summary)\b", clean) and
        re.search(r"\b(employees?|staff|workers?|personnel|drivers?|workforce)\b", clean)
    )
    if is_employee_count_query:
        return ClassifiedIntent(
            intent=LogisticsIntent.EMPLOYEE_SUPPORT,
            confidence=0.98,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.EMPLOYEE_SUPPORT],
            target_attribute="aggregate_count",
        )

    # 3. Check for Explicit Shipment ID (SHP-xxxxx) or Enterprise Booking Reference (ALC-YYYY-XXXXXX)
    direct_shipment_id = None
    try:
        direct_shipment_id = extract_shipment_id(query)
    except InvalidShipmentIdError:
        raise
    direct_booking_id = extract_booking_id(query) if not direct_shipment_id else None

    # 4a. Multi-Turn Employee Pronoun Resolution (e.g., 'What shift does she work?' after EMP-20001)
    if not direct_shipment_id and not direct_booking_id and previous_employee_id:
        has_emp_pronoun = bool(EMPLOYEE_PRONOUN_PATTERN.search(clean))
        has_emp_attr = any(k in clean for k in EMPLOYEE_FOLLOWUP_ATTR_KEYWORDS)
        has_explicit_shipment_word = bool(re.search(r"\b(shipment|package|parcel|cargo|container|order|waybill)\b", clean))
        if has_emp_pronoun and has_emp_attr and not has_explicit_shipment_word:
            logger.info("Resolved employee pronoun reference to: %s", previous_employee_id)
            return ClassifiedIntent(
                intent=LogisticsIntent.EMPLOYEE_SUPPORT,
                confidence=0.95,
                preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.EMPLOYEE_SUPPORT],
                employee_id=previous_employee_id,
                resolved_reference=True,
                target_attribute="employee_followup",
            )

    # 4b. Multi-Turn Shipment & Booking Reference Resolution (Pronoun handling)
    resolved_shipment_id = direct_shipment_id
    resolved_booking_id = direct_booking_id
    resolved_reference = False

    if not resolved_shipment_id and not resolved_booking_id and previous_shipment_id:
        has_pronoun = bool(PRONOUN_FOLLOWUP_PATTERN.search(query))
        tracking_followups = ("where", "status", "location", "arrive", "arrival", "eta", "delivered", "delay", "route", "destination", "origin")
        is_tracking_inquiry = any(w in clean for w in tracking_followups)

        # Standalone conceptual topics (without a pronoun like 'it'/'its'/'this shipment') do not inherit prior IDs
        has_independent_domain = (not has_pronoun) and any(k in clean for k in (
            "bill of lading", "commercial invoice", "customs document", "documents required", "what documents",
            "documentation", "claims", "refund", "forklift", "pharma", "cargo weight", "dimension limit",
            "container spec", "incoterm", "exw", "ddp", "fob", "cif", "bonded warehouse", "open warehouse",
        ))

        if (has_pronoun or is_tracking_inquiry) and not has_independent_domain:
            if previous_shipment_id.upper().startswith("ALC-") or UUID_PATTERN.match(previous_shipment_id):
                resolved_booking_id = previous_shipment_id
            else:
                resolved_shipment_id = previous_shipment_id
            resolved_reference = True
            logger.info("Resolved pronoun reference to previous tracking ref: %s", previous_shipment_id)

    # 5. Routing for Shipment & Enterprise Booking Inquiries
    if resolved_shipment_id or resolved_booking_id:
        kwargs = {
            "shipment_id": resolved_shipment_id,
            "booking_id": resolved_booking_id,
            "resolved_reference": resolved_reference,
            "entities": {"booking_id": resolved_booking_id} if resolved_booking_id else {},
        }
        if re.search(r"\b(when|arrive|arrival|eta|delivery\s+(?:date|status|schedule|update|time)|delivery|delivered|delay|delayed)\b", clean):
            return ClassifiedIntent(
                intent=LogisticsIntent.DELIVERY_UPDATES,
                confidence=0.95,
                preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.DELIVERY_UPDATES],
                target_attribute="eta",
                **kwargs,
            )
        elif re.search(r"\b(dimensions?|weight|cargo|goods|consignment|manifest|recipient|receiver|sender|consignor|consignee|hub|route|origin|destination|contents?|specs?|specification|details?|info|carrier|customer|warehouse|vehicle|weather|customs|product)\b", clean):
            return ClassifiedIntent(
                intent=LogisticsIntent.SHIPMENT_INFO,
                confidence=0.95,
                preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.SHIPMENT_INFO],
                target_attribute="details",
                **kwargs,
            )
        else:
            return ClassifiedIntent(
                intent=LogisticsIntent.SHIPMENT_TRACKING,
                confidence=0.95,
                preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.SHIPMENT_TRACKING],
                target_attribute="location",
                **kwargs,
            )

    # 5b. Ambiguous & Incomplete Query Detection (Requests requiring specific identifiers)
    # Check for tracking without shipment ID
    ambiguous_tracking_patterns = [
        r"^(where\s+(is|s)\s+(my\s+)?(shipment|order|package|parcel|cargo|consignment|delivery))$",
        r"^(where\s+has\s+(it|my\s+shipment|my\s+order)\s+reached)$",
        r"^when\s+(will|is)\s+(it|my\s+shipment|my\s+order|my\s+package)\s+(arrive|delivered|reaching)$",
        r"^track\s+(order|shipment|package|parcel|consignment|delivery)$",
        r"^why\s+is\s+(it|my\s+shipment|my\s+order|the\s+shipment)\s+(late|delayed)$",
        r"^(status\s+check|check\s+status|show\s+(me\s+)?the\s+status|what\s+is\s+the\s+status)$",
        r"^(tell\s+me\s+about\s+(the|my)?\s*(shipment|package|order|delivery))$",
        r"^(what\s+happened\s+to\s+(it|my\s+shipment|my\s+order|the\s+package))$",
        r"^(is\s+(it|my\s+shipment|my\s+order)\s+cleared(\s+yet)?)$",
    ]
    if any(re.search(p, clean) for p in ambiguous_tracking_patterns):
        return ClassifiedIntent(
            intent=LogisticsIntent.CLARIFICATION_REQUIRED,
            confidence=0.98,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.CLARIFICATION_REQUIRED],
            entities={"clarification_type": "missing_shipment_id"},
        )

    # Check for employee lookup without ID
    if re.search(r"^(can\s+you\s+)?(check|look\s*up|view|search)\s+(my\s+)?employee(\s+profile|\s+directory|\s+record)?$", clean) or clean in ("check my employee profile", "look up employee", "employee directory search"):
        return ClassifiedIntent(
            intent=LogisticsIntent.CLARIFICATION_REQUIRED,
            confidence=0.98,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.CLARIFICATION_REQUIRED],
            entities={"clarification_type": "missing_employee_id"},
        )

    # Check for ambiguous fee query
    if clean in ("what is the fee", "how much is the fee", "what are the fees", "check the fee"):
        return ClassifiedIntent(
            intent=LogisticsIntent.CLARIFICATION_REQUIRED,
            confidence=0.95,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.CLARIFICATION_REQUIRED],
            entities={"clarification_type": "ambiguous_fee"},
        )

    # Check for ambiguous hub query
    if clean in ("where is the hub located", "hub location", "where are the hubs", "where is the hub"):
        return ClassifiedIntent(
            intent=LogisticsIntent.CLARIFICATION_REQUIRED,
            confidence=0.95,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.CLARIFICATION_REQUIRED],
            entities={"clarification_type": "ambiguous_hub"},
        )

    # Check for broad delivery query
    if clean in ("tell me about delivery", "how does delivery work", "delivery details"):
        return ClassifiedIntent(
            intent=LogisticsIntent.CLARIFICATION_REQUIRED,
            confidence=0.95,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.CLARIFICATION_REQUIRED],
            entities={"clarification_type": "broad_delivery"},
        )

    # Check for broad company policy query (so it summarizes all company policies instead of one arbitrary PDF/manual)
    if clean in (
        "company policy", "company policies", "what is the company policy",
        "what is company policy", "what are the company policies", "what are your policies",
        "what are your company policies", "show company policy", "list policies", "policies",
    ):
        return ClassifiedIntent(
            intent=LogisticsIntent.CLARIFICATION_REQUIRED,
            confidence=0.96,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.CLARIFICATION_REQUIRED],
            entities={"clarification_type": "broad_policy"},
        )

    # Check for Employee Paid Leave / Time-Off / Overtime HR Policy Queries
    if re.search(
        r"\b(paid\s+leave|annual\s+leave|sick\s+leave|casual\s+leave|parental\s+leave|bereavement\s+leave|"
        r"leave\s+(?:policy|process|procedure|request|balance|entitlement|application|approval|rules?)|"
        r"process\s+(?:of|for)\s+leave|apply\s+for\s+leave|time\s+off|pto|overtime\s+claim)\b",
        clean,
    ):
        return ClassifiedIntent(
            intent=LogisticsIntent.EMPLOYEE_SUPPORT,
            confidence=0.94,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.EMPLOYEE_SUPPORT],
        )

    # 6. Check for Documentation Questions (Give priority to document/form queries)
    if any(k in clean for k in ("document", "documentation", "paperwork", "form", "forms")) or any(k in clean for k in DOCUMENTATION_KEYWORDS):
        return ClassifiedIntent(
            intent=LogisticsIntent.DOCUMENTATION,
            confidence=0.95,
            preferred_source=INTENT_SOURCE_MAP[LogisticsIntent.DOCUMENTATION],
        )

    # 7. Check for Company Policy & Claims
    if any(k in clean for k in POLICY_KEYWORDS) or INCOTERM_WORD_PATTERN.search(clean):
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
    if any(k in clean for k in PROCESS_KEYWORDS) or re.search(r"\b(3pl|wms)\b", clean):
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
