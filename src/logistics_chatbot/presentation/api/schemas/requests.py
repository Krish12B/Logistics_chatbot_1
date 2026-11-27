"""HTTP request models."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Payload for chat endpoints (/chat, /chat/stream, /api/chat)."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Employee query or instruction",
        json_schema_extra={"examples": ["What is the delivery process for international shipments?"]},
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for multi-turn conversation memory",
    )

    @field_validator("message")
    @classmethod
    def _reject_blank_message(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Message cannot be empty or whitespace only.")
        return value
