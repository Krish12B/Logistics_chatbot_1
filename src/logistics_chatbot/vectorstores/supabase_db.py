"""Supabase REST client operations wrapper.

Superseded by database/database.py for direct PostgreSQL pooling,
kept for backward-compatible REST API access where needed.
"""
from __future__ import annotations

import warnings
from typing import Optional

from supabase import Client, create_client

from logistics_chatbot.core import config
from logistics_chatbot.core.errors import DatabaseError, ShipmentNotFoundError

_client: Optional[Client] = None


def get_supabase() -> Client:
    """Return a cached Supabase REST client."""
    global _client
    if _client is not None:
        return _client

    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        raise DatabaseError(
            detail="SUPABASE_URL and SUPABASE_KEY must be set in the environment / .env"
        )
    try:
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    except Exception as exc:
        raise DatabaseError(detail=f"Cannot connect to Supabase: {exc}") from exc
    return _client


def get_shipment(shipment_id: str) -> dict:
    """Fetch one shipment row from Supabase by its ID."""
    try:
        response = (
            get_supabase()
            .table("shipments")
            .select("*")
            .eq("shipment_id", shipment_id)
            .execute()
        )
    except Exception as exc:
        raise DatabaseError(detail=f"Supabase query failed: {exc}") from exc

    if not response.data:
        raise ShipmentNotFoundError(
            f"I couldn't find shipment {shipment_id}. Please check the ID and try again.",
            detail=f"No row for {shipment_id}",
        )

    return response.data[0]
