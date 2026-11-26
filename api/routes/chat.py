"""Chat route controller for employee questions and AI response generation."""
from __future__ import annotations

import json
import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from api.schemas.request_models import ChatData, ChatRequest, ChatResponse, ErrorResponse
from chatbot.bot import generate_response, stream_chat_response
from logistics_chatbot.core import config
from logistics_chatbot.core.prompts import MAX_QUERY_LENGTH
from logistics_chatbot.core.errors import (
    ChatbotError,
    EmptyMessageError,
    InvalidShipmentIdError,
    LLMAuthError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUnavailableError,
    QueryTooLongError,
)

logger = logging.getLogger("logistics_chatbot.api.chat")
router = APIRouter(tags=["chat"])


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
def handle_chat(request: ChatRequest) -> ChatResponse:
    # Validate non-empty query
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty or contain only whitespace.",
        )

    try:
        chat_res = generate_response(
            message=request.message,
            session_id=request.session_id,
        )
        resp_text = getattr(chat_res, "response", chat_res[0] if isinstance(chat_res, (list, tuple)) else str(chat_res))
        sources_list = getattr(chat_res, "sources", chat_res[1] if isinstance(chat_res, (list, tuple)) and len(chat_res) > 1 else [])
        res_type = getattr(chat_res, "response_type", None)
        shp_id = getattr(chat_res, "shipment_id", None)

        return ChatResponse(
            success=True,
            message="Response generated successfully",
            response=resp_text,
            sources=sources_list,
            data=ChatData(
                query=request.message,
                response=resp_text,
                sources=sources_list,
                response_type=res_type,
                shipment_id=shp_id,
            ),
        )

    except EmptyMessageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.user_message)

    except InvalidShipmentIdError as exc:
        # Invalid format still returns a friendly guidance message with HTTP 200/400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.user_message)

    except QueryTooLongError as exc:
        raise HTTPException(status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413), detail=exc.user_message)

    except (LLMAuthError, LLMRateLimitError, LLMTimeoutError, LLMUnavailableError) as exc:
        logger.error("LLM failure during /chat: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service temporarily unavailable: {exc.user_message}",
        )

    except ChatbotError as exc:
        logger.error("Chatbot operational error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.user_message,
        )

    except Exception as exc:
        logger.exception("Unexpected exception in /chat endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the response.",
        )


@router.post(
    "/chat/stream",
    summary="Ask a logistics question with progressive Server-Sent Events (SSE) streaming",
    description="Streams LLM tokens progressively for minimum latency and zero waiting buffer.",
)
async def handle_chat_stream(request: ChatRequest):
    # Validate non-empty query
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty or contain only whitespace.",
        )

    max_len = getattr(config, "QUERY_MAX_LENGTH", MAX_QUERY_LENGTH)
    if len(request.message) > max_len:
        raise HTTPException(
            status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
            detail=f"Query is too long. Please keep queries under {max_len} characters.",
        )

    def event_generator():
        try:
            for event in stream_chat_response(request.message, session_id=request.session_id):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            logger.error("Streaming error: %s", exc)
            err_event = {
                "done": True,
                "response": "An operational error occurred while streaming the answer. Please try again.",
                "sources": [],
                "response_type": "error",
            }
            yield f"data: {json.dumps(err_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
