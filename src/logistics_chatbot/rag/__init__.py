"""RAG (Retrieval-Augmented Generation) package."""
from logistics_chatbot.rag.embeddings import embed_query, embed_texts
from logistics_chatbot.rag.ingestion import (
    load_kb_rows,
    load_shipment_rows,
    sync_knowledge,
    sync_shipments,
)
from logistics_chatbot.rag.knowledge_base import fetch_matches, search_knowledge_base
from logistics_chatbot.rag.retrieval import (
    classify_query,
    detect_shipment_id,
    format_context,
    format_shipment,
    get_shipment_by_id,
    retrieve,
    search_knowledge,
    search_shipments,
)
