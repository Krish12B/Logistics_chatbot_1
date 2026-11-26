"""FastAPI application entry point for the Logistics AI Chatbot backend.

Exposes:
  - GET  /health          - API health check
  - POST /chat            - Submit user question, returns grounded answer & sources
  - GET  /shipment/{id}   - Lookup shipment details by ID
  - POST /upload-doc      - Upload and index .txt knowledge documents into ChromaDB
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure project root and src/ are in sys.path
_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response

from api.routes.chat import router as chat_router
from api.routes.employee import router as employee_router
from api.routes.shipment import router as shipment_router
from api.routes.upload import router as upload_router
from api.schemas.request_models import HealthResponse
from api.web_ui import LANDING_PAGE_HTML
from logistics_chatbot.core import config
from logistics_chatbot.vectorstores import chroma_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("logistics_chatbot.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: verify ChromaDB on startup, clean up on shutdown."""
    logger.info("Initializing Logistics AI Chatbot backend...")
    try:
        chroma_db.get_chroma_collection()
        logger.info("ChromaDB vector store connection verified.")
    except Exception as exc:
        logger.warning("ChromaDB initialization notice: %s", exc)
    yield
    logger.info("Shutting down Logistics AI Chatbot API...")


app = FastAPI(
    title="Logistics AI Chatbot API",
    description=(
        "Production-ready FastAPI backend for Logistics RAG Chatbot. "
        "Integrates Groq LLM, ChromaDB vector store, shipment database, and document ingestion."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Centralized Exception Handlers ───────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Standardize HTTP errors into consistent JSON format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
            "data": None,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Standardize 422 Pydantic validation errors."""
    error_messages = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        error_messages.append(f"{loc}: {msg}")

    return JSONResponse(
        status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        content={
            "success": False,
            "message": "Invalid request structure",
            "data": {"errors": error_messages},
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Safely catch unhandled errors without leaking stack traces or credentials."""
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error occurred while processing request.",
            "data": None,
        },
    )


# ── Root Landing Page & Health Check ─────────────────────────────────

@app.get(
    "/",
    summary="Web Chat UI & API Landing Page",
    tags=["system"],
)
def root_endpoint(request: Request):
    """Serve the interactive web chat UI when viewed in a browser, or API catalog for JSON."""
    accept = request.headers.get("accept", "").lower()
    if "application/json" in accept and "text/html" not in accept:
        return JSONResponse(
            content={
                "success": True,
                "message": "Logistics AI Chatbot API is online. Visit /docs for Swagger UI.",
                "data": {
                    "docs": "/docs",
                    "redoc": "/redoc",
                    "health": "/health",
                    "chat": "POST /chat",
                    "shipment": "GET /shipment/{id}",
                    "employee": "GET /employee/{id}",
                    "employees": "GET /employees",
                    "upload_doc": "POST /upload-doc",
                },
            }
        )
    return HTMLResponse(content=LANDING_PAGE_HTML)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service availability status.",
    tags=["system"],
)
def health_check() -> HealthResponse:
    return HealthResponse(
        success=True,
        message="Logistics AI Chatbot API is running",
    )


# ── Router Registration ──────────────────────────────────────────────

app.include_router(chat_router)
app.include_router(shipment_router)
app.include_router(employee_router)
app.include_router(upload_router)

# Also include existing modular routes under /api for full backward compatibility
# (core_shipments_router already sets prefix="/api" internally)
from logistics_chatbot.api.routes.shipments import router as core_shipments_router
app.include_router(core_shipments_router)


@app.get(
    "/api/vector-db/health",
    summary="ChromaDB status",
    tags=["system"],
)
def vector_db_health():
    """Return health details of the ChromaDB vector database."""
    from rag.search import get_vector_db_health
    return get_vector_db_health()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
