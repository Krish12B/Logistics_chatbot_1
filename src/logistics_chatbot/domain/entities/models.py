"""Pure domain entities and value objects (independent of frameworks, DBs, or LLMs)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class LogisticsIntent(str, Enum):
    SHIPMENT_TRACKING = "shipment_tracking"
    SHIPMENT_INFO = "shipment_info"
    DELIVERY_UPDATES = "delivery_updates"
    COMPANY_POLICY = "company_policy"
    LOGISTICS_PROCESS = "logistics_process"
    DOCUMENTATION = "documentation"
    EMPLOYEE_SUPPORT = "employee_support"
    OPERATIONAL_ISSUES = "operational_issues"
    OPERATIONAL_STATUS = "operational_status"
    GENERAL_CONVERSATION = "general_conversation"
    UNSUPPORTED_OFFTOPIC = "unsupported_offtopic"
    CLARIFICATION_REQUIRED = "clarification_required"


class QueryType(Enum):
    SHIPMENT_LOOKUP = auto()
    SHIPMENT_FILTER = auto()
    KNOWLEDGE_SEARCH = auto()
    MIXED = auto()


@dataclass
class ClassifiedIntent:
    """Detailed intent analysis result."""
    intent: LogisticsIntent
    confidence: float
    preferred_source: str
    shipment_id: Optional[str] = None
    booking_id: Optional[str] = None
    employee_id: Optional[str] = None
    operational_id: Optional[str] = None
    resolved_reference: bool = False
    target_attribute: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryIntent:
    """Retrieval-layer query classification result."""
    query_type: QueryType
    shipment_id: Optional[str] = None
    status_filter: Optional[str] = None
    origin_filter: Optional[str] = None
    destination_filter: Optional[str] = None
    raw_query: str = ""


@dataclass
class ShipmentResult:
    """Container for a single shipment record."""
    shipment: dict
    source: str = "shipments"


@dataclass
class ShipmentListResult:
    """Container for a filtered list of shipments."""
    shipments: List[dict] = field(default_factory=list)
    total_count: int = 0
    filter_description: str = ""
    source: str = "shipments"


@dataclass
class KnowledgeResult:
    """Container for retrieved knowledge base articles."""
    articles: List[dict] = field(default_factory=list)
    source: str = "knowledge_base"


@dataclass
class RetrievedContext:
    """Complete context package for LLM prompt construction."""
    intent: QueryIntent
    shipment: Optional[dict] = None
    shipment_list: Optional[List[dict]] = None
    filter_description: str = ""
    knowledge_articles: List[dict] = field(default_factory=list)
    source_doc_ids: List[str] = field(default_factory=list)


@dataclass
class Message:
    """A single turn in a conversation."""
    role: str
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
        """Return the most recent messages formatted for LLM chat completion."""
        limit = (max_turns or self.max_history_turns // 2) * 2
        recent = self.messages[-limit:] if limit < len(self.messages) else self.messages
        return [{"role": m.role, "content": m.content} for m in recent]

    def get_last_context(self) -> Optional[str]:
        """Return the context string used in the most recent user turn."""
        for msg in reversed(self.messages):
            if msg.role == "user" and msg.context:
                return msg.context
        return None

    @property
    def turn_count(self) -> int:
        """Number of user messages in this conversation."""
        return sum(1 for m in self.messages if m.role == "user")


class ChatResult:
    """Structured response container maintaining backward-compatible 2-element tuple unpacking."""

    def __init__(
        self,
        response: str,
        sources: List[str],
        response_type: str = "general_knowledge",
        shipment_id: Optional[str] = None,
        structured_data: Optional[Dict[str, Any]] = None,
    ):
        self.response = response
        self.sources = sources
        self.response_type = response_type
        self.shipment_id = shipment_id
        self.structured_data = structured_data or {}

    def __iter__(self):
        yield self.response
        yield self.sources

    def __getitem__(self, idx: int):
        if idx == 0:
            return self.response
        if idx == 1:
            return self.sources
        raise IndexError("ChatResult index out of range (supports 0: response, 1: sources)")

    def __repr__(self) -> str:
        return f"<ChatResult type={self.response_type} shipment_id={self.shipment_id} sources={len(self.sources)}>"
