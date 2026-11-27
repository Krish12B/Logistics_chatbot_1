"""PostgreSQL pgvector knowledge base search via Supabase RPC match_knowledge."""
from __future__ import annotations

import logging
from typing import Optional

from logistics_chatbot.core import config
from logistics_chatbot.core.errors import KnowledgeBaseError
from logistics_chatbot.infrastructure.database.repository import run_query
from logistics_chatbot.infrastructure.embeddings.sentence_transformer import embed_query
from logistics_chatbot.utils.helpers import to_pgvector

logger = logging.getLogger("logistics_chatbot.knowledge_base")


def fetch_matches(
    query_vector,
    top_k: Optional[int] = None,
    min_score: Optional[float] = None,
) -> list[dict]:
    """Semantic search over knowledge_base table in PostgreSQL pgvector."""
    if top_k is None:
        top_k = config.RETRIEVAL_TOP_K
    if min_score is None:
        min_score = config.RETRIEVAL_MIN_SCORE

    if not config.SUPABASE_DB_URL:
        return []

    try:
        if isinstance(query_vector, list):
            vec_str = to_pgvector(query_vector)
        else:
            raise KnowledgeBaseError(detail="fetch_matches requires a dense vector (list of floats)")

        rows = run_query(
            "SELECT * FROM match_knowledge(%s::vector, %s, %s)",
            (vec_str, min_score, top_k),
        )
        return [
            {
                "doc_id": row.get("doc_id", ""),
                "category": row.get("category", ""),
                "section_title": row.get("section_title", ""),
                "content": row.get("content", ""),
                "score": float(row.get("similarity", 0)),
            }
            for row in rows
        ]
    except KnowledgeBaseError:
        raise
    except Exception as exc:
        raise KnowledgeBaseError(detail=f"Knowledge base search failed: {exc}") from exc


def search_knowledge_base(question: str, top_k: Optional[int] = None, min_score: Optional[float] = None) -> list[str]:
    """Embed question and return formatted knowledge base matches."""
    query_vector = embed_query(question)
    matches = fetch_matches(query_vector, top_k=top_k, min_score=min_score)
    return [f"[{m['doc_id']}] {m['section_title']}: {m['content']}" for m in matches]
