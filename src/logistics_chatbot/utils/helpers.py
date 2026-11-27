"""Utility helpers for date parsing/formatting, hashing, and vector conversion."""
from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Any, List, Optional


def compute_content_hash(text: str, length: Optional[int] = 16) -> str:
    """Generate SHA-256 hex digest of text for chunk versioning and deduplication."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return digest[:length] if length else digest


def parse_date(val: Any) -> Optional[date]:
    """Parse common date formats into a date object."""
    if not val:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(val).strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_datetime(val: Any) -> Optional[datetime]:
    """Parse common timestamp formats into a datetime object."""
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    for fmt in ("%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(val).strip(), fmt)
        except ValueError:
            continue
    return None


def format_date(value: Any) -> Optional[str]:
    """Convert date/datetime to standard ISO string representation."""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value) if value is not None else None


def format_display_date(date_str: Any) -> str:
    """Format dates for human-readable reports (e.g., '20 November 2026')."""
    if not date_str:
        return "Not available"
    s = str(date_str).strip()
    try:
        if " " in s:
            dt = datetime.strptime(s, "%Y-%m-%d %H:%M")
            return f"{dt.day} {dt.strftime('%B %Y')}, {dt.strftime('%H:%M')}"
        if "T" in s:
            dt = datetime.fromisoformat(s)
            return f"{dt.day} {dt.strftime('%B %Y')}, {dt.strftime('%H:%M')}"
        dt = datetime.strptime(s, "%Y-%m-%d")
        return f"{dt.day} {dt.strftime('%B %Y')}"
    except Exception:
        return s


def to_pgvector(vector: List[float]) -> str:
    """Format a Python float list as a PostgreSQL pgvector literal."""
    return "[" + ",".join(str(v) for v in vector) + "]"
