"""Chat routes supporting synchronous, SSE streaming, and legacy /api/chat contracts."""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from logistics_chatbot.application.services import chat_service
from logistics_chatbot.core.errors import (
    ChatbotError,
    EmptyMessageError,
    InvalidShipmentIdError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUnavailableError,
    QueryTooLongError,
)
from logistics_chatbot.presentation.api.schemas.requests import ChatRequest
from logistics_chatbot.presentation.api.schemas.responses import (
    ChatData,
    ChatResponse,
    ErrorResponse,
    LegacyChatResponse,
)

logger = logging.getLogger("logistics_chatbot.api.chat")
router = APIRouter(tags=["chat"])


def _map_chatbot_http_error(exc: ChatbotError) -> HTTPException:
    """Translate domain ChatbotError to legacy HTTP status codes without leaking exc.detail."""
    if isinstance(exc, (EmptyMessageError, InvalidShipmentIdError)):
        return HTTPException(status_code=400, detail=exc.user_message)
    if isinstance(exc, QueryTooLongError):
        return HTTPException(status_code=413, detail=exc.user_message)
    if isinstance(exc, LLMRateLimitError):
        logger.warning("LLM rate limit encountered: %s", exc.detail or exc.user_message)
        return HTTPException(status_code=500, detail=exc.user_message)
    if isinstance(exc, (LLMTimeoutError, LLMUnavailableError)):
        logger.warning("LLM unavailable/timeout encountered: %s", exc.detail or exc.user_message)
        return HTTPException(status_code=500, detail="AI service temporarily unavailable. Please try again shortly.")
    logger.error("Chatbot error encountered: %s", exc.detail or exc.user_message)
    return HTTPException(status_code=500, detail=exc.user_message)


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Empty or invalid message"},
        413: {"model": ErrorResponse, "description": "Query too long"},
        500: {"model": ErrorResponse, "description": "Internal server or LLM error"},
    },
    summary="Ask an employee logistics question",
    description="Processes employee queries using the RAG pipeline, ChromaDB vector knowledge base, and Groq LLM.",
)
async def handle_chat(request: ChatRequest):
    """Process an employee chat turn and return structured response + sources."""
    try:
        result = chat_service.process_chat_message(
            message=request.message,
            session_id=request.session_id,
        )
        if isinstance(result, tuple):
            ans_text, src_list = result[0], result[1] if len(result) > 1 else []
            resp_type, sid = None, None
        else:
            ans_text = result.response
            src_list = result.sources
            resp_type = result.response_type
            sid = result.shipment_id
        return ChatResponse(
            success=True,
            message="Response generated successfully",
            data=ChatData(
                query=request.message.strip(),
                response=ans_text,
                sources=src_list,
                response_type=resp_type,
                shipment_id=sid,
            ),
            response=ans_text,
            sources=src_list,
        )
    except ChatbotError as exc:
        raise _map_chatbot_http_error(exc)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error processing chat request: %s", exc)
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing your message.")


@router.post(
    "/chat/stream",
    summary="Ask a logistics question with progressive Server-Sent Events (SSE) streaming",
    description="Streams LLM tokens progressively for minimum latency and zero waiting buffer.",
)
async def handle_chat_stream(request: ChatRequest):
    """Stream SSE JSON events for progressive UI rendering."""
    try:
        event_iter = chat_service.stream_chat_message(
            message=request.message,
            session_id=request.session_id,
        )
    except ChatbotError as exc:
        raise _map_chatbot_http_error(exc)

    def event_generator():
        try:
            for event in event_iter:
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            logger.exception("Error during SSE stream generation: %s", exc)
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/api/chat", response_model=LegacyChatResponse, summary="Legacy chat endpoint")
async def legacy_chat(request: ChatRequest):
    """Handle legacy /api/chat requests preserving answer, session_id, and source_doc_ids."""
    try:
        payload = chat_service.process_legacy_api_chat(
            message=request.message,
            session_id=request.session_id,
        )
        return LegacyChatResponse(
            answer=payload["answer"],
            reply=payload["answer"],
            session_id=payload["session_id"],
            source_doc_ids=payload["source_doc_ids"],
        )
    except ChatbotError as exc:
        raise _map_chatbot_http_error(exc)
    except Exception as exc:
        logger.exception("Error processing /api/chat request: %s", exc)
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing your message.")
