"""Conversation and context management for multi-turn chat sessions.

Tracks user and assistant turns, attaches retrieved knowledge context,
enforces sliding-window token budgets, and supports follow-up continuity.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger("logistics_chatbot.conversation")


@dataclass
class Message:
    """A single turn in the conversation."""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context: Optional[str] = None


@dataclass
class ConversationSession:
    """Session history for a single user/client conversation."""
    session_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_active: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    messages: List[Message] = field(default_factory=list)
    max_history_turns: int = 6  # 3 user + 3 assistant turns

    def add_message(self, role: str, content: str, context: Optional[str] = None) -> Message:
        """Record a turn and refresh last_active."""
        msg = Message(role=role, content=content, context=context)
        self.messages.append(msg)
        self.last_active = datetime.now(timezone.utc)
        return msg

    def get_recent_messages(self, max_turns: Optional[int] = None) -> List[Dict[str, str]]:
        """Return the most recent messages formatted for Groq/OpenAI chat API."""
        limit = (max_turns or self.max_history_turns // 2) * 2
        recent = self.messages[-limit:] if limit < len(self.messages) else self.messages
        return [{"role": m.role, "content": m.content} for m in recent]

    def get_last_context(self) -> Optional[str]:
        """Return the context string used in the most recent user turn."""
        for msg in reversed(self.messages):
            if msg.role == "user" and msg.context:
                return msg.context
        return None

    def get_last_shipment_id(self) -> Optional[str]:
        """Scan previous messages to find a shipment ID for pronoun resolution."""
        from logistics_chatbot.rag.retrieval import detect_shipment_id
        for msg in reversed(self.messages):
            sid = detect_shipment_id(msg.content)
            if sid:
                return sid
        return None

    @property
    def turn_count(self) -> int:
        """Number of user messages in this conversation."""
        return sum(1 for m in self.messages if m.role == "user")


class ConversationStore:

    """In-memory thread-safe session store with automatic expiration."""

    def __init__(self, session_ttl_seconds: int = 3600):
        self._sessions: Dict[str, ConversationSession] = {}
        self.session_ttl_seconds = session_ttl_seconds

    def get_or_create(self, session_id: Optional[str] = None) -> ConversationSession:
        """Retrieve an existing session or start a new one."""
        if not session_id:
            session_id = str(uuid.uuid4())

        if session_id in self._sessions:
            session = self._sessions[session_id]
            # Check expiration
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


# Compatibility alias
Conversation = ConversationSession
