"""Chat API routes."""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status

from logistics_chatbot.chatbot.chatbot import chat, get_conversation_store
from logistics_chatbot.core.errors import (
    ChatbotError,
    EmptyMessageError,
    InvalidShipmentIdError,
    QueryTooLongError,
)
from logistics_chatbot.rag.retrieval import retrieve
from logistics_chatbot.schemas.models import ChatRequest, ChatResponse

logger = logging.getLogger("logistics_chatbot.api.chat")

router = APIRouter(prefix="/api", tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask a logistics question",
    description="Answers tracking, delay, customs, and policy questions using grounded logistics knowledge.",
)
def api_chat(req: ChatRequest):
    store = get_conversation_store()
    session_id = req.session_id or store.new_session_id()

    try:
        ctx = retrieve(req.message)
        answer = chat(req.message, session_id=session_id)
        return ChatResponse(
            answer=answer,
            session_id=session_id,
            source_doc_ids=ctx.source_doc_ids,
        )
    except EmptyMessageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.user_message)
    except InvalidShipmentIdError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.user_message)
    except QueryTooLongError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=exc.user_message)
    except ChatbotError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.user_message)
    except Exception as exc:
        logger.exception("Unexpected error in /api/chat: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request.",
        )
