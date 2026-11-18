"""Utility helpers for date formatting, hashing, and vector conversion."""
from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Any, List, Optional


def compute_content_hash(text: str) -> str:
    """Generate SHA-256 hash of text for chunk versioning and change detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def format_date(value: Any) -> Optional[str]:
    """Convert date/datetime to standard string representation."""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value) if value is not None else None


def to_pgvector(vector: List[float]) -> str:
    """Format a Python float list as a PostgreSQL pgvector literal, e.g. '[0.1,0.2,...]'."""
    return "[" + ",".join(str(v) for v in vector) + "]"
