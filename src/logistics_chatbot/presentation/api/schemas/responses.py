"""HTTP response models preserving all API contracts."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error envelope returned on 4xx/5xx errors."""

    success: bool = False
    message: str
    data: Any = None


class HealthResponse(BaseModel):
    """Response model for GET /health."""

    success: bool = True
    message: str = "Logistics AI Chatbot API is running"


class LegacyHealthResponse(BaseModel):
    """Response model for GET /api/health."""

    status: str
    groq_model: str
    groq_configured: bool
    supabase_configured: bool
    embedding_model: str
    active_dataset_shipments: int
    active_dataset_kb_articles: int


class ChatData(BaseModel):
    """Nested data payload for POST /chat."""

    query: str = Field(..., description="The user query processed")
    response: str = Field(..., description="AI-generated response grounded in knowledge base")
    sources: List[str] = Field(default_factory=list, description="IDs of knowledge base sources cited")
    response_type: Optional[str] = Field(default=None, description="Query type classification")
    shipment_id: Optional[str] = Field(default=None, description="Detected shipment ID if applicable")


class ChatResponse(BaseModel):
    """Envelope response for POST /chat."""

    success: bool = True
    message: str = "Response generated successfully"
    data: ChatData
    response: Optional[str] = Field(default=None, description="Top-level alias for data.response")
    sources: List[str] = Field(default_factory=list, description="Top-level alias for data.sources")


class LegacyChatResponse(BaseModel):
    """Legacy response contract for POST /api/chat."""

    answer: str
    reply: str = ""
    session_id: str
    source_doc_ids: List[str] = Field(default_factory=list)


class ShipmentEnvelopeResponse(BaseModel):
    """Envelope response for GET /shipment/{id}."""

    success: bool = True
    message: str = "Shipment retrieved successfully"
    data: Optional[Dict[str, Any]] = None


class ShipmentRecordResponse(BaseModel):
    """Typed shipment payload for /api/shipments endpoints."""

    shipment_id: str
    origin: str
    destination: str
    status: str
    current_location: Optional[str] = None
    route: Optional[str] = None
    estimated_delivery: Optional[str] = None
    delay_reason: Optional[str] = None
    customs_status: Optional[str] = None
    last_updated: Optional[str] = None


class ShipmentListResponse(BaseModel):
    """Filtered list payload for GET /api/shipments."""

    total_count: int
    filter_description: str
    shipments: List[ShipmentRecordResponse]


class DocUploadData(BaseModel):
    """Nested metadata payload for POST /upload-doc."""

    filename: str
    chunks_created: int = 0
    status: str = "Indexed Successfully"
    total_records: Optional[int] = None
    imported: Optional[int] = None
    skipped: Optional[int] = None
    failed: Optional[int] = None
    category: Optional[str] = None
    summary: Optional[str] = None


class DocUploadResponse(BaseModel):
    """Envelope response for POST /upload-doc."""

    success: bool = True
    message: str = "Document uploaded successfully"
    data: DocUploadData
    summary: Optional[str] = None
