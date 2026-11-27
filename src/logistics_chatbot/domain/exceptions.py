"""Domain exceptions re-exported independently of infrastructure frameworks."""
from logistics_chatbot.core.errors import (
    ChatbotError,
    DatabaseError,
    DocumentProcessingError,
    EmptyMessageError,
    InvalidFileFormatError,
    InvalidShipmentIdError,
    KnowledgeBaseError,
    LLMAuthError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUnavailableError,
    QueryTooLongError,
    ShipmentNotFoundError,
    VectorDBError,
)

__all__ = [
    "ChatbotError",
    "DatabaseError",
    "DocumentProcessingError",
    "EmptyMessageError",
    "InvalidFileFormatError",
    "InvalidShipmentIdError",
    "KnowledgeBaseError",
    "LLMAuthError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMUnavailableError",
    "QueryTooLongError",
    "ShipmentNotFoundError",
    "VectorDBError",
]
