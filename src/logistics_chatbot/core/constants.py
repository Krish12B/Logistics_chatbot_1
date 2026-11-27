"""Centralized domain and application constants for NexusFreight / FleetHarbor AI."""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

# ── Identifier Regex Patterns ────────────────────────────────────────
LOOSE_SHIPMENT_ID_PATTERN = re.compile(r"\bSHP[-\s]?(\d{3,6})\b", re.IGNORECASE)
VALID_SHIPMENT_ID_PATTERN = re.compile(r"^SHP-\d{5}$")
BOOKING_ID_PATTERN = re.compile(r"\bALC[-\s]?(\d{4})[-\s]?(\d{5,7})\b", re.IGNORECASE)
UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
EMPLOYEE_ID_PATTERN = re.compile(r"\bEMP[-\s]?(\d{5})\b", re.IGNORECASE)
OPERATIONAL_ID_PATTERN = re.compile(r"\bOPS[-\s]?(\d{1,6})\b", re.IGNORECASE)

# ── Upload & Input Limits ────────────────────────────────────────────
SUPPORTED_UPLOAD_EXTENSIONS: Tuple[str, ...] = (".txt", ".pdf", ".docx", ".csv")
MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
DEFAULT_MAX_QUERY_LENGTH: int = 2000

# ── Status Validation Sets ───────────────────────────────────────────
VALID_SHIPMENT_STATUSES = {
    "IN TRANSIT",
    "DELIVERED",
    "OUT FOR DELIVERY",
    "DELAYED",
    "CUSTOMS HOLD",
    "ON HOLD - CUSTOMS",
    "PENDING",
    "CANCELLED",
    "AWAITING PICKUP",
}

VALID_EMPLOYEE_STATUSES = {
    "ACTIVE",
    "ON LEAVE",
    "PROBATION",
    "SUSPENDED",
    "INACTIVE",
}

STATUS_EMOJI_MAP: Dict[str, str] = {
    "in transit": "🟡 In Transit",
    "delivered": "🟢 Delivered",
    "delayed": "🔴 Delayed",
    "on hold - customs": "🟠 On Hold - Customs",
    "customs hold": "🟠 Customs Hold",
    "out for delivery": "🚚 Out for Delivery",
    "pending": "⚪ Pending",
    "cancelled": "⚫ Cancelled",
}

# ── Retrieval Stop Words ─────────────────────────────────────────────
STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or",
    "is", "are", "was", "were", "what", "how", "why", "when", "where",
    "who", "which", "can", "could", "should", "would", "do", "does",
    "did", "tell", "me", "about", "your", "my", "our", "you", "i",
    "joke", "hi", "hello", "hey",
}

# ── Canonical Document Display Titles ────────────────────────────────
DOCUMENT_DISPLAY_MAP: Dict[str, str] = {
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

# ── PDF Document Catalog Mapping ─────────────────────────────────────
PDF_CATALOG_MAP: Dict[str, Tuple[str, str, str]] = {
    "customer support tracking booking reference.pdf": (
        "PDF-CUST-SUPPORT",
        "Customer Support, Tracking & Booking Reference",
        "customer_support",
    ),
    "export import documentation customs reference guide.pdf": (
        "PDF-EXIM-CUSTOMS",
        "Export-Import Documentation & Customs Reference Guide",
        "customs_documentation",
    ),
    "incoterms international trade terms guide.pdf": (
        "PDF-INCOTERMS",
        "Incoterms & International Trade Terms Guide",
        "incoterms_trade",
    ),
    "shipment delay causes route risk reference.pdf": (
        "PDF-DELAY-RISK",
        "Shipment Delay Causes & Route Risk Reference",
        "delay_route_risk",
    ),
    "warehousing contract logistics reference.pdf": (
        "PDF-WAREHOUSING",
        "Warehousing & Contract Logistics Reference",
        "warehousing_logistics",
    ),
}

# ── Text Chunking Defaults ───────────────────────────────────────────
CHUNK_SIZE: int = 500
CHUNK_OVERLAP: int = 80
PDF_CHUNK_SIZE: int = 750
PDF_CHUNK_OVERLAP: int = 110
MIN_CHUNK_LENGTH: int = 30
