"""Shipment tracking and search HTTP routes."""
from __future__ import annotations

import logging
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query

from logistics_chatbot.application.services import shipment_service
from logistics_chatbot.core.errors import ChatbotError, DatabaseError, ShipmentNotFoundError
from logistics_chatbot.presentation.api.schemas.responses import (
    ErrorResponse,
    ShipmentEnvelopeResponse,
    ShipmentListResponse,
    ShipmentRecordResponse,
)

logger = logging.getLogger("logistics_chatbot.api.shipments")
router = APIRouter()

_SHIPMENT_ID_RE = re.compile(r"^(SHP|ALC)-[A-Za-z0-9_-]+$", re.IGNORECASE)


@router.get(
    "/shipment/{id}",
    tags=["shipment"],
    response_model=ShipmentEnvelopeResponse,
    responses={
        200: {"model": ShipmentEnvelopeResponse, "description": "Shipment found and returned"},
        400: {"model": ErrorResponse, "description": "Invalid shipment ID format"},
        404: {"model": ErrorResponse, "description": "Shipment Not Found"},
        500: {"model": ErrorResponse, "description": "Database failure"},
    },
    summary="Retrieve shipment information by ID",
    description="Fetches tracking status, route, origin, destination, customs, and delay details for a Shipment ID.",
)
async def get_shipment_endpoint(
    id: str = Path(
        ...,
        description="Unique shipment identifier, e.g. SHP-10001",
        json_schema_extra={"examples": ["SHP-10001"]},
    )
):
    """Return structured shipment details by SHP-* or ALC-* identifier."""
    clean_id = (id or "").strip().upper()
    if not clean_id:
        raise HTTPException(status_code=400, detail="Shipment ID cannot be empty.")

    try:
        shipment_data = shipment_service.lookup_shipment_by_id(clean_id)
    except DatabaseError as exc:
        logger.error("Database failure looking up shipment %s: %s", clean_id, exc.detail or exc)
        raise HTTPException(status_code=500, detail=f"Database query failure: {exc.user_message}")
    except Exception as exc:
        logger.exception("Unexpected error looking up shipment %s: %s", clean_id, exc)
        raise HTTPException(status_code=500, detail="An internal error occurred while retrieving shipment details.")

    if not shipment_data:
        raise HTTPException(status_code=404, detail="Shipment Not Found")

    return ShipmentEnvelopeResponse(
        success=True,
        message="Shipment retrieved successfully",
        data=shipment_data,
    )


def _to_shipment_record(row: dict) -> ShipmentRecordResponse:
    """Map a repository shipment dict onto the typed API response model."""
    return ShipmentRecordResponse(
        shipment_id=str(row.get("shipment_id", "")),
        origin=str(row.get("origin", "")),
        destination=str(row.get("destination", "")),
        status=str(row.get("status", "")),
        current_location=row.get("current_location"),
        route=row.get("route"),
        estimated_delivery=row.get("estimated_delivery"),
        delay_reason=row.get("delay_reason"),
        customs_status=row.get("customs_status"),
        last_updated=row.get("last_updated"),
    )


@router.get(
    "/api/shipments/{shipment_id}",
    tags=["shipments"],
    response_model=ShipmentRecordResponse,
    summary="Get single shipment details",
)
async def api_get_shipment(shipment_id: str):
    """Return typed shipment details by ID."""
    try:
        res = shipment_service.get_shipment_detail(shipment_id)
        return _to_shipment_record(res.shipment)
    except ShipmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.user_message or exc.detail)
    except ChatbotError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.user_message or exc.detail)


@router.get(
    "/api/shipments",
    tags=["shipments"],
    response_model=ShipmentListResponse,
    summary="Filter shipments by status, origin, or destination",
)
async def api_list_shipments(
    status: Optional[str] = Query(default=None, description="Filter by status (Delayed, In Transit, Delivered, etc.)"),
    origin: Optional[str] = Query(default=None, description="Filter by origin location substring"),
    destination: Optional[str] = Query(default=None, description="Filter by destination location substring"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of records to return"),
):
    """Return shipments filtered by operational status and/or corridor."""
    res = shipment_service.filter_shipments(
        status=status,
        origin=origin,
        destination=destination,
        limit=limit,
    )
    items = [_to_shipment_record(s) for s in res.shipments]
    return ShipmentListResponse(
        total_count=res.total_count,
        filter_description=res.filter_description,
        shipments=items,
    )
