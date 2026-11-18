"""Vector stores package (ChromaDB primary, Supabase secondary)."""
from logistics_chatbot.vectorstores.chroma_db import (
    check_chroma_health,
    delete_collection,
    get_chroma_client,
    get_or_create_collection,
    ingest_from_kb,
    query_knowledge_chunks,
    upsert_knowledge_chunks,
)
