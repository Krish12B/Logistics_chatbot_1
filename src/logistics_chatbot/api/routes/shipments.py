"""Shipment tracking and lookup API routes."""
from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from logistics_chatbot.core.errors import ShipmentNotFoundError
from logistics_chatbot.rag.retrieval import get_shipment_by_id, search_shipments
from logistics_chatbot.schemas.models import ShipmentListResponse, ShipmentResponse

logger = logging.getLogger("logistics_chatbot.api.shipments")

router = APIRouter(prefix="/api", tags=["shipments"])


@router.get(
    "/shipments/{shipment_id}",
    response_model=ShipmentResponse,
    summary="Get single shipment details",
)
def api_get_shipment(shipment_id: str):
    try:
        result = get_shipment_by_id(shipment_id.upper())
        return ShipmentResponse(**result.shipment)
    except ShipmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.user_message)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get(
    "/shipments",
    response_model=ShipmentListResponse,
    summary="Filter shipments by status, origin, or destination",
)
def api_list_shipments(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (Delayed, In Transit, Delivered, etc.)"),
    origin: Optional[str] = Query(None, description="Filter by origin location substring"),
    destination: Optional[str] = Query(None, description="Filter by destination location substring"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
):
    try:
        result = search_shipments(
            status=status_filter,
            origin=origin,
            destination=destination,
            limit=limit,
        )
        return ShipmentListResponse(
            total_count=result.total_count,
            filter_description=result.filter_description,
            shipments=[ShipmentResponse(**s) for s in result.shipments],
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
