"""FastAPI dependency providers connecting HTTP handlers to application services."""
from __future__ import annotations

from functools import lru_cache
from typing import Dict

from logistics_chatbot.application.chatbot import orchestrator
from logistics_chatbot.application.chatbot.conversation import ConversationStore
from logistics_chatbot.core import config


@lru_cache(maxsize=1)
def get_app_settings() -> config.SettingsSnapshot:
    """Provide cached configuration settings snapshot."""
    return config.get_settings()


def get_conversation_store() -> ConversationStore:
    """Provide the shared conversation session store."""
    return orchestrator.get_conversation_store()


def get_api_endpoints() -> Dict[str, str]:
    """Return catalog of primary public HTTP endpoints."""
    return {
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "chat": "POST /chat",
        "chat_stream": "POST /chat/stream",
        "shipment": "GET /shipment/{id}",
        "shipments_search": "GET /api/shipments",
        "employee": "GET /employee/{id}",
        "employees": "GET /employees",
        "upload_doc": "POST /upload-doc",
        "vector_db_health": "GET /api/vector-db/health",
    }
