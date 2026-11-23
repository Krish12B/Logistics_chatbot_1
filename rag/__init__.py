"""RAG retrieval, search, embeddings, and document processing."""
from rag.embeddings import embed_query, embed_texts
from rag.search import get_chroma_collection, index_document_chunks, search_knowledge, get_vector_db_health
from rag.document_processor import process_txt_document, split_text_into_chunks

__all__ = [
    "embed_query",
    "embed_texts",
    "get_chroma_collection",
    "index_document_chunks",
    "search_knowledge",
    "get_vector_db_health",
    "process_txt_document",
    "split_text_into_chunks",
]
