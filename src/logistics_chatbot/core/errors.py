"""Custom error classes for FleetHarbor Logistics AI Chatbot.

Every error has two messages:
  * user_message - friendly text safe to show to the customer / API client
  * detail       - technical text written to internal logs only
"""
from __future__ import annotations


class ChatbotError(Exception):
    default_message = "Sorry, something went wrong. Please try again."

    def __init__(self, user_message=None, detail=""):
        self.user_message = user_message or self.default_message
        self.detail = detail
        super().__init__(self.user_message)


class EmptyMessageError(ChatbotError):
    default_message = (
        "Please type a question about your shipment, for example: "
        "'What is the status of SHP-10001?'"
    )


class QueryTooLongError(ChatbotError):
    default_message = "Your question is too long. Please keep questions under 2,000 characters."


class InvalidShipmentIdError(ChatbotError):
    default_message = (
        "That doesn't look like a valid shipment ID. IDs look like SHP-10001 "
        "(the letters SHP, a dash, then 5 digits)."
    )


class ShipmentNotFoundError(ChatbotError):
    default_message = "I couldn't find that shipment. Please check the ID and try again."


class DatabaseError(ChatbotError):
    default_message = "I can't reach our shipment database right now. Please try again shortly."


class KnowledgeBaseError(ChatbotError):
    default_message = "I'm having trouble loading our help articles right now. Please try again shortly."


class VectorDBError(KnowledgeBaseError):
    default_message = "I'm having trouble loading our vector knowledge base right now. Please try again shortly."


class LLMTimeoutError(ChatbotError):
    default_message = "The assistant took too long to respond. Please try again in a moment."


class LLMAuthError(ChatbotError):
    default_message = (
        "The assistant is not set up correctly (the API key is missing or invalid). "
        "Please contact the administrator."
    )


class LLMRateLimitError(ChatbotError):
    default_message = "The assistant is very busy right now. Please try again in a few seconds."


class LLMUnavailableError(ChatbotError):
    default_message = "The assistant is temporarily unavailable. Please try again later."
