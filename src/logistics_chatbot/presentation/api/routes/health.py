"""System health and vector-store status routes."""
from __future__ import annotations

from fastapi import APIRouter

from logistics_chatbot.application.ingestion.kb_loader import load_kb_rows
from logistics_chatbot.application.services import document_service
from logistics_chatbot.core import config
from logistics_chatbot.infrastructure.database import repository
from logistics_chatbot.presentation.api.schemas.responses import (
    HealthResponse,
    LegacyHealthResponse,
)

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """Return service availability status."""
    return HealthResponse(success=True, message="Logistics AI Chatbot API is running")


@router.get("/api/health", response_model=LegacyHealthResponse, summary="Detailed API health status")
async def legacy_health_check():
    """Return detailed configuration and dataset health telemetry."""
    try:
        shipment_count = repository.get_shipment_count()
    except Exception:
        shipment_count = 0

    try:
        kb_count = len(load_kb_rows())
    except Exception:
        kb_count = 0

    return LegacyHealthResponse(
        status="healthy",
        groq_model=config.GROQ_MODEL,
        groq_configured=bool(config.GROQ_API_KEY),
        supabase_configured=bool(config.SUPABASE_URL or config.SUPABASE_DB_URL),
        embedding_model=config.EMBEDDING_MODEL,
        active_dataset_shipments=shipment_count,
        active_dataset_kb_articles=kb_count,
    )


@router.get("/api/vector-db/health", summary="ChromaDB status")
async def vector_db_health():
    """Return health details of the ChromaDB vector database."""
    return document_service.vector_store_health()
