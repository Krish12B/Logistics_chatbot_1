"""Application chat use-case service mediating between HTTP API and chatbot orchestration."""
from __future__ import annotations

from typing import Iterator, Optional

from logistics_chatbot.application.chatbot import orchestrator
from logistics_chatbot.application.rag import retriever
from logistics_chatbot.core import config
from logistics_chatbot.application.prompts.system_prompt import MAX_QUERY_LENGTH
from logistics_chatbot.core.errors import EmptyMessageError, QueryTooLongError
from logistics_chatbot.domain.entities.models import ChatResult


def process_chat_message(message: str, session_id: Optional[str] = None) -> ChatResult:
    """Process a single synchronous chat turn."""
    if not message or not message.strip():
        raise EmptyMessageError("Message cannot be empty or contain only whitespace.")
    return orchestrator.generate_response(message=message, session_id=session_id)


def stream_chat_message(message: str, session_id: Optional[str] = None) -> Iterator[dict]:
    """Validate and stream SSE-compatible events for a chat turn."""
    if not message or not message.strip():
        raise EmptyMessageError("Message cannot be empty or contain only whitespace.")
    max_len = getattr(config, "QUERY_MAX_LENGTH", MAX_QUERY_LENGTH)
    if len(message) > max_len:
        raise QueryTooLongError(f"Query is too long. Please keep queries under {max_len} characters.")
    return orchestrator.stream_chat_response(message, session_id=session_id)


def process_legacy_api_chat(message: str, session_id: Optional[str] = None) -> dict:
    """Handle legacy /api/chat contract returning answer, session_id, source_doc_ids."""
    store = orchestrator.get_conversation_store()
    sid = session_id or store.new_session_id()
    ctx = retriever.retrieve(message)
    answer = orchestrator.rag_chat(message, session_id=sid)
    return {
        "answer": answer,
        "session_id": sid,
        "source_doc_ids": ctx.source_doc_ids,
    }
