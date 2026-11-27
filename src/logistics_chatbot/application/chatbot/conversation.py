"""Conversation and session context management for multi-turn chat sessions."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from logistics_chatbot.core import config
from logistics_chatbot.domain.entities.models import ConversationSession as _DomainSession, Message

logger = logging.getLogger("logistics_chatbot.conversation")


class ConversationSession(_DomainSession):
    """Application-aware conversation session adding shipment ID resolution."""

    def get_last_shipment_id(self) -> Optional[str]:
        """Scan previous messages to find a shipment ID for pronoun resolution."""
        from logistics_chatbot.application.rag.retriever import detect_shipment_id

        for msg in reversed(self.messages):
            sid = detect_shipment_id(msg.content)
            if sid:
                return sid
        return None


class ConversationStore:
    """In-memory session store with automatic TTL expiration."""

    def __init__(self, session_ttl_seconds: Optional[int] = None):
        self._sessions: Dict[str, ConversationSession] = {}
        self.session_ttl_seconds = (
            session_ttl_seconds
            if session_ttl_seconds is not None
            else getattr(config, "SESSION_TTL_SECONDS", 3600)
        )

    def get_or_create(self, session_id: Optional[str] = None) -> ConversationSession:
        """Retrieve an existing session or start a new one."""
        if not session_id:
            session_id = str(uuid.uuid4())

        if session_id in self._sessions:
            session = self._sessions[session_id]
            age = (datetime.now(timezone.utc) - session.last_active).total_seconds()
            if age > self.session_ttl_seconds:
                logger.info("Session %s expired after %ds of inactivity, resetting", session_id, int(age))
                session = ConversationSession(session_id=session_id)
                self._sessions[session_id] = session
            return session

        session = ConversationSession(session_id=session_id)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Optional[ConversationSession]:
        """Return session if active, else None."""
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        """Explicitly end and remove a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self) -> List[str]:
        """Return all active session IDs."""
        return list(self._sessions.keys())

    def cleanup_expired(self) -> int:
        """Purge sessions inactive longer than TTL."""
        now = datetime.now(timezone.utc)
        expired = [
            sid for sid, s in self._sessions.items()
            if (now - s.last_active).total_seconds() > self.session_ttl_seconds
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)

    def new_session_id(self) -> str:
        """Generate a random unique session UUID."""
        return str(uuid.uuid4())


Conversation = ConversationSession
__all__ = ["Conversation", "ConversationSession", "ConversationStore", "Message"]
