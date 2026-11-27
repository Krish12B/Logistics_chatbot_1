"""Application document ingestion and vector knowledge service."""
from __future__ import annotations

from typing import Any, Dict

from logistics_chatbot.application.ingestion.csv_processor import process_csv_upload
from logistics_chatbot.application.ingestion.document_processor import SUPPORTED_EXTENSIONS, process_document
from logistics_chatbot.application.rag.hybrid_search import get_vector_db_health, index_document_chunks


def ingest_uploaded_file(filename: str, content_bytes: bytes) -> Dict[str, Any]:
    """Ingest an uploaded CSV or unstructured document (.txt, .pdf, .docx)."""
    if filename.lower().endswith(".csv"):
        csv_result = process_csv_upload(filename=filename, content_bytes=content_bytes)
        return {
            "kind": "csv",
            "payload": csv_result,
        }

    chunks, doc_id = process_document(filename=filename, content=content_bytes)
    indexed_count = index_document_chunks(chunks)
    return {
        "kind": "document",
        "doc_id": doc_id,
        "chunks_created": indexed_count,
        "filename": filename,
    }


def vector_store_health() -> Dict[str, Any]:
    """Return ChromaDB vector store health metrics."""
    return get_vector_db_health()


__all__ = [
    "SUPPORTED_EXTENSIONS",
    "get_vector_db_health",
    "index_document_chunks",
    "ingest_uploaded_file",
    "process_csv_upload",
    "process_document",
    "vector_store_health",
]
