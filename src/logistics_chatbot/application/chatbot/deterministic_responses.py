"""Deterministic fast-path responses for greetings, direct concepts, entities, and aggregates."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from logistics_chatbot.application.chatbot.classifier import (
    classify_logistics_query,
    extract_booking_id,
    extract_employee_id,
    extract_operational_id,
)
from logistics_chatbot.application.chatbot.response_formatter import (
    build_employee_aggregate_report,
    build_employee_location_count_report,
    build_employee_profile_report,
    build_enterprise_shipment_report,
    build_operational_status_report,
    build_shipment_aggregate_report,
    build_shipment_status_report,
    format_enterprise_entity_card,
    map_source_display,
)
from logistics_chatbot.application.prompts.system_prompt import GREETING_TEXT
from logistics_chatbot.application.rag.retriever import detect_shipment_id
from logistics_chatbot.core.errors import InvalidShipmentIdError, ShipmentNotFoundError
from logistics_chatbot.domain.entities.models import ChatResult, LogisticsIntent
from logistics_chatbot.infrastructure.database import repository as database

logger = logging.getLogger("logistics_chatbot.deterministic")

DIRECT_ANSWERS: Dict[str, Tuple[str, List[str]]] = {
    "out for delivery": (
        "**Out for Delivery** indicates that the shipment has arrived at the destination local fulfillment facility or hub and has been loaded onto the delivery courier vehicle. The delivery executive is actively en route to complete physical delivery to the recipient's address today during standard delivery hours.",
        ["Logistics Tracking & Status Guide (SS-003)", "Freight Lifecycle, Shipping Terms & Operational SOP (DOC-CAED8BC8636D)"],
    ),
    "in transit": (
        "**In Transit** means your shipment has departed the origin facility and is actively moving between logistics facilities, gateway terminals, or along linehaul corridors toward its destination.",
        ["Logistics Tracking & Status Guide (SS-003)"],
    ),
    "delivered": (
        "**Delivered** means your shipment has reached its final destination address and has been physically received and signed for by the consignee with Proof of Delivery (POD) recorded.",
        ["Logistics Tracking & Status Guide (SS-003)"],
    ),
    "delayed": (
        "**Delayed** means an unexpected event (such as adverse weather, transport congestion, mechanical maintenance, or documentation review) has extended the initial estimated transit time.",
        ["Shipment Delay & Exception Policy (LC-0003)"],
    ),
    "customs clearance": (
        "**Customs Clearance** is the mandatory government regulatory procedure where export and import declarations, commercial invoices, and duties/taxes are verified and settled before goods can legally cross international borders.",
        ["Customs Trade Compliance & Cross-Border Rules (DOC-6BDEA8303C7A)", "Logistics Terminology & Glossary (GL-0069)"],
    ),
    "bill of lading": (
        "A **Bill of Lading (BOL)** is a legally binding contract and title document issued by a freight carrier detailing cargo type, quantity, origin, consignee, and destination for ocean and multimodal transport.",
        ["Documentation Standard Operating Procedure (DC-0085)", "Customer Service Rules & Shipping Terms (DOC-7806D9117C6C)"],
    ),
    "demurrage": (
        "**Demurrage** is a penalty charge assessed by shipping lines or port authorities when an imported container remains inside the port terminal or container yard beyond the allotted free days (typically 4 to 7 calendar days). In contrast, **Detention** (per diem) is charged when an empty or loaded container is kept outside the port facility beyond the permitted free return window.",
        ["Freight Lifecycle, Shipping Terms & Operational SOP (DOC-CAED8BC8636D)"],
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
        ["Freight Lifecycle, Shipping Terms & Operational SOP (DOC-CAED8BC8636D)"],
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
        ["Cargo Weight, Dimensions & Container Specifications (DOC-CF9235FF4F8A)"],
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
        ["Freight Lifecycle, Shipping Terms & Operational SOP (DOC-CAED8BC8636D)"],
    ),
    "proof of delivery": (
        "**Proof of Delivery (POD)** is an authoritative verification and legal receipt confirming that cargo has been physically handed over to and accepted by the consignee.\n\n"
        "FleetHarbor captures electronic Proof of Delivery (e-POD) at the delivery address, recording:\n"
        "- Consignee recipient full name and digital signature.\n"
        "- Exact date, timestamp, and GPS delivery coordinates.\n"
        "- Delivered carton count and outer packaging integrity sign-off.\n"
        "- Exception annotations (if visible damage or shortage occurred).\n\n"
        "e-POD records are archived digitally and accessible via shipment tracking lookup within 15 minutes of completion.",
        ["Freight Lifecycle, Shipping Terms & Operational SOP (DOC-CAED8BC8636D)"],
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
        ["Freight Lifecycle, Shipping Terms & Operational SOP (DOC-CAED8BC8636D)"],
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
        ["Shipment Delay & Exception Policy (LC-0003)"],
    ),
}

DIRECT_DEFINITIONS = {k: v[0] for k, v in DIRECT_ANSWERS.items()}


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
    domain_keywords = ("shp-", "customs", "cold-chain", "pharma", "delay", "transit", "invoice", "lading", "tracking")
    for p in patterns:
        if re.search(p, clean):
            return not any(dk in clean for dk in domain_keywords)
    return False


def find_direct_answer(clean_msg: str) -> Optional[Tuple[str, List[str]]]:
    """Check if query directly matches standard logistics concept inquiries."""
    q = re.sub(r"[?!.,;:]+", "", clean_msg.strip().lower())

    if "out for delivery" in q and any(w in q for w in ("what", "mean", "define", "explain", "meaning")):
        return DIRECT_ANSWERS["out for delivery"]
    if q in ("out for delivery", "what is out for delivery", "what does out for delivery mean"):
        return DIRECT_ANSWERS["out for delivery"]
    if any(k in q for k in ("cargo weight", "dimension limit", "container spec", "container dimension", "container size", "weight and dimension", "weight and dimension limits")):
        return DIRECT_ANSWERS["cargo weight limits"]
    if "lifecycle" in q or ("pickup to delivery" in q and "shipment" in q):
        return DIRECT_ANSWERS["shipment lifecycle"]
    if "demurrage" in q and any(w in q for w in ("what", "mean", "define", "explain", "meaning", "freight")):
        return DIRECT_ANSWERS["demurrage"]
    if ("fob" in q and "cif" in q) or "difference between fob and cif" in q:
        return DIRECT_ANSWERS["fob vs cif"]
    if ("proof of delivery" in q or " pod " in f" {q} ") and any(w in q for w in ("what", "how", "obtained", "verify", "meaning")):
        return DIRECT_ANSWERS["proof of delivery"]
    if "air vs ocean" in q or "ocean vs air" in q or ("air" in q and "ocean" in q and "transit" in q):
        return DIRECT_ANSWERS["air vs ocean transit"]
    if "what should customers do when a shipment is delayed" in q or "what can be done" in q:
        return None
    if "happens when a shipment is delayed" in q or "handling shipment delays" in q or q in ("shipment delayed", "delayed shipment"):
        return DIRECT_ANSWERS["delayed shipment"]

    for term, (definition, sources) in DIRECT_ANSWERS.items():
        if q in (term, f"what is {term}", f"what does {term} mean", f"define {term}"):
            return (definition, sources)
    return None


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
    return has_count_cue and (has_shipment_noun or any(s in q for s in ("in transit", "delivered", "delayed", "customs hold", "out for delivery")))


def is_aggregate_employee_query(text: str) -> bool:
    """Determine if a query asks for total workforce count or department staffing breakdown."""
    q = re.sub(r"[?!.,;:]+", " ", text.lower()).strip()
    has_count = any(w in q for w in ("how many", "count", "total number", "number of", "total employees", "total staff", "workforce count"))
    has_emp = any(w in q for w in ("employee", "employees", "staff", "personnel", "workers", "workforce", "drivers"))
    return has_count and has_emp


def _is_hybrid_enterprise_query(msg_lower: str) -> bool:
    reasoning_cues = (
        "why ", "why?", "explain", "what can be done", "how can", "how to ",
        "recommend", "mitigate", "incoterm", "responsibilit", "guidance",
        "requirement", "requirements", "what should", "resolve", "steps",
    )
    return any(cue in msg_lower for cue in reasoning_cues)


def _lookup_enterprise_shipment_safe(booking_id: str, msg_lower: str, db_repo=None) -> Tuple[str, List[str], str, Optional[Dict[str, Any]]]:
    repo = db_repo or database
    try:
        ent = repo.get_enterprise_shipment(booking_id)
        if ent:
            report = build_enterprise_shipment_report(ent, msg_lower)
            return report, [f"Enterprise Shipment Database ({ent['booking_id']})"], "enterprise_shipment", ent
    except Exception as exc:
        logger.warning("Enterprise shipment lookup error for %s: %s", booking_id, exc)
    not_found = (
        f"I couldn't find shipment booking **{booking_id}** in the enterprise shipment registry. "
        "Please verify the booking reference (e.g., `ALC-2025-100000` through `ALC-2026-104999`) or `SHP-10001` ID and try again."
    )
    return not_found, [], "not_found", None


def _lookup_standalone_enterprise_entity(clean_msg: str, db_repo=None) -> Optional[ChatResult]:
    repo = db_repo or database
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
        if term.lower() in ("information", "details", "rules", "management", "operations", "reference", "requirements"):
            continue
        rows = repo.search_enterprise_entity(etype, term, limit=3)
        if rows:
            return format_enterprise_entity_card(etype, rows[0])

    rm = re.search(r"route\s+(?:between|from)\s+([A-Za-z\s]{2,30}?)\s+to\s+([A-Za-z\s]{2,30})", clean_msg, re.IGNORECASE)
    if rm:
        orig_q = rm.group(1).strip()
        dest_q = re.sub(r"[?!.,;:]+$", "", rm.group(2)).strip()
        matched = repo.search_enterprise_entity("route", f"{orig_q}->{dest_q}", limit=5)
        if matched:
            return format_enterprise_entity_card("route", matched[0])
    return None


def _lookup_shipment_safe(target_shipment_id: str, msg_lower: str, db_repo=None) -> Tuple[str, List[str], str, Optional[Dict[str, Any]]]:
    repo = db_repo or database
    try:
        shipment = repo.get_shipment(target_shipment_id)
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


def _lookup_employee_safe(target_emp_id: str, db_repo=None) -> Tuple[str, List[str], str, Optional[Dict[str, Any]]]:
    repo = db_repo or database
    try:
        emp = repo.get_employee(target_emp_id)
        if emp:
            return build_employee_profile_report(emp), [f"Employee Directory Roster ({target_emp_id})"], "employee_lookup", emp
    except Exception as exc:
        logger.warning("Employee lookup notice: %s", exc)
    not_found_emp = (
        f"I could not find employee **{target_emp_id}** in the FleetHarbor personnel directory. "
        "Please verify the 5-digit employee ID (e.g., `EMP-20001` through `EMP-20500`) or contact the workforce dispatch desk at `dispatch@fleetharbor.com`."
    )
    return not_found_emp, [], "employee_not_found", None


def _clarification_response(clarif_type: Optional[str], db_repo=None) -> Tuple[str, List[str], str]:
    if clarif_type == "missing_shipment_id":
        return (
            "To check your tracking status, real-time location, transit progress, or estimated delivery date, "
            "please provide your **5-digit Shipment ID** (e.g., `SHP-10001` through `SHP-20000`).\n\n"
            "If you have a physical waybill or receipt, the tracking ID is printed below the barcode in the format `SHP-XXXXX`.",
            [],
            "clarification_request",
        )
    if clarif_type == "missing_employee_id":
        return (
            "To look up an employee profile in the FleetHarbor personnel directory, "
            "please provide their **5-digit Employee ID** (e.g., `EMP-20001` through `EMP-20500`).",
            [],
            "clarification_request",
        )
    if clarif_type == "ambiguous_fee":
        return (
            "# 📋 FleetHarbor Operational Fee Structures\n\n"
            "FleetHarbor maintains standard fee schedules across several operational areas. Could you clarify which fee you are inquiring about?\n\n"
            "- **Demurrage & Detention Fees:** Assessed on ocean containers kept beyond free time (typically $85/day for dry containers, $220/day for reefers).\n"
            "- **Order Cancellation Haulage Fee:** $150 for standard road dispatch cancellation after collection, $450 for specialized heavy/reefer transport.\n"
            "- **Re-delivery Attempt Fees:** Assessed after 2 failed delivery attempts when the consignee is unreachable.\n"
            "- **Customs Clearance Brokerage Fees:** Administrative tariff entry filing and clearance fee schedules.",
            [],
            "clarification_request",
        )
    if clarif_type == "ambiguous_hub":
        repo = db_repo or database
        hub_rows = []
        try:
            if hasattr(repo, "list_hubs"):
                hub_rows = repo.list_hubs()
        except Exception as exc:
            logger.debug("Hub lookup notice: %s", exc)
        if hub_rows:
            hub_lines = "\n".join(
                f"{idx}. **{h['facility_name']}** (`{h['hub_code']}`) – {h['city_country']}"
                for idx, h in enumerate(hub_rows, start=1)
            )
            return (
                f"# 🌐 FleetHarbor Global Hub Network\n\n"
                f"FleetHarbor operates {len(hub_rows)} primary logistics gateway hubs. Which hub location would you like details on?\n\n"
                f"{hub_lines}",
                ["Global Hubs Registry"],
                "clarification_request",
            )
        return (
            "# 🌐 FleetHarbor Global Hub Network\n\n"
            "Could you specify which hub city or facility name you would like information about?",
            [],
            "clarification_request",
        )
    if clarif_type == "broad_delivery":
        return (
            "# 🚚 FleetHarbor Delivery Operations\n\n"
            "FleetHarbor provides multimodal delivery management across air, ocean, road linehaul, and local final-mile courier routes.\n\n"
            "Could you clarify how I can best assist you?\n"
            "- **Track a Specific Delivery:** Provide your Shipment ID (e.g., `SHP-10001`)\n"
            "- **Delivery Statuses:** Learn what *Out for Delivery*, *In Transit*, or *Delivered* mean\n"
            "- **Delivery Exceptions & Delays:** Understand protocols for failed delivery attempts, weather delays, or customs holds\n"
            "- **Proof of Delivery (POD):** How electronic signature and GPS delivery verification are recorded",
            [],
            "clarification_request",
        )
    if clarif_type == "broad_policy":
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
        return policy_overview, policy_sources, "policy_overview"

    return (
        "Could you please provide more details or specify a Shipment ID (e.g., `SHP-10001`) so I can assist you with your logistics request?",
        [],
        "clarification_request",
    )


def resolve_deterministic_response(
    clean_msg: str,
    session,
    previous_shipment_id: Optional[str],
    previous_employee_id: Optional[str],
    db_repo=None,
) -> Optional[ChatResult]:
    """Resolve non-LLM deterministic intents (greetings, compound/single entities, direct defs, guardrails)."""
    repo = db_repo or database
    msg_lower = clean_msg.lower()

    classified = classify_logistics_query(
        clean_msg,
        session_history=session.get_recent_messages() if session else None,
        previous_shipment_id=previous_shipment_id,
        previous_employee_id=previous_employee_id,
    )

    explicit_ops_id = extract_operational_id(clean_msg)
    explicit_emp_id = extract_employee_id(clean_msg)
    explicit_booking_id = extract_booking_id(clean_msg)
    explicit_shp_id = detect_shipment_id(clean_msg)

    direct_match = None if (explicit_booking_id or classified.booking_id) else find_direct_answer(clean_msg)

    target_ops_id = explicit_ops_id or classified.operational_id
    target_shp_id = explicit_shp_id or (classified.shipment_id if classified.preferred_source == "shipment_database" else None)
    target_booking_id = explicit_booking_id or classified.booking_id
    target_emp_id = explicit_emp_id or (classified.employee_id if classified.preferred_source == "employee_directory" else None)

    component_count = sum(1 for item in (target_ops_id, target_shp_id, target_emp_id, direct_match) if item)
    if component_count > 1:
        parts: List[str] = []
        sources: List[str] = []
        structured: Dict[str, Any] = {}
        primary_type = "general_knowledge"

        if target_shp_id:
            shp_resp, shp_srcs, shp_type, shp_data = _lookup_shipment_safe(target_shp_id, msg_lower, repo)
            parts.append(shp_resp)
            sources.extend(shp_srcs)
            primary_type = shp_type
            if shp_data:
                structured["shipment"] = shp_data
        if target_emp_id:
            emp_resp, emp_srcs, _, emp_data = _lookup_employee_safe(target_emp_id, repo)
            parts.append(emp_resp)
            sources.extend(emp_srcs)
            if emp_data:
                structured["employee"] = emp_data
        if target_ops_id:
            ops_rec = repo.fetch_operational_record(target_ops_id)
            if ops_rec:
                parts.append(build_operational_status_report(ops_rec))
                sources.append(f"Operational Database ({target_ops_id})")
                structured["operational"] = ops_rec
        if direct_match:
            dir_resp, dir_srcs = direct_match
            parts.append(dir_resp)
            sources.extend(dir_srcs)

        combined_resp = "\n\n---\n\n".join(parts)
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", combined_resp)
        return ChatResult(
            response=combined_resp,
            sources=list(dict.fromkeys(sources)),
            response_type=primary_type,
            shipment_id=target_shp_id,
            structured_data=structured,
        )

    if classified.intent == LogisticsIntent.GENERAL_CONVERSATION or is_greeting_or_capability_query(clean_msg):
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", GREETING_TEXT)
        return ChatResult(response=GREETING_TEXT, sources=[], response_type="greeting", shipment_id=None)

    if classified.intent == LogisticsIntent.CLARIFICATION_REQUIRED:
        clarif_text, clarif_srcs, clarif_res_type = _clarification_response(
            classified.entities.get("clarification_type"),
            db_repo=repo,
        )
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", clarif_text)
        return ChatResult(
            response=clarif_text,
            sources=clarif_srcs,
            response_type=clarif_res_type,
            shipment_id=None,
        )

    if not target_shp_id and not target_ops_id and (
        (classified.target_attribute == "aggregate_count" and classified.intent == LogisticsIntent.SHIPMENT_INFO)
        or is_aggregate_shipment_query(clean_msg)
    ):
        status_flt = classified.entities.get("status_filter")
        loc_flt = classified.entities.get("location_filter")
        orig_flt = classified.entities.get("origin_filter")
        dest_flt = classified.entities.get("destination_filter")

        if loc_flt or orig_flt or dest_flt:
            summary = repo.get_filtered_shipment_summary(
                status=status_flt,
                location=loc_flt,
                origin=orig_flt,
                destination=dest_flt,
            )
            agg_result = build_shipment_aggregate_report(
                clean_msg,
                counts=summary["counts_by_status"],
                status_filter=status_flt,
                location_filter=summary.get("location"),
                origin_filter=summary.get("origin"),
                destination_filter=summary.get("destination"),
                corridor_origin_count=summary.get("corridor_origin_count"),
                corridor_destination_count=summary.get("corridor_destination_count"),
            )
        else:
            counts = repo.get_shipment_status_counts()
            agg_result = build_shipment_aggregate_report(
                clean_msg, counts=counts, status_filter=status_flt
            )
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", agg_result.response)
        return agg_result

    if not target_emp_id and not target_ops_id and (
        (classified.target_attribute == "aggregate_count" and classified.intent == LogisticsIntent.EMPLOYEE_SUPPORT)
        or is_aggregate_employee_query(clean_msg)
    ):
        emp_loc_flt = classified.entities.get("location_filter")
        if emp_loc_flt and hasattr(repo, "get_employee_count_by_location"):
            emp_agg_result = build_employee_location_count_report(
                repo.get_employee_count_by_location(emp_loc_flt)
            )
        else:
            emp_agg_result = build_employee_aggregate_report(repo.get_employee_counts())
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", emp_agg_result.response)
        return emp_agg_result

    if target_ops_id:
        try:
            ops_record = repo.fetch_operational_record(target_ops_id)
            if ops_record:
                ops_report = build_operational_status_report(ops_record)
                if session:
                    session.add_message("user", clean_msg)
                    session.add_message("assistant", ops_report)
                return ChatResult(
                    response=ops_report,
                    sources=[f"Operational Database ({target_ops_id})"],
                    response_type="operational_status",
                    shipment_id=None,
                    structured_data=ops_record,
                )
            not_found_msg = (
                f"I couldn't find operational record **{target_ops_id}** in the FleetHarbor operational database. "
                "Please verify the record ID (e.g., `OPS-001` through `OPS-120`) or upload the operational dataset via the attachment (+) button."
            )
            if session:
                session.add_message("user", clean_msg)
                session.add_message("assistant", not_found_msg)
            return ChatResult(response=not_found_msg, sources=[], response_type="not_found", shipment_id=None)
        except Exception as exc:
            logger.warning("Operational record lookup notice: %s", exc)

    if direct_match:
        dir_resp, dir_sources = direct_match
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", dir_resp)
        return ChatResult(response=dir_resp, sources=dir_sources, response_type="direct_answer", shipment_id=None)

    if target_booking_id:
        if _is_hybrid_enterprise_query(msg_lower):
            if repo.get_enterprise_shipment(target_booking_id) is None:
                ent_resp, ent_srcs, ent_type, ent_data = _lookup_enterprise_shipment_safe(target_booking_id, msg_lower, repo)
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
            return None

        ent_resp, ent_srcs, ent_type, ent_data = _lookup_enterprise_shipment_safe(target_booking_id, msg_lower, repo)
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

    if target_shp_id:
        shp_resp, shp_srcs, shp_type, shp_data = _lookup_shipment_safe(target_shp_id, msg_lower, repo)
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

    if target_emp_id:
        emp_resp, emp_srcs, emp_type, emp_data = _lookup_employee_safe(target_emp_id, repo)
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
        return ChatResult(response=offtopic_msg, sources=[], response_type="unsupported", shipment_id=None)

    ent_entity_res = _lookup_standalone_enterprise_entity(clean_msg, repo)
    if ent_entity_res is not None:
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", ent_entity_res.response)
        return ent_entity_res

    return None
