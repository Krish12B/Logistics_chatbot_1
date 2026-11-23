"""Database module: shipment data access, connection pooling, and record retrieval."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from logistics_chatbot.database import database as _core_db
from logistics_chatbot.core.errors import DatabaseError, ShipmentNotFoundError

logger = logging.getLogger("logistics_chatbot.db")


def get_shipment_by_id(shipment_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single shipment record by its unique Shipment ID.

    Args:
        shipment_id: Normalized or raw shipment identifier (e.g. 'SHP-10001' or 'SH12345').

    Returns:
        Dictionary containing shipment record details, or None if not found.
    """
    clean_id = (shipment_id or "").strip().upper()
    if not clean_id:
        return None

    try:
        return _core_db.get_shipment(clean_id)
    except ShipmentNotFoundError:
        return None
    except Exception as exc:
        logger.error("Error retrieving shipment %s: %s", clean_id, exc)
        raise DatabaseError(detail=f"Database query failed for shipment {clean_id}: {exc}") from exc


def get_all_shipments(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch shipments list with optional limit."""
    from logistics_chatbot.rag.retrieval import search_shipments
    result = search_shipments(limit=limit)
    return result.shipments


def get_employee_by_id(employee_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve an employee record by ID (e.g. 'EMP-20001')."""
    clean_id = (employee_id or "").strip().upper()
    if not clean_id:
        return None
    try:
        return _core_db.get_employee(clean_id)
    except ShipmentNotFoundError:
        return None
    except Exception as exc:
        logger.error("Error retrieving employee %s: %s", clean_id, exc)
        return None


def init_database() -> None:
    """Initialize database connection or verify schema."""
    _core_db.init_database()


def close() -> None:
    """Close active database connections."""
    _core_db.close()
