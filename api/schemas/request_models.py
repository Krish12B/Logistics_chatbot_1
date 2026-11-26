"""Pydantic data models and response schemas matching project API contracts."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ── Request Models ──────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Employee query or instruction",
        examples=["What is the delivery process for international shipments?"],
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID for multi-turn conversation memory",
    )

    @field_validator("message")
    @classmethod
    def validate_non_whitespace(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or contain only whitespace.")
        return v.strip()


# ── Response Data Models ────────────────────────────────────────────

class ChatData(BaseModel):
    query: str = Field(..., description="The user query processed")
    response: str = Field(..., description="AI-generated response grounded in knowledge base")
    sources: List[str] = Field(default_factory=list, description="IDs of knowledge base sources cited")
    response_type: Optional[str] = Field(None, description="Query type classification")
    shipment_id: Optional[str] = Field(None, description="Detected shipment ID if applicable")


class ChatResponse(BaseModel):
    success: bool = True
    message: str = "Response generated successfully"
    data: ChatData
    response: Optional[str] = Field(None, description="Top-level alias for data.response")
    sources: List[str] = Field(default_factory=list, description="Top-level alias for data.sources")


class ShipmentResponse(BaseModel):
    success: bool = True
    message: str = "Shipment retrieved successfully"
    data: Optional[Dict[str, Any]] = None


class DocUploadData(BaseModel):
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
    success: bool = True
    message: str = "Document uploaded successfully"
    data: DocUploadData
    summary: Optional[str] = None


class HealthResponse(BaseModel):
    success: bool = True
    message: str = "Logistics AI Chatbot API is running"


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    data: Optional[Any] = None
