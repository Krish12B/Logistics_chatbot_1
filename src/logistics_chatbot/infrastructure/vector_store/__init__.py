"""Vector store infrastructure package."""
from logistics_chatbot.infrastructure.vector_store.chroma_store import (
    check_chroma_health,
    close,
    delete_collection,
    delete_document_chunks,
    get_chroma_client,
    get_chroma_collection,
    get_or_create_collection,
    ingest_from_kb,
    query_knowledge_chunks,
    upsert_knowledge_chunks,
)
from logistics_chatbot.infrastructure.vector_store.pgvector_store import (
    fetch_matches,
    search_knowledge_base,
)

__all__ = [
    "check_chroma_health",
    "close",
    "delete_collection",
    "delete_document_chunks",
    "fetch_matches",
    "get_chroma_client",
    "get_chroma_collection",
    "get_or_create_collection",
    "ingest_from_kb",
    "query_knowledge_chunks",
    "search_knowledge_base",
    "upsert_knowledge_chunks",
]
