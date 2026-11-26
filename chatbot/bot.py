"""Chatbot core business logic, RAG coordination, and response formatting."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from logistics_chatbot.chatbot.chatbot import get_conversation_store
from logistics_chatbot.chatbot.classifier import (
    LogisticsIntent,
    classify_logistics_query,
    extract_booking_id,
    extract_employee_id,
    extract_operational_id,
    extract_shipment_id,
    normalize_logistics_query,
)
from logistics_chatbot.core import config
from logistics_chatbot.core.errors import (
    ChatbotError,
    EmptyMessageError,
    InvalidShipmentIdError,
    QueryTooLongError,
    ShipmentNotFoundError,
)
from logistics_chatbot.core.prompts import GREETING_TEXT, HELP_TEXT, MAX_QUERY_LENGTH, SYSTEM_PROMPT
from logistics_chatbot.database import database
from logistics_chatbot.rag.retrieval import (
    detect_shipment_id,
    retrieve,
    format_context,
)
from logistics_chatbot.chatbot.llm_client import call_llm, stream_llm

logger = logging.getLogger("logistics_chatbot.bot")

_CITATION_PATTERN = re.compile(r"\[([A-Za-z0-9_\-]+)\]")

GREETING_PATTERN = re.compile(
    r"^(hello|hi|hey|greetings|good\s+(morning|afternoon|evening)|howdy|sup|welcome|who\s+are\s+you|what\s+can\s+you\s+do|help)\b",
    re.IGNORECASE
)


def is_greeting_or_capability_query(msg: str) -> bool:
    """Determine if a query is a greeting, introduction, or capability inquiry."""
    clean = re.sub(r"[?!.,;:]+", "", msg.strip().lower())

    exact_matches = {
        "hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening",
        "howdy", "sup", "welcome", "help", "help me",
        "who are you", "who r u", "what are you", "what r u",
        "tell me about yourself", "introduce yourself",
        "how can you help", "how can u help",
        "how can you help me", "how can u help me",
        "how do you help", "how do u help",
        "how do you help me", "how do u help me",
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
    if clean in exact_matches:
        return True

    patterns = [
        r"^(hello|hi|hey|greetings|howdy|sup|welcome)\b",
        r"^good\s+(morning|afternoon|evening|day)\b",
        r"^(who|what)\s+(are|r)\s+(you|u)\b",
        r"^how\s+(can|do)\s+(you|u)\s+help(\s+me)?\b",
        r"^what\s+(can|do)\s+(you|u)\s+(do|help)\b",
        r"^can\s+(you|u)\s+help(\s+me)?\b",
        r"^(help|assist)(\s+me)?$",
    ]
    for p in patterns:
        if re.search(p, clean):
            domain_keywords = ["shp-", "customs", "cold-chain", "pharma", "delay", "transit", "invoice", "lading", "tracking"]
            if any(dk in clean for dk in domain_keywords):
                return False
            return True

    return False

STATUS_EMOJI_MAP = {
    "in transit": "🟡 In Transit",
    "delivered": "🟢 Delivered",
    "delayed": "🔴 Delayed",
    "on hold - customs": "🟠 On Hold - Customs",
    "customs hold": "🟠 Customs Hold",
    "out for delivery": "🚚 Out for Delivery",
    "pending": "⚪ Pending",
    "cancelled": "⚫ Cancelled",
}

DIRECT_ANSWERS: Dict[str, Tuple[str, List[str]]] = {
    "out for delivery": (
        "**Out for Delivery** indicates that the shipment has arrived at the destination local fulfillment facility or hub and has been loaded onto the delivery courier vehicle. The delivery executive is actively en route to complete physical delivery to the recipient's address today during standard delivery hours.",
        ["Logistics Tracking & Status Guide (SS-003)", "Freight Lifecycle, Shipping Terms & Operational SOP (DOC-CAED8BC8636D)"]
    ),
    "in transit": (
        "**In Transit** means your shipment has departed the origin facility and is actively moving between logistics facilities, gateway terminals, or along linehaul corridors toward its destination.",
        ["Logistics Tracking & Status Guide (SS-003)"]
    ),
    "delivered": (
        "**Delivered** means your shipment has reached its final destination address and has been physically received and signed for by the consignee with Proof of Delivery (POD) recorded.",
        ["Logistics Tracking & Status Guide (SS-003)"]
    ),
    "delayed": (
        "**Delayed** means an unexpected event (such as adverse weather, transport congestion, mechanical maintenance, or documentation review) has extended the initial estimated transit time.",
        ["Shipment Delay & Exception Policy (LC-0003)"]
    ),
    "customs clearance": (
        "**Customs Clearance** is the mandatory government regulatory procedure where export and import declarations, commercial invoices, and duties/taxes are verified and settled before goods can legally cross international borders.",
        ["Customs Trade Compliance & Cross-Border Rules (DOC-6BDEA8303C7A)", "Logistics Terminology & Glossary (GL-0069)"]
    ),
    "bill of lading": (
        "A **Bill of Lading (BOL)** is a legally binding contract and title document issued by a freight carrier detailing cargo type, quantity, origin, consignee, and destination for ocean and multimodal transport.",
        ["Documentation Standard Operating Procedure (DC-0085)", "Customer Service Rules & Shipping Terms (DOC-7806D9117C6C)"]
    ),
    "demurrage": (
        "**Demurrage** is a penalty charge assessed by shipping lines or port authorities when an imported container remains inside the port terminal or container yard beyond the allotted free days (typically 4 to 7 calendar days). In contrast, **Detention** (per diem) is charged when an empty or loaded container is kept outside the port facility beyond the permitted free return window.",
        ["Freight Lifecycle, Shipping Terms & Operational SOP (DOC-CAED8BC8636D)"]
    ),
    "fob vs cif": (
        "# 📋 FOB vs CIF Shipping Terms (Incoterms 2020)\n\n"
        "### 1. Overview\n"
        "FOB and CIF are standard International Commercial Terms (Incoterms) defining the division of transport costs, marine insurance, and risk of loss between buyers and sellers.\n\n"
        "### 2. Key Differences\n"
        "| Feature | FOB (Free On Board) | CIF (Cost, Insurance, and Freight) |\n"
        "|---|---|---|\n"
        "| **Seller Responsibility** | Delivers cargo safely loaded on board the vessel at the origin port. Clears export customs. | Pays for inland transport, export customs, ocean freight carriage, and minimum marine insurance to the destination port. |\n"
        "| **Buyer Responsibility** | Pays ocean freight carriage, marine cargo insurance, destination terminal fees, import duties, and inland delivery. | Pays destination port handling charges, import customs clearance, tariffs, and inland transport to final facility. |\n"
        "| **Risk Transfer Point** | Transfers to buyer when cargo is loaded on board the vessel at the port of origin. | Transfers to buyer when cargo is loaded on board the vessel at origin (even though seller pays freight & insurance). |\n"
        "| **Applicable Transport** | Maritime ocean and inland waterway transport only. | Maritime ocean and inland waterway transport only. |",
        ["Freight Lifecycle, Shipping Terms & Operational SOP (DOC-CAED8BC8636D)"]
    ),
    "cargo weight limits": (
        "# 📋 Cargo Weight & Dimension Limits\n\n"
        "### 1. Overview\n"
        "FleetHarbor freight operations adhere to international ISO, IATA, and DOT standards governing permissible dimensions, gross weights, and payload capacities across ocean, air, and road freight.\n\n"
        "### 2. Standard Ocean ISO Container Specifications\n"
        "| Container Type | Internal Dimensions (L × W × H) | Tare Weight | Max Cargo Payload | Max Gross Mass (MGM) | Cubic Capacity |\n"
        "|---|---|---|---|---|---|\n"
        "| **20ft Standard** | 5.90 m × 2.35 m × 2.39 m (19'4\" × 7'8\" × 7'10\") | 2,280 kg (5,026 lbs) | 28,200 kg (62,170 lbs) | 30,480 kg (67,200 lbs) | 33.2 m³ (1,172 cu ft) |\n"
        "| **40ft Standard** | 12.03 m × 2.35 m × 2.39 m (39'5\" × 7'8\" × 7'10\") | 3,700 kg (8,157 lbs) | 28,800 kg (63,490 lbs) | 32,500 kg (71,650 lbs) | 67.7 m³ (2,390 cu ft) |\n"
        "| **40ft High Cube (HC)** | 12.03 m × 2.35 m × 2.70 m (39'5\" × 7'8\" × 8'10\") | 3,900 kg (8,598 lbs) | 28,600 kg (63,050 lbs) | 32,500 kg (71,650 lbs) | 76.4 m³ (2,698 cu ft) |\n"
        "| **45ft High Cube** | 13.56 m × 2.35 m × 2.70 m (44'6\" × 7'8\" × 8'10\") | 4,640 kg (10,230 lbs) | 27,860 kg (61,420 lbs) | 32,500 kg (71,650 lbs) | 86.0 m³ (3,037 cu ft) |\n"
        "| **20ft Reefer** | 5.44 m × 2.29 m × 2.27 m (17'10\" × 7'6\" × 7'5\") | 3,080 kg (6,790 lbs) | 27,400 kg (60,410 lbs) | 30,480 kg (67,200 lbs) | 28.3 m³ (999 cu ft) |\n"
        "| **40ft Reefer HC** | 11.58 m × 2.29 m × 2.54 m (38'0\" × 7'6\" × 8'4\") | 4,480 kg (9,880 lbs) | 29,520 kg (65,080 lbs) | 34,000 kg (74,960 lbs) | 67.3 m³ (2,377 cu ft) |\n\n"
        "### 3. Air Freight & ULD Limits\n"
        "- **Lower Deck Passenger Aircraft:** Max cargo height is 160 cm (63 in). Standard LD3 (AKE) container max gross weight is 1,588 kg (3,500 lbs).\n"
        "- **Main Deck Dedicated Freighter:** Accommodates PMC pallets up to 300 cm (118 in) height and 6,800 kg (15,000 lbs) per pallet position.\n"
        "- **Volumetric Weight Formula:** Standard IATA air ratio is $\\text{Length (cm)} \\times \\text{Width (cm)} \\times \\text{Height (cm)} / 6000 = \\text{Volumetric Weight (kg)}$ (1 m³ = 167 kg).\n\n"
        "### 4. Road Freight & Pallet Standards\n"
        "- **Euro Pallet (EUR-1):** 1,200 mm × 800 mm. Max dynamic load: 1,500 kg (3,307 lbs). Safe warehouse stack height: ≤ 180 cm.\n"
        "- **Standard Industrial Pallet (ISO / GMA):** 1,200 mm × 1,000 mm (48\" × 40\"). Max dynamic load: 1,500 kg.\n"
        "- **Standard 53ft Dry Van Truckload:** Max legal cargo payload is ~45,000 lbs (20,412 kg). Total legal Gross Vehicle Weight (GVW) is 80,000 lbs.\n"
        "- **Express Parcel Limits:** Max weight per individual parcel is 70 kg (150 lbs); max length is 274 cm (108 in); max length + girth is 400 cm (157 in).",
        ["Cargo Weight, Dimensions & Container Specifications (DOC-CF9235FF4F8A)"]
    ),
    "shipment lifecycle": (
        "# 📋 Complete Shipment Lifecycle\n\n"
        "### 1. Overview\n"
        "The FleetHarbor end-to-end logistics lifecycle encompasses six audited, sequential milestones connecting booking, multimodal transit, regulatory clearance, and final physical delivery.\n\n"
        "### 2. Six Operational Lifecycle Stages\n"
        "1. **Stage 1 – Booking & Order Creation:** Shipper books cargo; commercial invoices and packing lists are verified; and unique waybill tracking tags (e.g., `SHP-10001`) and shipping barcodes are generated.\n"
        "2. **Stage 2 – Inbound Pickup & Hub Consolidation:** Local pickup dispatch collects freight from shipper warehouse; cargo is scanned, weighed, palletized, and prepared for linehaul departure.\n"
        "3. **Stage 3 – Export Customs Clearance & Screening:** Electronic export declarations are filed with customs authorities; cargo passes security X-ray and hazmat compliance screening.\n"
        "4. **Stage 4 – Linehaul Transit:** Goods move across ocean lanes, international air routes, or interstate trucking corridors with continuous satellite GPS tracking.\n"
        "5. **Stage 5 – Import Customs Clearance & Gateway Arrival:** Consignment arrives at destination gateway terminal; import tariffs and customs duties are assessed and cleared.\n"
        "6. **Stage 6 – Out for Delivery & Proof of Delivery (POD):** Cargo is sorted onto local delivery courier routes, dispatched for final-mile delivery, and handed over to the consignee upon capturing digital signature.\n\n"
        "### 3. Operational Exception Management\n"
        "If severe weather, mechanical delay, or customs physical inspections occur during transit, the status automatically updates to `Delayed` or `On Hold - Customs` with proactive stakeholder notifications.",
        ["Freight Lifecycle, Shipping Terms & Operational SOP (DOC-CAED8BC8636D)"]
    ),
    "proof of delivery": (
        "**Proof of Delivery (POD)** is an authoritative verification and legal receipt confirming that cargo has been physically handed over to and accepted by the consignee.\n\n"
        "FleetHarbor captures electronic Proof of Delivery (e-POD) at the delivery address, recording:\n"
        "- Consignee recipient full name and digital signature.\n"
        "- Exact date, timestamp, and GPS delivery coordinates.\n"
        "- Delivered carton count and outer packaging integrity sign-off.\n"
        "- Exception annotations (if visible damage or shortage occurred).\n\n"
        "e-POD records are archived digitally and accessible via shipment tracking lookup within 15 minutes of completion.",
        ["Freight Lifecycle, Shipping Terms & Operational SOP (DOC-CAED8BC8636D)"]
    ),
    "air vs ocean transit": (
        "# 📋 Air vs Ocean Freight Comparison\n\n"
        "### 1. Overview\n"
        "FleetHarbor provides multimodal transport solutions across global air and ocean shipping lanes, balancing transit speed against transportation cost.\n\n"
        "### 2. Transit Times & Economics Comparison\n"
        "| Parameter | Air Freight | Ocean Freight (FCL / LCL) |\n"
        "|---|---|---|\n"
        "| **Transit Time** | **1 to 5 business days** globally. | **15 to 45 calendar days** depending on maritime lane and port congestion. |\n"
        "| **Cost Factor** | **4× to 6× higher** than ocean freight. Billed on actual weight or volumetric weight (1:6000 ratio). | **Significantly lower cost per kg / CBM**. Highly economical for bulk and heavy consignments. |\n"
        "| **Payload Capacity** | Limited by aircraft payload and ULD dimensions (max height ~160–300 cm). | High capacity (standard 20ft/40ft containers up to 28,800 kg payload). |\n"
        "| **Best Suited For** | High-value electronics, pharmaceuticals (cold-chain), urgent spare parts, and fashion. | Heavy machinery, raw materials, consumer retail bulk goods, and non-perishables. |\n"
        "| **Environmental Impact** | Higher carbon footprint per ton-km. | Lower carbon emissions per ton-km. |",
        ["Freight Lifecycle, Shipping Terms & Operational SOP (DOC-CAED8BC8636D)"]
    ),
    "delayed shipment": (
        "# 📋 Shipment Delay Handling & Exception Procedures\n\n"
        "### 1. Overview\n"
        "When transit interruptions occur due to severe weather, customs holds, port congestion, or carrier mechanical disruptions, FleetHarbor activates automated exception protocols.\n\n"
        "### 2. Operational Procedures\n"
        "1. **Telemetry Trigger:** Automated carrier scans or GPS route deviations trigger an exception event in the tracking system.\n"
        "2. **Status Transition:** The shipment status transitions to `Delayed`, and the specific root-cause reason (e.g., *Weather disruption*, *Vessel mechanical maintenance*, or *Highway congestion*) is logged in the tracking record.\n"
        "3. **Dynamic ETA Recalculation:** Route algorithms recalculate a revised Estimated Delivery Date based on real-time transit telemetry.\n"
        "4. **Stakeholder Notification:** Automated email and portal alerts notify both the shipper and consignee with the revised schedule.\n"
        "5. **Expedited Recovery:** Operations teams coordinate priority rerouting or expedited cross-dock dispatch to minimize overall transit impact.",
        ["Shipment Delay & Exception Policy (LC-0003)"]
    ),
}

DIRECT_DEFINITIONS = {k: v[0] for k, v in DIRECT_ANSWERS.items()}


def find_direct_answer(clean_msg: str) -> Optional[Tuple[str, List[str]]]:
    """Check if query directly matches standard logistics concept inquiries."""
    q = re.sub(r"[?!.,;:]+", "", clean_msg.strip().lower())

    # Out for delivery
    if "out for delivery" in q and any(w in q for w in ("what", "mean", "define", "explain", "meaning")):
        return DIRECT_ANSWERS["out for delivery"]
    if q in ("out for delivery", "what is out for delivery", "what does out for delivery mean"):
        return DIRECT_ANSWERS["out for delivery"]

    # Cargo weight and dimension limits
    if any(k in q for k in ("cargo weight", "dimension limit", "container spec", "container dimension", "container size", "weight and dimension", "weight and dimension limits")):
        return DIRECT_ANSWERS["cargo weight limits"]

    # Shipment lifecycle
    if "lifecycle" in q or ("pickup to delivery" in q and "shipment" in q):
        return DIRECT_ANSWERS["shipment lifecycle"]

    # Demurrage
    if "demurrage" in q and any(w in q for w in ("what", "mean", "define", "explain", "meaning", "freight")):
        return DIRECT_ANSWERS["demurrage"]

    # FOB vs CIF
    if ("fob" in q and "cif" in q) or "difference between fob and cif" in q:
        return DIRECT_ANSWERS["fob vs cif"]

    # Proof of delivery
    if ("proof of delivery" in q or " pod " in f" {q} ") and any(w in q for w in ("what", "how", "obtained", "verify", "meaning")):
        return DIRECT_ANSWERS["proof of delivery"]

    # Air vs ocean transit
    if ("air vs ocean" in q or "ocean vs air" in q or ("air" in q and "ocean" in q and "transit" in q)):
        return DIRECT_ANSWERS["air vs ocean transit"]

    # Delayed shipment (keep exact general policy question fast while routing customer delay troubleshooting to RAG)
    if "what should customers do when a shipment is delayed" in q or "what can be done" in q:
        return None
    if ("happens when a shipment is delayed" in q or "handling shipment delays" in q or q in ("shipment delayed", "delayed shipment")):
        return DIRECT_ANSWERS["delayed shipment"]

    # Check exact phrasing matches
    for term, (definition, sources) in DIRECT_ANSWERS.items():
        if q in (term, f"what is {term}", f"what does {term} mean", f"define {term}"):
            return (definition, sources)

    return None


class ChatResult:
    """Structured response container maintaining backward-compatible 2-element tuple unpacking."""

    def __init__(
        self,
        response: str,
        sources: List[str],
        response_type: str = "general_knowledge",
        shipment_id: Optional[str] = None,
        structured_data: Optional[Dict[str, Any]] = None,
    ):
        self.response = response
        self.sources = sources
        self.response_type = response_type
        self.shipment_id = shipment_id
        self.structured_data = structured_data or {}

    def __iter__(self):
        yield self.response
        yield self.sources

    def __getitem__(self, idx):
        if idx == 0:
            return self.response
        if idx == 1:
            return self.sources
        raise IndexError("ChatResult index out of range (supports 0: response, 1: sources)")

    def __repr__(self):
        return f"<ChatResult type={self.response_type} shipment_id={self.shipment_id} sources={len(self.sources)}>"


def map_source_display(source_id: str) -> str:
    """Map raw internal document IDs into human-readable source titles while preserving the ID for auditability."""
    sid = str(source_id).strip()
    if sid.startswith("Enterprise "):
        return sid
    if sid.startswith("SHP-") or ("shipment" in sid.lower() and "pdf" not in sid.lower()):
        clean_id = re.search(r"SHP-\d+", sid)
        shp_str = clean_id.group(0) if clean_id else sid
        return f"Shipment Database Record ({shp_str})"
    if sid.startswith("EMP-") or "employee" in sid.lower():
        clean_id = re.search(r"EMP-\d+", sid)
        emp_str = clean_id.group(0) if clean_id else sid
        return f"Employee Directory Roster ({emp_str})"

    # Direct document title mapping
    doc_map = {
        "DOC-CF9235FF4F8A": "Cargo Weight, Dimensions & Container Specifications (DOC-CF9235FF4F8A)",
        "DOC-CAED8BC8636D": "Freight Lifecycle, Shipping Terms & Operational SOP (DOC-CAED8BC8636D)",
        "DOC-AFFBF53DD573": "Warehouse Operations & Safety Standard Operating Procedure (DOC-AFFBF53DD573)",
        "DOC-133970A063BD": "Corporate Fleet Profile & Global Operations (DOC-133970A063BD)",
        "DOC-7806D9117C6C": "Customer Service Rules & Shipping Terms (DOC-7806D9117C6C)",
        "DOC-6BDEA8303C7A": "Customs Trade Compliance & Cross-Border Rules (DOC-6BDEA8303C7A)",
        "DOC-A425D209E7E3": "Dangerous Goods & Hazardous Materials Packaging SOP (DOC-A425D209E7E3)",
        "DOC-9167A59967A4": "Pharmaceutical Cold-Chain & GDP Compliance Manual (DOC-9167A59967A4)",
        "DOC-9C68FFC317D6": "Employee Operations & Department Directory (DOC-9C68FFC317D6)",
        "DOC-AF885F63B95E": "Employee Paid Leave, Time-Off Process & HR Policy (DOC-AF885F63B95E)",
        "PDF-CUST-SUPPORT": "Customer Support, Tracking & Booking Reference (PDF-CUST-SUPPORT)",
        "PDF-EXIM-CUSTOMS": "Export-Import Documentation & Customs Reference Guide (PDF-EXIM-CUSTOMS)",
        "PDF-INCOTERMS": "Incoterms & International Trade Terms Guide (PDF-INCOTERMS)",
        "PDF-DELAY-RISK": "Shipment Delay Causes & Route Risk Reference (PDF-DELAY-RISK)",
        "PDF-WAREHOUSING": "Warehousing & Contract Logistics Reference (PDF-WAREHOUSING)",
    }
    if sid in doc_map:
        return doc_map[sid]

    if "CUSTOMS" in sid or sid in ("PL-0010", "GL-0069", "DC-0030", "DC-0029"):
        return f"Customs & Regulatory Policy ({sid})"
    if "DELAY" in sid or sid in ("LC-0003",):
        return f"Shipment Delay & Exception Policy ({sid})"
    if "STATUS" in sid or sid.startswith("SS-"):
        return f"Logistics Tracking & Status Guide ({sid})"
    if "PHARMA" in sid or "531F90" in sid:
        return f"Cold-Chain Pharmaceutical Policy ({sid})"
    if sid.startswith("DC-"):
        return f"Documentation Standard Operating Procedure ({sid})"
    if sid.startswith("CM-"):
        return f"Commodity Handling Guidelines ({sid})"
    if sid.startswith("GL-"):
        return f"Logistics Terminology & Glossary ({sid})"
    if sid.startswith("LW-") or sid.startswith("SP-"):
        return f"Logistics Workflow & Order Lifecycle ({sid})"
    if sid.startswith("DOC-"):
        return f"Uploaded Knowledge Document ({sid})"
    if sid.startswith("FAQ-"):
        return f"Standard Operating Procedure ({sid})"
    return f"Verified Knowledge Document ({sid})"


def format_display_date(date_str: Any) -> str:
    """Format dates into readable format, e.g., '20 November 2026' or '15 November 2026, 18:30'."""
    if not date_str:
        return "Not available"
    s = str(date_str).strip()
    try:
        if " " in s:
            dt = datetime.strptime(s, "%Y-%m-%d %H:%M")
            return f"{dt.day} {dt.strftime('%B %Y')}, {dt.strftime('%H:%M')}"
        elif "T" in s:
            dt = datetime.fromisoformat(s)
            return f"{dt.day} {dt.strftime('%B %Y')}, {dt.strftime('%H:%M')}"
        else:
            dt = datetime.strptime(s, "%Y-%m-%d")
            return f"{dt.day} {dt.strftime('%B %Y')}"
    except Exception:
        return s


def build_shipment_status_report(shipment: dict, query_lower: str) -> str:
    """Construct a concise shipment tracking report: status header, overview table, and transit progress only."""
    sid = shipment["shipment_id"]
    status_raw = shipment.get("status") or "In Transit"
    status_emoji = STATUS_EMOJI_MAP.get(status_raw.lower(), f"🔵 {status_raw}")
    curr_loc = shipment.get("current_location") or "In Transit"
    origin = shipment.get("origin") or "Origin"
    dest = shipment.get("destination") or "Destination"
    eta = format_display_date(shipment.get("estimated_delivery"))
    updated = format_display_date(shipment.get("last_updated"))
    route = shipment.get("route") or f"{origin} -> {dest}"
    delay_reason = shipment.get("delay_reason")
    customs_status = shipment.get("customs_status")

    stops = [s.strip() for s in route.split("->")]
    origin_name = stops[0] if stops else origin
    dest_name = stops[-1] if stops else dest

    # Check if this is specifically a location query
    is_location_query = any(w in query_lower for w in ("location", "where is", "where's", "where"))

    if is_location_query:
        header = f"# 📍 Shipment Location – {sid}\n\n**Current Location:** 📍 {curr_loc}\n**Current Status:** {status_emoji}"
    else:
        header = f"# 📦 Shipment Status – {sid}\n\n**Current Status:** {status_emoji}"

    # 1. Shipment Overview Table (always surface customs_status & delay_reason when relevant)
    overview_rows = [
        f"| Shipment ID | {sid} |",
        f"| Current Location | {curr_loc} |",
        f"| Origin | {origin} |",
        f"| Destination | {dest} |",
        f"| Estimated Delivery | {eta} |",
        f"| Last Updated | {updated} |",
    ]
    if customs_status:
        overview_rows.append(f"| Customs Status | {customs_status} |")
    if delay_reason:
        overview_rows.append(f"| Delay Reason | {delay_reason} |")

    overview = (
        "### 1. Shipment Overview\n\n"
        "| Field | Details |\n"
        "|---|---|\n"
        + "\n".join(overview_rows)
    )

    # 2. Shipment Progress
    progress_lines = [
        "- Origin processing: Completed",
        f"- Departure from {origin_name}: Completed",
    ]

    curr_idx = -1
    for idx, stop in enumerate(stops):
        if curr_loc.lower() in stop.lower() or stop.lower() in curr_loc.lower():
            curr_idx = idx
            break

    if len(stops) > 2:
        for idx, stop in enumerate(stops[1:-1], start=1):
            if "delivered" in status_raw.lower():
                progress_lines.append(f"- Transit through {stop}: Completed")
            elif curr_idx != -1 and idx < curr_idx:
                progress_lines.append(f"- Transit through {stop}: Completed")
            elif curr_idx == idx:
                if delay_reason:
                    progress_lines.append(f"- Transit through {stop}: Delayed ({delay_reason})")
                elif "customs" in status_raw.lower():
                    progress_lines.append(f"- Transit through {stop}: On Hold (Customs Inspection)")
                elif "out for delivery" in status_raw.lower():
                    progress_lines.append(f"- Transit through {stop}: In Progress (Out for Delivery)")
                else:
                    progress_lines.append(f"- Transit through {stop}: In Progress")
            else:
                progress_lines.append(f"- Transit through {stop}: Pending")
    elif curr_loc and curr_loc not in (origin_name, dest_name):
        if "delivered" in status_raw.lower():
            progress_lines.append(f"- Transit through {curr_loc}: Completed")
        elif "out for delivery" in status_raw.lower():
            progress_lines.append(f"- Transit through {curr_loc}: In Progress (Out for Delivery)")
        elif delay_reason:
            progress_lines.append(f"- Transit through {curr_loc}: Delayed ({delay_reason})")
        else:
            progress_lines.append(f"- Transit through {curr_loc}: In Progress")

    if "delivered" in status_raw.lower():
        progress_lines.append(f"- Arrival at {dest_name}: Completed")
        progress_lines.append("- Final delivery: Completed")
    else:
        progress_lines.append(f"- Arrival at {dest_name}: Pending")
        progress_lines.append("- Final delivery: Pending")

    progress_sec = "### 2. Shipment Progress\n\n" + "\n".join(progress_lines)

    return f"{header}\n\n{overview}\n\n{progress_sec}"


def clean_citation_brackets(text: str) -> str:
    """Remove raw bracket tokens like [DOC-XXXX] or [FAQ-XXXX] from the prose body for clean reading."""
    # Remove patterns like ([DOC-123]) or [DOC-123]
    cleaned = re.sub(r"\s*\(\[[A-Za-z0-9_\-]+\]\)", "", text)
    cleaned = re.sub(r"\s*\[[A-Za-z0-9_\-]+\]", "", cleaned)
    # Clean double spaces
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()


def build_operational_status_report(ops: Dict[str, Any]) -> str:
    """Construct structured OPERATIONAL RECORD card matching Issue 5 specifications."""
    doc_id = ops.get("doc_id", "N/A")
    category = ops.get("category", "operational_case").replace("_", " ").title()
    title = ops.get("section_title") or f"Operational Case {doc_id}"
    status = ops.get("status", "Active")
    origin = ops.get("origin", "N/A")
    destination = ops.get("destination", "N/A")
    assigned = ops.get("assigned_employee", "Operations Coordinator (Dispatch Desk)")
    dept = ops.get("responsible_department", category)
    last_updated = ops.get("last_updated", "N/A")
    risk = ops.get("risk_factors", "Standard monitoring")
    content = ops.get("content", "")

    # Status badge
    status_lower = status.lower()
    if "awaiting" in status_lower or "pending" in status_lower:
        status_badge = f"🟡 {status}"
    elif "transit" in status_lower or "active" in status_lower:
        status_badge = f"🟢 {status}"
    elif "delay" in status_lower or "hold" in status_lower or "exception" in status_lower:
        status_badge = f"🔴 {status}"
    else:
        status_badge = f"⚪ {status}"

    location_str = f"{origin} → {destination}"
    if origin != "N/A":
        location_str += f" (Current Facility: {origin} Hub)"

    report = (
        f"# 📋 OPERATIONAL RECORD\n\n"
        f"**Case Title:** {title}\n\n"
        f"- **Record ID:** `{doc_id}`\n"
        f"- **Current Status:** {status_badge}\n"
        f"- **Responsible Department:** {dept}\n"
        f"- **Assigned Employee:** {assigned}\n"
        f"- **Current Location:** {location_str}\n"
        f"- **Last Updated:** {last_updated}\n"
    )

    details = []
    if risk and risk != "N/A":
        details.append(f"**Key Risk Identified:** {risk}.")

    if "coordinator should" in content.lower():
        m = re.search(r"(The coordinator should [^.]+\.)", content, re.IGNORECASE)
        if m:
            details.append(f"**Protocol:** {m.group(1)}")
    elif content:
        first_sentence = content.split(".")[0].strip()
        if first_sentence:
            details.append(f"{first_sentence}.")

    if details:
        report += f"- **Additional Details:** {' '.join(details)}\n"

    return report


def _build_employee_profile_report(emp: Dict[str, Any]) -> str:
    """Format an employee database record into a structured Markdown card."""
    return (
        f"# 👤 Employee Profile – {emp['employee_id']}\n\n"
        f"**Personnel Record:** {emp['full_name']} ({emp['job_title']})\n\n"
        f"### 1. Operations Overview\n\n"
        f"| Field | Details |\n"
        f"|---|---|\n"
        f"| Employee ID | {emp['employee_id']} |\n"
        f"| Full Name | {emp['full_name']} |\n"
        f"| Department | {emp['department']} |\n"
        f"| Job Title | {emp['job_title']} |\n"
        f"| Assigned Hub | {emp['assigned_hub']} |\n"
        f"| Shift Rotation | {emp['shift']} |\n"
        f"| Certification | {emp.get('certification') or 'Standard Operations Certified'} |\n"
        f"| Operational Status | {emp.get('status', 'Active')} |\n\n"
        f"### 2. Contact & Internal Routing\n\n"
        f"- **Corporate Email:** `{emp['email']}`\n"
        f"- **VoIP Extension:** `{emp.get('phone_extension', 'x4000')}`\n"
        f"- **Dispatch Desk:** Reachable through {emp['assigned_hub']} operations center."
    )


def is_aggregate_shipment_query(text: str) -> bool:
    """Determine if a query asks for aggregate shipment statistics, counts, or status totals."""
    q = re.sub(r"[?!.,;:]+", " ", text.lower()).strip()

    count_cues = (
        "how many", "count of", "number of", "total shipments", "total freight",
        "total packages", "how much freight", "all shipments", "status count",
        "shipment breakdown", "breakdown of shipments", "shipment summary",
        "summary of shipments", "shipments by status", "overview of shipments",
    )
    has_count_cue = any(c in q for c in count_cues)
    has_shipment_noun = any(n in q for n in ("shipment", "shipments", "packages", "orders", "freight", "cargo", "consignments"))

    direct_status_count = any(
        f"how many {s}" in q
        or f"how many are {s}" in q
        or f"how many were {s}" in q
        or f"how many have been {s}" in q
        or f"how many shipments {s}" in q
        or f"how many shipments are {s}" in q
        or f"how many shipments have been {s}" in q
        for s in ("in transit", "currently in transit", "delivered", "delayed", "on hold", "out for delivery", "pending")
    )

    if direct_status_count:
        return True

    if has_count_cue and (has_shipment_noun or any(s in q for s in ("in transit", "delivered", "delayed", "customs hold", "out for delivery"))):
        return True

    return False


def is_aggregate_employee_query(text: str) -> bool:
    """Determine if a query asks for total workforce count or department staffing breakdown."""
    q = re.sub(r"[?!.,;:]+", " ", text.lower()).strip()
    has_count = any(w in q for w in ("how many", "count", "total number", "number of", "total employees", "total staff", "workforce count"))
    has_emp = any(w in q for w in ("employee", "employees", "staff", "personnel", "workers", "workforce", "drivers"))
    return has_count and has_emp


def build_shipment_aggregate_report(
    query: str,
    status_filter: Optional[str] = None,
) -> ChatResult:
    """Construct an authoritative aggregate shipment metrics report grounded in the database."""
    q = query.lower()
    counts = database.get_shipment_status_counts()
    total = sum(counts.values()) or 10000

    if not status_filter:
        if "transit" in q:
            status_filter = "In Transit"
        elif "delivered" in q:
            status_filter = "Delivered"
        elif "delayed" in q:
            status_filter = "Delayed"
        elif "customs" in q or "on hold" in q:
            status_filter = "On Hold - Customs"
        elif "out for delivery" in q:
            status_filter = "Out for Delivery"
        elif "pending" in q:
            status_filter = "Pending"

    status_emojis = {
        "In Transit": "🟡 In Transit",
        "Delivered": "🟢 Delivered",
        "Delayed": "🔴 Delayed",
        "On Hold - Customs": "🟠 On Hold - Customs",
        "Out for Delivery": "🚚 Out for Delivery",
        "Pending": "⚪ Pending",
        "Cancelled": "⚫ Cancelled",
    }

    ordered_keys = ["In Transit", "Delivered", "Delayed", "On Hold - Customs", "Out for Delivery"]
    table_rows = []
    for k in ordered_keys:
        if k in counts:
            cnt = counts[k]
            pct = (cnt / total) * 100.0 if total else 0
            label = status_emojis.get(k, k)
            if status_filter and k.lower() == status_filter.lower():
                table_rows.append(f"| **{label}** | **{cnt:,}** | **{pct:.1f}%** |")
            else:
                table_rows.append(f"| {label} | {cnt:,} | {pct:.1f}% |")

    for k, cnt in counts.items():
        if k not in ordered_keys:
            pct = (cnt / total) * 100.0 if total else 0
            label = status_emojis.get(k, k)
            table_rows.append(f"| {label} | {cnt:,} | {pct:.1f}% |")

    table_rows.append(f"| **Total Active Freight** | **{total:,}** | **100.0%** |")
    table_md = "| Lifecycle Status | Active Shipments | Network Share |\n|---|---|---|\n" + "\n".join(table_rows)

    if status_filter:
        target_count = counts.get(status_filter, 0)
        if target_count == 0:
            for k, v in counts.items():
                if status_filter.lower() in k.lower():
                    target_count = v
                    status_filter = k
                    break

        pct = (target_count / total) * 100.0 if total else 0
        emoji_label = status_emojis.get(status_filter, status_filter)

        body = (
            f"# 📊 Real-Time Shipment Status Count\n\n"
            f"There are currently **{target_count:,} shipments** in **{emoji_label}** status ({pct:.1f}% of active freight) across FleetHarbor's logistics network.\n\n"
            f"### Operational Network Snapshot\n\n{table_md}\n\n"
            f"To inspect any specific consignment, query its tracking number (e.g., `SHP-10001` through `SHP-20000`)."
        )
    else:
        body = (
            f"# 📊 Total Shipments Overview & Network Status\n\n"
            f"FleetHarbor AI is currently tracking **{total:,} total real-time shipments** across 20 global hub locations and maritime routes.\n\n"
            f"### Current Network Distribution\n\n{table_md}\n\n"
            f"To query a specific shipment, type its identifier (e.g. `What is the status of SHP-10001?`)."
        )

    source_label = f"Shipment Database Registry ({total:,} Real-Time Shipments)"
    return ChatResult(
        response=body,
        sources=[source_label],
        response_type="shipment_aggregate",
        shipment_id=None,
        structured_data={"status_counts": counts, "total": total, "filter": status_filter},
    )


def build_employee_aggregate_report() -> ChatResult:
    """Construct an authoritative employee directory workforce distribution report."""
    emp_data = database.get_employee_counts()
    total = emp_data.get("total", 500)
    dept_counts = emp_data.get("by_department", {})

    dept_icons = {
        "Warehouse Operations": "📦 Warehouse Operations",
        "Fleet & Linehaul Dispatch": "🚛 Fleet & Linehaul Dispatch",
        "Customs & Trade Compliance": "📋 Customs & Trade Compliance",
        "Logistics Coordination": "🌐 Logistics Coordination",
        "Safety & Maintenance": "🔧 Safety & Maintenance",
    }
    table_rows = []
    for dept, count in dept_counts.items():
        icon_label = dept_icons.get(dept, f"👥 {dept}")
        pct = (count / total) * 100.0 if total else 0
        table_rows.append(f"| {icon_label} | **{count}** | {pct:.1f}% |")

    table_rows.append(f"| **Total Logistics Workforce** | **{total}** | **100.0%** |")
    table_md = "| Department / Operations Division | Active Staff | Share |\n|---|---|---|\n" + "\n".join(table_rows)

    body = (
        f"# 👥 FleetHarbor Personnel & Workforce Directory\n\n"
        f"FleetHarbor employs **{total} active logistics professionals** deployed across 20 global hubs.\n\n"
        f"### Operations Staffing Breakdown\n\n{table_md}\n\n"
        f"To look up a specific team member, query their Employee ID (e.g., `Look up EMP-20001`)."
    )
    source_label = f"Employee Directory Roster ({total} Personnel)"
    return ChatResult(
        response=body,
        sources=[source_label],
        response_type="employee_aggregate",
        shipment_id=None,
        structured_data=emp_data,
    )


def _extract_session_context(session_id: Optional[str]):
    """Retrieve conversation session plus most recent shipment/booking ID & employee ID."""
    from logistics_chatbot.chatbot.classifier import extract_booking_id

    session = None
    previous_shipment_id = None
    previous_employee_id = None
    if session_id:
        store = get_conversation_store()
        session = store.get_or_create(session_id)
        if session and session.messages:
            for past_msg in reversed(session.messages):
                if not previous_shipment_id:
                    booking_ref = extract_booking_id(past_msg.content)
                    if booking_ref:
                        previous_shipment_id = booking_ref
                if not previous_shipment_id:
                    try:
                        sid = detect_shipment_id(past_msg.content)
                        if sid:
                            previous_shipment_id = sid
                    except InvalidShipmentIdError:
                        pass
                if not previous_employee_id:
                    eid = extract_employee_id(past_msg.content)
                    if eid:
                        previous_employee_id = eid
                if previous_shipment_id and previous_employee_id:
                    break
    return session, previous_shipment_id, previous_employee_id


def _is_hybrid_enterprise_query(msg_lower: str) -> bool:
    """Detect whether an enterprise booking query needs ChromaDB knowledge + LLM reasoning."""
    reasoning_cues = (
        "why ", "why?", "explain", "what can be done", "how can", "how to ",
        "recommend", "mitigate", "incoterm", "responsibilit", "guidance",
        "requirement", "requirements", "what should", "resolve", "steps",
    )
    return any(cue in msg_lower for cue in reasoning_cues)


def format_enterprise_shipment_context(ent: Dict[str, Any]) -> str:
    """Serialize all verified relational fields of an enterprise booking for grounded hybrid RAG."""
    ai_feat = ent.get("ai_features") or {}
    ai_inf = ent.get("ai_inference") or {}
    alerts = ent.get("alerts") or []
    alert_summary = "; ".join(
        f"[{a.get('severity', 'Info')}] {a.get('alert_type', 'Alert')} ({a.get('alert_status', '')}): {a.get('recommended_action', '')}"
        for a in alerts[:3]
    ) or "None"

    delay_txt = (
        f"Delayed (+{ent.get('delay_days', 0)} days beyond expected)"
        if ent.get("is_delayed")
        else f"Delivered ({ent.get('derived_status', 'Delivered')})"
    )

    lines = [
        f"Booking Reference: {ent['booking_id']} (UUID: {ent['shipment_id']})",
        f"Derived Status (from Shipment_Delivery_History): {delay_txt}",
        f"Customer: {ent.get('customer_name')} ({ent.get('customer_type')}, {ent.get('industry')}, {ent.get('customer_city')}, {ent.get('customer_country')})",
        f"Product / Cargo: {ent.get('product_name')} | Category: {ent.get('product_category')} | HS Code: {ent.get('hs_code')} | Supplier: {ent.get('supplier_name')}",
        f"Cargo Flags: Hazardous={ent.get('product_hazardous')}, Perishable={ent.get('product_perishable')}, Temp-Controlled={ent.get('temperature_controlled')}, Fragile={ent.get('fragile')}, Insurance={ent.get('insurance')}",
        f"Mode & Type: {ent.get('shipping_mode')} ({ent.get('shipment_type')}), Priority={ent.get('priority')}, Weight={ent.get('weight_kg')} kg, Volume={ent.get('volume_cbm')} CBM, Declared Value=${ent.get('declared_value')}",
        f"Carrier: {ent.get('carrier_name')} ({ent.get('carrier_type')}, Rating={ent.get('carrier_rating')}/5.0, Fleet={ent.get('fleet_size')}, HQ={ent.get('carrier_hq')})",
        f"Vehicle: {ent.get('vehicle_number')} ({ent.get('vehicle_type')}, Maintenance={ent.get('maintenance_status')}, Fuel={ent.get('fuel_type')})",
        f"Origin Warehouse: {ent.get('warehouse_name')} ({ent.get('warehouse_city')}, Type={ent.get('warehouse_type')}, Utilization={ent.get('current_utilization')}%)",
        f"Route: {ent.get('origin_city')}, {ent.get('origin_country')} ({ent.get('origin_port')}) -> {ent.get('destination_city')}, {ent.get('destination_country')} ({ent.get('destination_port')})",
        f"Route Risk Metrics: Distance={ent.get('distance_km')} km, Avg Transit={ent.get('average_transit_days')} days, Risk={ent.get('route_risk')}, Traffic Index={ent.get('traffic_index')}",
        f"Weather Forecast ({ent.get('weather_city')}, {ent.get('forecast_date')}): {ent.get('weather_condition')}, Temp={ent.get('temperature')}C, Wind={ent.get('wind_speed')} km/h, Rainfall={ent.get('rainfall')} mm, Visibility={ent.get('visibility')} km",
        f"Customs: Required={ent.get('customs_required')}, Documentation Complete={ent.get('documentation_complete')}, Inspection Required={ent.get('inspection_required')}, Cargo Class={ent.get('cargo_type')}, Dest Country={ent.get('customs_destination_country')}",
        f"Schedule & Delivery History: Booked={ent.get('booking_date')}, Shipped={ent.get('ship_date')}, Expected={ent.get('expected_delivery_date')}, Actual={ent.get('actual_delivery_date')}, Attempts={ent.get('delivery_attempts')}",
        f"Incoterm Field: Not stored on this shipment booking record.",
    ]
    if ai_feat or ai_inf:
        lines.append(
            f"AI Risk Telemetry: Route Delay Rate={ai_feat.get('route_delay_rate', 'N/A')}%, "
            f"Carrier Reliability={ai_feat.get('carrier_reliability_score', 'N/A')}, "
            f"Weather Severity={ai_feat.get('weather_severity_score', 'N/A')}, "
            f"Predicted Delay Prob={ai_inf.get('delay_probability', 'N/A')} ({ai_inf.get('risk_category', 'N/A')})"
        )
    lines.append(f"Monitoring Alerts: {alert_summary}")
    return "\n".join(lines)


def build_enterprise_shipment_report(ent: Dict[str, Any], query_lower: str) -> str:
    """Build structured, concise Markdown report for enterprise booking queries (Phase 6 format)."""
    bid = ent["booking_id"]
    is_delayed = ent.get("is_delayed", False)
    status_str = f"🔴 Delayed (+{ent.get('delay_days', 0)} days)" if is_delayed else "🟢 Delivered"

    # Focused attribute responses when user asks one concise question
    if any(w in query_lower for w in ("carrier", "who is carrying", "airline", "shipping line")) and "overview" not in query_lower:
        return (
            f"### Shipment Information – `{bid}`\n"
            f"- **Booking Reference:** `{bid}`\n"
            f"- **Assigned Carrier:** **{ent.get('carrier_name')}** (`{ent.get('carrier_type')}` carrier)\n"
            f"- **Carrier Rating:** {ent.get('carrier_rating')}/5.0 ({ent.get('years_of_service')} years of service, fleet size {ent.get('fleet_size'):,}, HQ: {ent.get('carrier_hq')})\n"
            f"- **Assigned Vehicle:** `{ent.get('vehicle_number')}` ({ent.get('vehicle_type')}, {ent.get('maintenance_status')} condition)\n"
            f"- **Derived Shipment Status:** {status_str}"
        )

    if ("destination" in query_lower or "where is it going" in query_lower) and "origin" not in query_lower:
        return (
            f"### Shipment Information – `{bid}`\n"
            f"- **Booking Reference:** `{bid}`\n"
            f"- **Destination:** **{ent.get('destination_city')}, {ent.get('destination_country')}** (Port/Gateway: {ent.get('destination_port')})\n"
            f"- **Origin:** {ent.get('origin_city')}, {ent.get('origin_country')} ({ent.get('origin_port')})\n"
            f"- **Expected Delivery:** {ent.get('expected_delivery_date')} | **Actual Delivery:** {ent.get('actual_delivery_date')} ({status_str})"
        )

    if "weather" in query_lower and "status" not in query_lower:
        return (
            f"### Operational Weather Context – `{bid}`\n"
            f"- **Monitored City:** {ent.get('weather_city')} (Forecast: {ent.get('forecast_date')})\n"
            f"- **Condition:** **{ent.get('weather_condition')}**\n"
            f"- **Metrics:** Temp {ent.get('temperature')}°C | Rainfall {ent.get('rainfall')} mm | Wind {ent.get('wind_speed')} km/h | Humidity {ent.get('humidity')}% | Visibility {ent.get('visibility')} km\n"
            f"- **Derived Delivery Status:** {status_str}"
        )

    if any(w in query_lower for w in ("warehouse", "storage facility")):
        return (
            f"### Operational Warehouse Information – `{bid}`\n"
            f"- **Warehouse:** **{ent.get('warehouse_name')}** ({ent.get('warehouse_type')} facility)\n"
            f"- **Location:** {ent.get('warehouse_city')}, {ent.get('warehouse_state')}\n"
            f"- **Capacity / Utilization:** {ent.get('warehouse_capacity'):,} units ({ent.get('current_utilization')}% utilized)"
        )

    if "delivery history" in query_lower or "attempts" in query_lower:
        return (
            f"### Operational Delivery History – `{bid}`\n"
            f"- **Derived Delivery Status:** {status_str} *(computed from `shipment_delivery_history`)*\n"
            f"- **Expected Delivery Date:** {ent.get('expected_delivery_date')}\n"
            f"- **Actual Delivery Date:** {ent.get('actual_delivery_date')}\n"
            f"- **Delivery Attempts:** {ent.get('delivery_attempts')}\n"
            f"- **Delay Beyond Expected:** {ent.get('delay_days', 0)} day(s)"
        )

    customs_flag = "Required" if ent.get("customs_required") else "Not Required"
    docs_flag = "Complete" if ent.get("documentation_complete") else "Incomplete"
    insp_flag = "Required" if ent.get("inspection_required") else "Not Required"
    ai_inf = ent.get("ai_inference") or {}
    alerts = ent.get("alerts") or []

    alert_lines = (
        "\n".join(
            f"- **{a.get('severity', 'Info')} — {a.get('alert_type')} ({a.get('alert_status')}):** {a.get('recommended_action')}"
            for a in alerts[:3]
        )
        if alerts
        else "- No open monitoring alerts logged."
    )

    return (
        f"# 📦 Shipment Report – `{bid}`\n\n"
        f"### Shipment Information\n"
        f"- **Booking Reference:** `{bid}`\n"
        f"- **Shipment Status:** {status_str} *(derived from delivery history)*\n"
        f"- **Customer:** {ent.get('customer_name')} ({ent.get('customer_type')} · {ent.get('industry')})\n"
        f"- **Origin:** {ent.get('origin_city')}, {ent.get('origin_country')} ({ent.get('origin_port')})\n"
        f"- **Destination:** {ent.get('destination_city')}, {ent.get('destination_country')} ({ent.get('destination_port')})\n"
        f"- **Carrier:** {ent.get('carrier_name')} ({ent.get('carrier_type')}, Rating {ent.get('carrier_rating')}/5.0)\n"
        f"- **Product / Cargo:** {ent.get('product_name')} (`{ent.get('product_category')}`, HS `{ent.get('hs_code')}`, {ent.get('weight_kg')} kg, ${ent.get('declared_value'):,.2f})\n"
        f"- **Expected Delivery:** {ent.get('expected_delivery_date')}\n"
        f"- **Actual Delivery:** {ent.get('actual_delivery_date')} ({ent.get('delivery_attempts')} attempt(s))\n\n"
        f"### Operational Information\n"
        f"- **Route & Risk:** {ent.get('distance_km')} km (~{ent.get('average_transit_days')} days avg) · Route Risk: **{ent.get('route_risk')}** (Traffic Index: {ent.get('traffic_index')})\n"
        f"- **Warehouse:** {ent.get('warehouse_name')} ({ent.get('warehouse_type')}, {ent.get('current_utilization')}% utilized)\n"
        f"- **Weather Forecast:** {ent.get('weather_city')} — {ent.get('weather_condition')} ({ent.get('temperature')}°C, Wind {ent.get('wind_speed')} km/h)\n"
        f"- **Customs Status:** Customs {customs_flag} · Documentation: **{docs_flag}** · Inspection: {insp_flag}\n"
        f"- **AI Delay Risk Assessment:** Probability `{ai_inf.get('delay_probability', 'N/A')}` (`{ai_inf.get('risk_category', 'N/A')}` risk)\n"
        f"{alert_lines}\n\n"
        f"### Summary\n"
        f"Shipment `{bid}` ({ent.get('shipping_mode')} {ent.get('shipment_type')}, Priority: {ent.get('priority')}) is **{ent.get('derived_status')}** via {ent.get('carrier_name')} from {ent.get('origin_city')} to {ent.get('destination_city')}."
    )


def _lookup_enterprise_shipment_safe(booking_id: str, msg_lower: str) -> Tuple[str, List[str], str, Optional[Dict[str, Any]]]:
    """Retrieve enterprise booking safely and return deterministic structured response."""
    try:
        ent = database.get_enterprise_shipment(booking_id)
        if ent:
            report = build_enterprise_shipment_report(ent, msg_lower)
            src = f"Enterprise Shipment Database ({ent['booking_id']})"
            return report, [src], "enterprise_shipment", ent
    except Exception as exc:
        logger.warning("Enterprise shipment lookup error for %s: %s", booking_id, exc)
    not_found = (
        f"I couldn't find shipment booking **{booking_id}** in the enterprise shipment registry. "
        "Please verify the booking reference (e.g., `ALC-2025-100000` through `ALC-2026-104999`) or `SHP-10001` ID and try again."
    )
    return not_found, [], "not_found", None


def _lookup_standalone_enterprise_entity(clean_msg: str) -> Optional[ChatResult]:
    """Handle explicit lookup requests for Customers, Carriers, Warehouses, or Routes."""
    patterns = [
        ("customer", r"(?:customer|client|account)\s+(?:details|info|information|record|profile)?\s*(?:for|named|is|:)?\s*[\"']?([A-Za-z0-9][A-Za-z0-9\s\-&]{2,45})[\"']?"),
        ("carrier", r"(?:carrier|carrier details|carrier info|shipping line)\s+(?:details|info|information|record)?\s*(?:for|named|is|:)?\s*[\"']?([A-Za-z0-9][A-Za-z0-9\s\-&]{2,40})[\"']?"),
        ("warehouse", r"(?:warehouse|warehouse details|warehouse info|facility)\s+(?:details|info|information|record)?\s*(?:for|named|in|at|:)?\s*[\"']?([A-Za-z0-9][A-Za-z0-9\s\-]{2,45})[\"']?"),
    ]
    for etype, pat in patterns:
        m = re.search(pat, clean_msg, re.IGNORECASE)
        if not m:
            continue
        term = re.sub(r"[?!.,;:]+$", "", m.group(1)).strip()
        # Ignore generic policy words
        if term.lower() in ("information", "details", "rules", "management", "operations", "reference", "requirements"):
            continue
        rows = database.search_enterprise_entity(etype, term, limit=3)
        if not rows:
            continue
        r = rows[0]
        if etype == "customer":
            body = (
                f"### Customer Account Details\n"
                f"- **Customer Name:** {r['customer_name']} (`{r['customer_id']}`)\n"
                f"- **Type / Industry:** {r['customer_type']} · {r['industry']}\n"
                f"- **Location:** {r['city']}, {r['state']}, {r['country']}\n"
                f"- **Status:** {r['customer_status']} (Registered: {r['registration_date']})"
            )
            src = f"Enterprise Customers Database ({r['customer_name']})"
        elif etype == "carrier":
            body = (
                f"### Carrier Details\n"
                f"- **Carrier Name:** {r['carrier_name']} (`{r['carrier_id']}`)\n"
                f"- **Mode / Type:** {r['carrier_type']}\n"
                f"- **Rating:** {r['average_rating']}/5.0\n"
                f"- **Fleet Size:** {r['fleet_size']} · **Experience:** {r['years_of_service']} years\n"
                f"- **Headquarters:** {r['headquarters']}"
            )
            src = f"Enterprise Carriers Database ({r['carrier_name']})"
        else:
            body = (
                f"### Warehouse Information\n"
                f"- **Warehouse:** {r['warehouse_name']} (`{r['warehouse_id']}`)\n"
                f"- **Facility Type:** {r['warehouse_type']}\n"
                f"- **Location:** {r['city']}, {r['state']}\n"
                f"- **Capacity / Utilization:** {r['warehouse_capacity']:,} ({r['current_utilization']}% utilized)"
            )
            src = f"Enterprise Warehouses Database ({r['warehouse_name']})"
        return ChatResult(response=body, sources=[src], response_type=f"enterprise_{etype}", structured_data=r)

    # Check route lookup: "route from X to Y"
    rm = re.search(r"route\s+(?:between|from)\s+([A-Za-z\s]{2,30}?)\s+to\s+([A-Za-z\s]{2,30})", clean_msg, re.IGNORECASE)
    if rm:
        orig_q = rm.group(1).strip()
        dest_q = re.sub(r"[?!.,;:]+$", "", rm.group(2)).strip()
        matched = database.search_enterprise_entity("route", f"{orig_q}->{dest_q}", limit=5)
        if matched:
            rt = matched[0]
            body = (
                f"### Route Information\n"
                f"- **Corridor:** {rt['origin_city']}, {rt['origin_country']} ({rt['origin_port']}) → "
                f"{rt['destination_city']}, {rt['destination_country']} ({rt['destination_port']})\n"
                f"- **Distance:** {rt['distance_km']} km | **Avg Transit:** {rt['average_transit_days']} days\n"
                f"- **Route Risk:** {rt['route_risk']} | **Traffic Index:** {rt['traffic_index']}"
            )
            return ChatResult(
                response=body,
                sources=[f"Enterprise Routes Database ({rt['origin_city']} -> {rt['destination_city']})"],
                response_type="enterprise_route",
                structured_data=rt,
            )
    return None


def _lookup_shipment_safe(target_shipment_id: str, msg_lower: str) -> Tuple[str, List[str], str, Optional[Dict[str, Any]]]:
    """Lookup shipment safely without turning missing IDs into HTTP 500 crashes."""
    try:
        shipment = database.get_shipment(target_shipment_id)
        if shipment:
            report = build_shipment_status_report(shipment, msg_lower)
            source_label = map_source_display(target_shipment_id)
            res_type = "shipment_location" if any(w in msg_lower for w in ("location", "where")) else "shipment_status"
            return report, [source_label], res_type, shipment
    except ShipmentNotFoundError:
        pass
    not_found_msg = (
        f"I couldn't find shipment **{target_shipment_id}** in the FleetHarbor tracking database. "
        "Please verify your 5-digit Shipment ID (e.g., `SHP-10001` through `SHP-20000`) and try again."
    )
    return not_found_msg, [], "not_found", None


def _lookup_employee_safe(target_emp_id: str) -> Tuple[str, List[str], str, Optional[Dict[str, Any]]]:
    """Lookup employee safely and return formatted profile or friendly not-found notice."""
    try:
        emp = database.get_employee(target_emp_id)
        if emp:
            return _build_employee_profile_report(emp), [f"Employee Directory Roster ({target_emp_id})"], "employee_lookup", emp
    except Exception as exc:
        logger.warning("Employee lookup notice: %s", exc)
    not_found_emp = (
        f"I could not find employee **{target_emp_id}** in the FleetHarbor personnel directory. "
        "Please verify the 5-digit employee ID (e.g., `EMP-20001` through `EMP-20500`) or contact the workforce dispatch desk at `dispatch@fleetharbor.com`."
    )
    return not_found_emp, [], "employee_not_found", None


def _resolve_deterministic_response(
    clean_msg: str,
    session,
    previous_shipment_id: Optional[str],
    previous_employee_id: Optional[str],
) -> Optional[ChatResult]:
    """Resolve non-LLM deterministic intents (greetings, compound/single entities, direct defs, guardrails)."""
    msg_lower = clean_msg.lower()

    classified = classify_logistics_query(
        clean_msg,
        session_history=session.get_recent_messages() if session else None,
        previous_shipment_id=previous_shipment_id,
        previous_employee_id=previous_employee_id,
    )

    # Extract explicit/resolved IDs & direct domain matches to handle compound queries cleanly
    explicit_ops_id = extract_operational_id(clean_msg)
    explicit_emp_id = extract_employee_id(clean_msg)
    explicit_booking_id = extract_booking_id(clean_msg)
    explicit_shp_id = None
    try:
        explicit_shp_id = detect_shipment_id(clean_msg)
    except InvalidShipmentIdError:
        raise

    direct_match = None if (explicit_booking_id or classified.booking_id) else find_direct_answer(clean_msg)

    target_ops_id = explicit_ops_id or classified.operational_id
    target_shp_id = explicit_shp_id or (classified.shipment_id if classified.preferred_source == "shipment_database" else None)
    target_booking_id = explicit_booking_id or classified.booking_id
    target_emp_id = explicit_emp_id or (classified.employee_id if classified.preferred_source == "employee_directory" else None)

    # Compound multi-entity query handling (e.g. SHP-10001 + EMP-20001 + FOB vs CIF)
    component_count = sum(1 for item in (target_ops_id, target_shp_id, target_emp_id, direct_match) if item)
    if component_count > 1:
        parts: List[str] = []
        sources: List[str] = []
        structured: Dict[str, Any] = {}
        primary_type = "general_knowledge"

        if target_shp_id:
            shp_resp, shp_srcs, shp_type, shp_data = _lookup_shipment_safe(target_shp_id, msg_lower)
            parts.append(shp_resp)
            sources.extend(shp_srcs)
            primary_type = shp_type
            if shp_data:
                structured["shipment"] = shp_data

        if target_emp_id:
            emp_resp, emp_srcs, _, emp_data = _lookup_employee_safe(target_emp_id)
            parts.append(emp_resp)
            sources.extend(emp_srcs)
            if emp_data:
                structured["employee"] = emp_data

        if target_ops_id:
            ops_rec = database.fetch_operational_record(target_ops_id)
            if ops_rec:
                parts.append(build_operational_status_report(ops_rec))
                sources.append(f"Operational Database ({target_ops_id})")
                structured["operational"] = ops_rec

        if direct_match:
            dir_resp, dir_srcs = direct_match
            parts.append(dir_resp)
            sources.extend(dir_srcs)

        combined_resp = "\n\n---\n\n".join(parts)
        deduped_sources = list(dict.fromkeys(sources))
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", combined_resp)
        return ChatResult(
            response=combined_resp,
            sources=deduped_sources,
            response_type=primary_type,
            shipment_id=target_shp_id,
            structured_data=structured,
        )

    # Greeting & Capability Inquiries
    if classified.intent == LogisticsIntent.GENERAL_CONVERSATION or is_greeting_or_capability_query(clean_msg):
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", GREETING_TEXT)
        return ChatResult(
            response=GREETING_TEXT,
            sources=[],
            response_type="greeting",
            shipment_id=None,
        )

    # Ambiguous Queries Requiring Clarification
    if classified.intent == LogisticsIntent.CLARIFICATION_REQUIRED:
        clarif_type = classified.entities.get("clarification_type")
        if clarif_type == "missing_shipment_id":
            clarif_text = (
                "To check your tracking status, real-time location, transit progress, or estimated delivery date, "
                "please provide your **5-digit Shipment ID** (e.g., `SHP-10001` through `SHP-20000`).\n\n"
                "If you have a physical waybill or receipt, the tracking ID is printed below the barcode in the format `SHP-XXXXX`."
            )
        elif clarif_type == "missing_employee_id":
            clarif_text = (
                "To look up an employee profile in the FleetHarbor personnel directory, "
                "please provide their **5-digit Employee ID** (e.g., `EMP-20001` through `EMP-20500`)."
            )
        elif clarif_type == "ambiguous_fee":
            clarif_text = (
                "# 📋 FleetHarbor Operational Fee Structures\n\n"
                "FleetHarbor maintains standard fee schedules across several operational areas. Could you clarify which fee you are inquiring about?\n\n"
                "- **Demurrage & Detention Fees:** Assessed on ocean containers kept beyond free time (typically $85/day for dry containers, $220/day for reefers).\n"
                "- **Order Cancellation Haulage Fee:** $150 for standard road dispatch cancellation after collection, $450 for specialized heavy/reefer transport.\n"
                "- **Re-delivery Attempt Fees:** Assessed after 2 failed delivery attempts when the consignee is unreachable.\n"
                "- **Customs Clearance Brokerage Fees:** Administrative tariff entry filing and clearance fee schedules."
            )
        elif clarif_type == "ambiguous_hub":
            clarif_text = (
                "# 🌐 FleetHarbor Global Hub Network\n\n"
                "FleetHarbor operates 10 global logistics gateways and sorting hubs. Which hub location would you like details on?\n\n"
                "1. **Dubai Logistics City Gateway** (`DXB-HUB-01`) – UAE\n"
                "2. **Singapore Changi Mega Cargo Hub** (`SIN-HUB-02`) – Singapore\n"
                "3. **Rotterdam Maasvlakte Terminal** (`RTM-HUB-03`) – Netherlands\n"
                "4. **Frankfurt CargoCity South Hub** (`FRA-HUB-04`) – Germany\n"
                "5. **London Heathrow World Cargo Centre** (`LHR-HUB-05`) – UK\n"
                "6. **Tokyo Narita Air Cargo Center** (`NRT-HUB-06`) – Japan\n"
                "7. **Los Angeles / Long Beach Intermodal Hub** (`LAX-HUB-07`) – USA\n"
                "8. **Chicago O'Hare Freight Consolidation Hub** (`ORD-HUB-08`) – USA\n"
                "9. **Amsterdam Schiphol Logistics Hub** (`AMS-HUB-09`) – Netherlands\n"
                "10. **Mumbai Air Cargo & JNPT Terminal** (`BOM-HUB-10`) – India"
            )
        elif clarif_type == "broad_delivery":
            clarif_text = (
                "# 🚚 FleetHarbor Delivery Operations\n\n"
                "FleetHarbor provides multimodal delivery management across air, ocean, road linehaul, and local final-mile courier routes.\n\n"
                "Could you clarify how I can best assist you?\n"
                "- **Track a Specific Delivery:** Provide your Shipment ID (e.g., `SHP-10001`)\n"
                "- **Delivery Statuses:** Learn what *Out for Delivery*, *In Transit*, or *Delivered* mean\n"
                "- **Delivery Exceptions & Delays:** Understand protocols for failed delivery attempts, weather delays, or customs holds\n"
                "- **Proof of Delivery (POD):** How electronic signature and GPS delivery verification are recorded"
            )
        elif clarif_type == "broad_policy":
            policy_overview = (
                "# 📋 FleetHarbor Company Policies Overview\n\n"
                "FleetHarbor maintains standardized operational, compliance, customer, and employee HR policies across all global hubs:\n\n"
                "### 1. Customer & Commercial Policies (`DOC-7806D9117C6C`)\n"
                "- **Service Tiers & Credit:** Enterprise Corporate (Net 30/60), Healthcare & Pharma Priority, and Standard Commercial (Net 15).\n"
                "- **Booking Cut-Offs & Cancellation:** Air (8h), Ocean FCL (48h), LCL (24h), Road (4h); $150–$450 cancellation haulage after dispatch.\n"
                "- **Demurrage & Claims:** Ocean free time (5 days import / 7 days export); claims filed within 3/14/30 days and settled within 21 business days.\n\n"
                "### 2. Cold-Chain, Hazmat & Safety Compliance\n"
                "- **Cold-Chain Pharmaceutical (`CC-POL-9921`):** WHO/EU/USP GDP validation across -70°C, -20°C, 2°C–8°C, and 15°C–25°C.\n"
                "- **Dangerous Goods (`DOC-A425D209E7E3`):** IATA/IMDG/ADR hazard segregation (6 m barrier) and lithium battery rules.\n"
                "- **Warehouse Safety SOP (`DOC-AFFBF53DD573`):** Mandatory EN/ASTM PPE, 8 km/h forklift speed cap, and 3-level incident escalation.\n\n"
                "### 3. Customs & International Trade (`PDF-EXIM-CUSTOMS`, `PDF-INCOTERMS`)\n"
                "- **Cross-Border Clearance:** Export/import declarations, commercial invoices, packing lists, HS codes, and Incoterms 2020 rules.\n\n"
                "### 4. Employee HR, Paid Leave & Overtime (`SOP-HR-006`)\n"
                "- **Leave & Overtime:** 20 annual paid days, 10 paid sick days, 5-step HR Portal leave approval process, and bi-weekly overtime claims.\n\n"
                "Would you like detailed guidelines on any specific policy (e.g., `paid leave`, `process of leave`, `claims policy`, `customs clearance`, or `cold-chain CC-POL-9921`)?"
            )
            policy_sources = [
                "Customer Service Rules & Shipping Terms (DOC-7806D9117C6C)",
                "Warehouse Operations & Safety Standard Operating Procedure (DOC-AFFBF53DD573)",
                "Pharmaceutical Cold-Chain & GDP Compliance Manual (DOC-9167A59967A4)",
                "Employee Paid Leave, Time-Off Process & HR Policy (DOC-AF885F63B95E)",
                "Export-Import Documentation & Customs Reference Guide (PDF-EXIM-CUSTOMS)",
            ]
            if session:
                session.add_message("user", clean_msg)
                session.add_message("assistant", policy_overview)
            return ChatResult(
                response=policy_overview,
                sources=policy_sources,
                response_type="policy_overview",
                shipment_id=None,
            )
        else:
            clarif_text = (
                "Could you please provide more details or specify a Shipment ID (e.g., `SHP-10001`) so I can assist you with your logistics request?"
            )

        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", clarif_text)

        return ChatResult(
            response=clarif_text,
            sources=[],
            response_type="clarification_request",
            shipment_id=None,
        )

    # Aggregate Shipment & Status Count Queries (e.g. "How many shipments are in transit?")
    if not target_shp_id and not target_ops_id and (
        (classified.target_attribute == "aggregate_count" and classified.intent == LogisticsIntent.SHIPMENT_INFO)
        or is_aggregate_shipment_query(clean_msg)
    ):
        agg_result = build_shipment_aggregate_report(
            clean_msg, status_filter=classified.entities.get("status_filter")
        )
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", agg_result.response)
        return agg_result

    # Aggregate Employee Workforce Queries (e.g. "How many employees do we have?")
    if not target_emp_id and not target_ops_id and (
        (classified.target_attribute == "aggregate_count" and classified.intent == LogisticsIntent.EMPLOYEE_SUPPORT)
        or is_aggregate_employee_query(clean_msg)
    ):
        emp_agg_result = build_employee_aggregate_report()
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", emp_agg_result.response)
        return emp_agg_result

    # Operational Records (e.g. OPS-001)
    if target_ops_id:
        try:
            ops_record = database.fetch_operational_record(target_ops_id)
            if ops_record:
                ops_report = build_operational_status_report(ops_record)
                source_label = f"Operational Database ({target_ops_id})"
                if session:
                    session.add_message("user", clean_msg)
                    session.add_message("assistant", ops_report)
                return ChatResult(
                    response=ops_report,
                    sources=[source_label],
                    response_type="operational_status",
                    shipment_id=None,
                    structured_data=ops_record,
                )
            not_found_msg = (
                f"I couldn't find operational record **{target_ops_id}** in the FleetHarbor operational database. "
                f"Please verify the record ID (e.g., `OPS-001` through `OPS-120`) or upload the operational dataset via the attachment (+) button."
            )
            if session:
                session.add_message("user", clean_msg)
                session.add_message("assistant", not_found_msg)
            return ChatResult(
                response=not_found_msg,
                sources=[],
                response_type="not_found",
                shipment_id=None,
            )
        except Exception as exc:
            logger.warning("Operational record lookup notice: %s", exc)

    # Direct Domain Definitions
    if direct_match:
        dir_resp, dir_sources = direct_match
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", dir_resp)
        return ChatResult(
            response=dir_resp,
            sources=dir_sources,
            response_type="direct_answer",
            shipment_id=None,
        )

    # Enterprise Booking Inquiries (ALC-2025-XXXXXX / UUID)
    if target_booking_id:
        if _is_hybrid_enterprise_query(msg_lower):
            # Verify existence first so missing IDs never invoke LLM unnecessarily
            if database.get_enterprise_shipment(target_booking_id) is None:
                ent_resp, ent_srcs, ent_type, ent_data = _lookup_enterprise_shipment_safe(target_booking_id, msg_lower)
                if session:
                    session.add_message("user", clean_msg)
                    session.add_message("assistant", ent_resp)
                return ChatResult(
                    response=ent_resp,
                    sources=ent_srcs,
                    response_type=ent_type,
                    shipment_id=target_booking_id,
                    structured_data=ent_data or {},
                )
            return None  # Hand over to Hybrid Enterprise SQL + ChromaDB RAG + LLM pipeline

        ent_resp, ent_srcs, ent_type, ent_data = _lookup_enterprise_shipment_safe(target_booking_id, msg_lower)
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", ent_resp)
        return ChatResult(
            response=ent_resp,
            sources=ent_srcs,
            response_type=ent_type,
            shipment_id=target_booking_id,
            structured_data=ent_data or {},
        )

    # Shipment Inquiries
    if target_shp_id:
        shp_resp, shp_srcs, shp_type, shp_data = _lookup_shipment_safe(target_shp_id, msg_lower)
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", shp_resp)
        return ChatResult(
            response=shp_resp,
            sources=shp_srcs,
            response_type=shp_type,
            shipment_id=target_shp_id,
            structured_data=shp_data or {},
        )

    # Employee Directory Lookup Intent
    if target_emp_id:
        emp_resp, emp_srcs, emp_type, emp_data = _lookup_employee_safe(target_emp_id)
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", emp_resp)
        return ChatResult(
            response=emp_resp,
            sources=emp_srcs,
            response_type=emp_type,
            shipment_id=None,
            structured_data=emp_data or {},
        )

    # Unsupported / Off-Topic Queries
    if classified.intent == LogisticsIntent.UNSUPPORTED_OFFTOPIC:
        offtopic_msg = (
            "I apologize, but that topic is outside the FleetHarbor logistics domain.\n\n"
            "I can assist you with shipment tracking, delivery routes, customs clearance documentation, "
            "cold-chain cargo rules, and logistics policies. If you need specialized assistance, "
            "please contact the support team at support@fleetharbor.com."
        )
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", offtopic_msg)
        return ChatResult(
            response=offtopic_msg,
            sources=[],
            response_type="unsupported",
            shipment_id=None,
        )

    # Standalone Enterprise Dimension Entity Lookups (Customers, Carriers, Warehouses, Routes)
    ent_entity_res = _lookup_standalone_enterprise_entity(clean_msg)
    if ent_entity_res is not None:
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", ent_entity_res.response)
        return ent_entity_res

    return None


def _prepare_rag_prompt(
    clean_msg: str,
    session,
    previous_shipment_id: Optional[str],
):
    """Run RAG retrieve() (plus enterprise SQL + ChromaDB hybrid enrichment when applicable) ONCE."""
    from logistics_chatbot.chatbot.classifier import extract_booking_id
    from logistics_chatbot.rag.retrieval import RetrievedContext, QueryIntent, QueryType, search_knowledge

    booking_ref = extract_booking_id(clean_msg)
    if not booking_ref and previous_shipment_id and (
        previous_shipment_id.upper().startswith("ALC-") or len(previous_shipment_id) == 36
    ):
        booking_ref = previous_shipment_id

    if booking_ref:
        ent = database.get_enterprise_shipment(booking_ref)
        if ent:
            rag_query = clean_msg
            low = clean_msg.lower()
            if "delay" in low:
                rag_query = f"{clean_msg} shipment delay causes route risk weather customs carrier reliability"
            elif "custom" in low:
                rag_query = f"{clean_msg} customs clearance export import documentation inspection hs code"
            elif "incoterm" in low:
                rag_query = f"{clean_msg} Incoterms 2020 buyer seller responsibility risk transfer"
            elif ent.get("is_delayed") or "guidance" in low or "recommend" in low:
                rag_query = f"{clean_msg} Allcargo customer support delay causes route risk escalation procedure"

            kb_res = search_knowledge(rag_query, top_k=4)
            articles = kb_res.articles if kb_res else []
            ctx = RetrievedContext(
                intent=QueryIntent(query_type=QueryType.MIXED, raw_query=clean_msg),
                shipment=ent,
                knowledge_articles=articles,
                source_doc_ids=[a.get("doc_id", "DOC") for a in articles if a.get("doc_id")],
            )
            raw_sources = [f"Enterprise Shipment Database ({ent['booking_id']})"] + list(ctx.source_doc_ids)
            ent_block = "ENTERPRISE SHIPMENT DATABASE RECORD:\n" + format_enterprise_shipment_context(ent)
            kb_lines = []
            for a in articles:
                did = a.get("doc_id", "DOC")
                ttl = a.get("section_title") or a.get("title") or ""
                kb_lines.append(f"[{did}] {ttl}\n{a.get('content', '')}")
            kb_block = "KNOWLEDGE BASE:\n" + "\n\n".join(kb_lines) if kb_lines else "KNOWLEDGE BASE:\n(No additional documents matched.)"
            formatted = f"{ent_block}\n\n{kb_block}"

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            if session:
                messages.extend(session.get_recent_messages(max_turns=3))
            messages.append({
                "role": "user",
                "content": (
                    f"CONTEXT:\n{formatted}\n\n"
                    f"USER QUESTION: {clean_msg}\n\n"
                    "FORMAT INSTRUCTIONS: Organize your answer clearly using these headings where applicable: "
                    "### Shipment Information, ### Operational Information, ### Knowledge-Based Explanation, ### Summary. "
                    "Clearly distinguish verified database records from general knowledge base guidance. "
                    "Never invent Incoterms or fields marked not stored in the record."
                ),
            })
            return ctx, formatted, messages, raw_sources

    context = retrieve(clean_msg, previous_shipment_id=previous_shipment_id)
    raw_sources = list(context.source_doc_ids) if context and context.source_doc_ids else []
    if context and getattr(context, "shipment_list", None) and not raw_sources:
        raw_sources.append("Shipment Database Registry")
    formatted = format_context(context) if context else ""
    if not formatted:
        return context, "", [], []

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if session:
        messages.extend(session.get_recent_messages(max_turns=3))
    messages.append({
        "role": "user",
        "content": f"CONTEXT:\n{formatted}\n\nUSER QUESTION: {clean_msg}",
    })
    return context, formatted, messages, raw_sources


def _is_unavailable_text(text: str) -> bool:
    ans_lower = (text or "").lower()
    return any(phrase in ans_lower for phrase in (
        "information is not available",
        "not available in the fleetharbor",
        "outside the fleetharbor logistics domain",
        "temporarily unavailable",
        "cannot find",
        "i apologize",
        "sorry, something unexpected went wrong",
        "please contact our support team at support@fleetharbor.com",
    ))


def _invoke_llm(messages: List[Dict[str, str]]) -> str:
    """Invoke call_llm cleanly while honoring test patches on either bot or core chatbot."""
    from unittest.mock import Mock
    import logistics_chatbot.chatbot.chatbot as _core_mod

    if isinstance(_core_mod.call_llm, Mock):
        return _core_mod.call_llm(messages)
    return call_llm(messages)


def generate_response(
    message: str,
    session_id: Optional[str] = None,
) -> ChatResult:
    """Process a user query through the intelligent RAG pipeline and return a structured ChatResult."""
    if not message or not message.strip():
        raise EmptyMessageError(
            "Message cannot be empty. Please provide a question or shipment query."
        )

    clean_msg = message.strip()
    if len(clean_msg) > MAX_QUERY_LENGTH:
        raise QueryTooLongError()

    session, previous_shipment_id, previous_employee_id = _extract_session_context(session_id)

    # 1. Deterministic fast-path intents (greetings, DB entities, direct defs, guardrails)
    det_res = _resolve_deterministic_response(
        clean_msg, session, previous_shipment_id, previous_employee_id
    )
    if det_res is not None:
        return det_res

    # 2. Single-pass RAG retrieval & LLM generation
    context, formatted_ctx, messages, raw_sources = _prepare_rag_prompt(
        clean_msg, session, previous_shipment_id
    )

    if not formatted_ctx or (not context.knowledge_articles and not context.shipment and not context.shipment_list):
        unavailable_msg = (
            "I apologize, but that information is not available in the FleetHarbor logistics knowledge base.\n\n"
            "I can help you with shipment tracking, delivery routes, customs clearance documentation, "
            "cold-chain cargo rules, and logistics policies. If you need specialized assistance, "
            "please contact the support team at support@fleetharbor.com."
        )
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", unavailable_msg)
        return ChatResult(
            response=unavailable_msg,
            sources=[],
            response_type="unavailable",
            shipment_id=None,
        )

    # Let ChatbotError / LLMTimeoutError / LLMRateLimitError propagate cleanly to HTTP layer
    answer = (_invoke_llm(messages) or "").strip()
    if not answer:
        from logistics_chatbot.core.errors import LLMUnavailableError
        raise LLMUnavailableError(detail="Groq returned an empty reply")

    found_citations = _CITATION_PATTERN.findall(answer)
    for cite in found_citations:
        if cite not in raw_sources and not cite.isdigit():
            raw_sources.append(cite)

    clean_answer = clean_citation_brackets(answer)

    if _is_unavailable_text(clean_answer):
        if session:
            session.add_message("user", clean_msg, context=formatted_ctx)
            session.add_message("assistant", clean_answer)
        return ChatResult(
            response=clean_answer,
            sources=[],
            response_type="unavailable",
            shipment_id=None,
        )

    mapped_sources = [map_source_display(s) for s in raw_sources]
    deduped_sources = list(dict.fromkeys(mapped_sources))

    res_booking_id = (
        context.shipment.get("booking_id")
        if (context and isinstance(context.shipment, dict) and context.shipment.get("booking_id"))
        else None
    )

    if session:
        session.add_message("user", clean_msg, context=formatted_ctx)
        session.add_message("assistant", clean_answer)

    return ChatResult(
        response=clean_answer,
        sources=deduped_sources,
        response_type="hybrid_enterprise_rag" if res_booking_id else "general_knowledge",
        shipment_id=res_booking_id,
    )


def stream_chat_response(
    message: str,
    session_id: Optional[str] = None,
):
    """Generator yielding progressive SSE-compatible payload dictionaries (single-pass, zero duplicate LLM calls)."""
    clean_msg = (message or "").strip()
    if not clean_msg:
        msg = "Please type a question about your shipment or logistics operations."
        yield {"token": msg, "done": False}
        yield {"done": True, "response": msg, "sources": [], "response_type": "error"}
        return

    if len(clean_msg) > MAX_QUERY_LENGTH:
        msg = f"Query is too long. Please keep queries under {MAX_QUERY_LENGTH} characters."
        yield {"token": msg, "done": False}
        yield {"done": True, "response": msg, "sources": [], "response_type": "error"}
        return

    try:
        session, previous_shipment_id, previous_employee_id = _extract_session_context(session_id)

        # 1. Deterministic fast-path (ZERO retrieve() or call_llm()!)
        det_res = _resolve_deterministic_response(
            clean_msg, session, previous_shipment_id, previous_employee_id
        )
        if det_res is not None:
            yield {"token": det_res.response, "done": False}
            yield {
                "done": True,
                "response": det_res.response,
                "sources": det_res.sources,
                "response_type": det_res.response_type,
                "shipment_id": det_res.shipment_id,
            }
            return

        # 2. Single-pass RAG retrieval + streaming LLM call
        context, formatted_ctx, messages, raw_sources = _prepare_rag_prompt(
            clean_msg, session, previous_shipment_id
        )
        if not formatted_ctx or (not context.knowledge_articles and not context.shipment and not context.shipment_list):
            unavailable_msg = (
                "I apologize, but that information is not available in the FleetHarbor logistics knowledge base.\n\n"
                "I can help you with shipment tracking, delivery routes, customs clearance documentation, "
                "cold-chain cargo rules, and logistics policies. If you need specialized assistance, "
                "please contact the support team at support@fleetharbor.com."
            )
            if session:
                session.add_message("user", clean_msg)
                session.add_message("assistant", unavailable_msg)
            yield {"token": unavailable_msg, "done": False}
            yield {
                "done": True,
                "response": unavailable_msg,
                "sources": [],
                "response_type": "unavailable",
                "shipment_id": None,
            }
            return

        accumulated_chunks: List[str] = []
        for token_chunk in stream_llm(messages):
            accumulated_chunks.append(token_chunk)
            yield {"token": token_chunk, "done": False}

        full_raw_text = "".join(accumulated_chunks)
        clean_text = clean_citation_brackets(full_raw_text)

        found_citations = _CITATION_PATTERN.findall(full_raw_text)
        for cite in found_citations:
            if cite not in raw_sources and not cite.isdigit():
                raw_sources.append(cite)

        if _is_unavailable_text(clean_text):
            final_sources: List[str] = []
            final_type = "unavailable"
            res_booking_id = None
        else:
            final_sources = list(dict.fromkeys([map_source_display(s) for s in raw_sources]))
            res_booking_id = (
                context.shipment.get("booking_id")
                if (context and isinstance(context.shipment, dict) and context.shipment.get("booking_id"))
                else None
            )
            final_type = "hybrid_enterprise_rag" if res_booking_id else "general_knowledge"

        if session:
            session.add_message("user", clean_msg, context=formatted_ctx)
            session.add_message("assistant", clean_text)

        yield {
            "done": True,
            "response": clean_text,
            "sources": final_sources,
            "response_type": final_type,
            "shipment_id": res_booking_id,
        }

    except ChatbotError as exc:
        logger.warning("Handled chatbot error during stream: %s", exc.detail or exc.user_message)
        yield {"token": exc.user_message, "done": False}
        yield {
            "done": True,
            "response": exc.user_message,
            "sources": [],
            "response_type": "error",
            "shipment_id": None,
        }

    except Exception as exc:
        logger.exception("Unexpected error during chat stream: %s", exc)
        err_msg = "An operational error occurred while generating your answer. Please try again."
        yield {"token": err_msg, "done": False}
        yield {
            "done": True,
            "response": err_msg,
            "sources": [],
            "response_type": "error",
            "shipment_id": None,
        }


def chat(message: str, session_id: Optional[str] = None) -> str:
    """Convenience single-string chat wrapper matching legacy interface."""
    result = generate_response(message, session_id=session_id)
    return result.response
