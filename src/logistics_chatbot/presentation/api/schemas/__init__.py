"""Pydantic request and response schemas for the Logistics AI Chatbot HTTP API."""
from logistics_chatbot.presentation.api.schemas.requests import ChatRequest
from logistics_chatbot.presentation.api.schemas.responses import (
    ChatData,
    ChatResponse,
    DocUploadData,
    DocUploadResponse,
    ErrorResponse,
    HealthResponse,
    LegacyChatResponse,
    LegacyHealthResponse,
    ShipmentEnvelopeResponse,
    ShipmentListResponse,
    ShipmentRecordResponse,
)

__all__ = [
    "ChatData",
    "ChatRequest",
    "ChatResponse",
    "DocUploadData",
    "DocUploadResponse",
    "ErrorResponse",
    "HealthResponse",
    "LegacyChatResponse",
    "LegacyHealthResponse",
    "ShipmentEnvelopeResponse",
    "ShipmentListResponse",
    "ShipmentRecordResponse",
]
