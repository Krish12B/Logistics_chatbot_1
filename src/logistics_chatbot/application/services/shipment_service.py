"""Application shipment use-case service."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from logistics_chatbot.application.rag import retriever
from logistics_chatbot.core.errors import DatabaseError, ShipmentNotFoundError
from logistics_chatbot.domain.entities.models import ShipmentListResult, ShipmentResult
from logistics_chatbot.infrastructure.database import repository

logger = logging.getLogger("logistics_chatbot.services.shipment")


def lookup_shipment_by_id(shipment_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a legacy SHP-* or enterprise ALC-* shipment record, or None if not found."""
    clean_id = (shipment_id or "").strip().upper()
    if not clean_id:
        return None
    try:
        if clean_id.startswith("ALC-"):
            return repository.get_enterprise_shipment(clean_id)
        return repository.get_shipment(clean_id)
    except ShipmentNotFoundError:
        return None
    except Exception as exc:
        logger.error("Error retrieving shipment %s: %s", clean_id, exc)
        raise DatabaseError(detail=f"Database query failed for shipment {clean_id}: {exc}") from exc


def get_shipment_detail(shipment_id: str) -> ShipmentResult:
    """Retrieve shipment result (raises ShipmentNotFoundError when missing)."""
    return retriever.get_shipment_by_id(shipment_id.upper())


def filter_shipments(
    status: Optional[str] = None,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    limit: int = 10,
) -> ShipmentListResult:
    """Filter shipments by status, origin, or destination."""
    return retriever.search_shipments(
        status=status,
        origin=origin,
        destination=destination,
        limit=limit,
    )
