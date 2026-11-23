"""FastAPI dependencies for service injection."""
from __future__ import annotations

from chatbot.bot import generate_response
from database.db import get_shipment_by_id
from rag.search import get_chroma_collection, search_knowledge

def get_chatbot_service():
    """Dependency providing response generation service."""
    return generate_response

def get_database_service():
    """Dependency providing shipment database service."""
    return get_shipment_by_id

def get_search_service():
    """Dependency providing vector search service."""
    return search_knowledge
