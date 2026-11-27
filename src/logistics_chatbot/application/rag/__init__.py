"""Application RAG package."""
from logistics_chatbot.application.rag.context_builder import (
    format_context,
    format_enterprise_shipment_context,
    format_shipment,
)
from logistics_chatbot.application.rag.hybrid_search import (
    get_chroma_collection,
    get_vector_db_health,
    index_document_chunks,
    search_knowledge as search_knowledge_hybrid,
)
from logistics_chatbot.application.rag.retriever import (
    classify_query,
    detect_booking_id,
    detect_shipment_id,
    get_shipment_by_id,
    retrieve,
    search_knowledge,
    search_shipments,
)

__all__ = [
    "classify_query",
    "detect_booking_id",
    "detect_shipment_id",
    "format_context",
    "format_enterprise_shipment_context",
    "format_shipment",
    "get_chroma_collection",
    "get_shipment_by_id",
    "get_vector_db_health",
    "index_document_chunks",
    "retrieve",
    "search_knowledge",
    "search_knowledge_hybrid",
    "search_shipments",
]
