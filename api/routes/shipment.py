"""Shipment route controller for looking up shipment status and logistics records."""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, Path, status
from fastapi.responses import JSONResponse

from api.schemas.request_models import ErrorResponse, ShipmentResponse
from database.db import get_shipment_by_id
from logistics_chatbot.core.errors import DatabaseError

logger = logging.getLogger("logistics_chatbot.api.shipment")
router = APIRouter(tags=["shipment"])


@router.get(
    "/shipment/{id}",
    response_model=ShipmentResponse,
    responses={
        200: {"model": ShipmentResponse, "description": "Shipment found and returned"},
        400: {"model": ErrorResponse, "description": "Invalid shipment ID format"},
        404: {"model": ErrorResponse, "description": "Shipment Not Found"},
        500: {"model": ErrorResponse, "description": "Database failure"},
    },
    summary="Retrieve shipment information by ID",
    description="Fetches tracking status, route, origin, destination, customs, and delay details for a Shipment ID.",
)
def get_shipment_endpoint(
    id: str = Path(..., description="Unique shipment identifier, e.g. SHP-10001", examples=["SHP-10001"])
) -> JSONResponse:
    clean_id = (id or "").strip()
    if not clean_id:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": "Shipment ID cannot be empty",
                "data": None,
            },
        )

    try:
        record = get_shipment_by_id(clean_id)
        if record is None:
            logger.info("Shipment lookup not found: %s", clean_id)
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "message": "Shipment Not Found",
                    "data": None,
                },
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Shipment retrieved successfully",
                "data": record,
            },
        )

    except DatabaseError as exc:
        logger.error("Database error retrieving %s: %s", clean_id, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"Database query failure: {exc.user_message}",
                "data": None,
            },
        )
    except Exception as exc:
        logger.exception("Unexpected error in /shipment/%s: %s", clean_id, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal server error occurred while retrieving shipment record.",
                "data": None,
            },
        )
