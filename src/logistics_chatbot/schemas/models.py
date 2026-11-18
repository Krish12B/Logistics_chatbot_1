"""Pydantic data models and schemas for API requests and responses."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User's question or message")
    session_id: Optional[str] = Field(None, description="Optional conversation session ID for multi-turn context")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded plain-English response")
    reply: Optional[str] = Field(None, description="Alias for answer for backwards compatibility")
    session_id: str = Field(..., description="Conversation session ID")
    source_doc_ids: List[str] = Field(default_factory=list, description="IDs of knowledge base documents cited")

    def __init__(self, **data):
        if "answer" in data and ("reply" not in data or data["reply"] is None):
            data["reply"] = data["answer"]
        elif "reply" in data and ("answer" not in data or data["answer"] is None):
            data["answer"] = data["reply"]
        super().__init__(**data)


class ShipmentResponse(BaseModel):
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
    total_count: int
    filter_description: str
    shipments: List[ShipmentResponse]


class HealthResponse(BaseModel):
    status: str
    groq_model: str
    groq_configured: bool
    supabase_configured: bool
    embedding_model: str
    active_dataset_shipments: int
    active_dataset_kb_articles: int


class VectorHealthResponse(BaseModel):
    status: str
    mode: str
    heartbeat: Optional[int] = None
    collection_name: str
    record_count: Optional[int] = None
    persist_directory: Optional[str] = None
    error: Optional[str] = None
