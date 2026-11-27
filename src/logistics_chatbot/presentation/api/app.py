"""FastAPI application factory assembling routers, static files, middleware, and error handlers."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from logistics_chatbot.core import config
from logistics_chatbot.core.logging import configure_logging, get_logger
from logistics_chatbot.presentation.api.routes import (
    chat,
    documents,
    employees,
    health,
    shipments,
    web,
)

configure_logging()
logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize logging and verify core storage readiness at startup."""
    logger.info("Starting NexusFreight / FleetHarbor Logistics AI Chatbot API...")
    try:
        from logistics_chatbot.infrastructure.database.connection import resolve_sqlite_db_path

        db_path = resolve_sqlite_db_path()
        if db_path is not None:
            logger.info("SQLite database ready: %s", db_path)
        else:
            logger.warning("SQLite database not found at %s; CSV fallback active", config.DB_PATH)
    except Exception as exc:
        logger.warning("Database startup probe warning: %s", exc)

    try:
        from logistics_chatbot.infrastructure.vector_store.chroma_store import get_chroma_collection

        coll = get_chroma_collection()
        logger.info("ChromaDB collection ready (%s chunks)", coll.count())
    except Exception as exc:
        logger.warning("ChromaDB startup probe warning: %s", exc)

    yield
    logger.info("Shutting down NexusFreight / FleetHarbor Logistics AI Chatbot API.")


def create_app() -> FastAPI:
    """Create and configure the canonical FastAPI application."""
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if config.STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": str(exc.detail), "data": None},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Invalid request structure",
                "data": {"errors": jsonable_encoder(exc.errors())},
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error occurred while processing request.",
                "data": None,
            },
        )

    app.include_router(web.router)
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(shipments.router)
    app.include_router(employees.router)
    app.include_router(documents.router)

    return app


app = create_app()
