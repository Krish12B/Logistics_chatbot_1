"""FastAPI REST API application for FleetHarbor Logistics AI Chatbot.

Endpoints:
  POST /api/chat            - Submit user question, returns grounded answer & session
  GET  /api/shipments/{id}  - Lookup shipment by ID
  GET  /api/shipments       - Filter shipments by status, origin, destination
  GET  /api/health          - Health check and configuration status
  GET  /api/vector-db/health- ChromaDB vector database health check
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

# Ensure src/ is discoverable even when executed directly via VS Code "Run" button
_SRC_DIR = Path(__file__).resolve().parents[2]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from logistics_chatbot.core import config
from logistics_chatbot.core.errors import (
    ChatbotError,
    EmptyMessageError,
    InvalidShipmentIdError,
    QueryTooLongError,
    ShipmentNotFoundError,
)
from logistics_chatbot.chatbot.chatbot import chat, get_conversation_store
from logistics_chatbot.rag.retrieval import get_shipment_by_id, retrieve, search_shipments
from logistics_chatbot.schemas.models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ShipmentListResponse,
    ShipmentResponse,
)
from logistics_chatbot.vectorstores import chroma_db

logger = logging.getLogger("logistics_chatbot.api")

app = FastAPI(
    title="FleetHarbor Logistics AI Chatbot API",
    description="Backend RAG service integrating ChromaDB, Supabase PostgreSQL, pgvector, and Groq LLM.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Chat Endpoint ───────────────────────────────────────────────────

@app.post(
    "/api/chat",
    response_model=ChatResponse,
    summary="Ask a logistics question",
    description="Answers tracking, delay, customs, and policy questions using grounded knowledge.",
    tags=["chat"],
)
def api_chat(req: ChatRequest):
    store = get_conversation_store()
    session_id = req.session_id or store.new_session_id()

    try:
        ctx = retrieve(req.message)
        answer = chat(req.message, session_id=session_id)
        return ChatResponse(
            answer=answer,
            session_id=session_id,
            source_doc_ids=ctx.source_doc_ids,
        )
    except EmptyMessageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.user_message)
    except InvalidShipmentIdError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.user_message)
    except QueryTooLongError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=exc.user_message)
    except ChatbotError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.user_message)
    except Exception as exc:
        logger.exception("Unexpected error in /api/chat: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request.",
        )


# ── Shipment Endpoints ──────────────────────────────────────────────

@app.get(
    "/api/shipments/{shipment_id}",
    response_model=ShipmentResponse,
    summary="Get single shipment details",
    tags=["shipments"],
)
def api_get_shipment(shipment_id: str):
    try:
        result = get_shipment_by_id(shipment_id.upper())
        return ShipmentResponse(**result.shipment)
    except ShipmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.user_message)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.get(
    "/api/shipments",
    response_model=ShipmentListResponse,
    summary="Filter shipments by status, origin, or destination",
    tags=["shipments"],
)
def api_search_shipments(
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


# ── Health & Diagnostics Endpoints ──────────────────────────────────

@app.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Health check and configuration status",
    tags=["health"],
)
def api_health():
    from logistics_chatbot.rag import ingestion

    groq_ok = bool(config.GROQ_API_KEY and not config.GROQ_API_KEY.startswith("your_"))
    db_ok = bool(config.SUPABASE_DB_URL and "user:password" not in config.SUPABASE_DB_URL)

    try:
        shipment_count = len(ingestion.load_shipment_rows())
    except Exception:
        shipment_count = 0

    try:
        kb_count = len(ingestion.load_kb_rows())
    except Exception:
        kb_count = 0

    return HealthResponse(
        status="healthy",
        groq_model=config.GROQ_MODEL,
        groq_configured=groq_ok,
        supabase_configured=db_ok,
        embedding_model=config.EMBEDDING_MODEL,
        active_dataset_shipments=shipment_count,
        active_dataset_kb_articles=kb_count,
    )


@app.get(
    "/api/vector-db/health",
    summary="ChromaDB vector database health check",
    tags=["health"],
)
def api_vector_db_health():
    """Returns status, connection mode, heartbeat, and chunk count of ChromaDB."""
    return chroma_db.check_chroma_health()
