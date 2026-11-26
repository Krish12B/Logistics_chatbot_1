"""Search and vector database module: ChromaDB connection, document indexing, and semantic retrieval."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from logistics_chatbot.core import config
from logistics_chatbot.core.errors import KnowledgeBaseError, VectorDBError
from logistics_chatbot.vectorstores import chroma_db
from rag.embeddings import embed_query, embed_texts

logger = logging.getLogger("logistics_chatbot.search")


def get_chroma_collection():
    """Retrieve the primary ChromaDB collection for logistics knowledge chunks."""
    return chroma_db.get_or_create_collection()


def index_document_chunks(chunks: List[Dict[str, Any]]) -> int:
    """Index processed document chunks into ChromaDB with embeddings and metadata.

    Args:
        chunks: List of dictionaries each containing 'chunk_id', 'text', and 'metadata'.

    Returns:
        Number of chunks successfully indexed.
    """
    if not chunks:
        return 0

    collection = get_chroma_collection()

    ids = [c["chunk_id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    # Generate embeddings for the batch of chunks
    embeddings = embed_texts(texts)

    try:
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        logger.info("Indexed %d document chunks into ChromaDB", len(chunks))
        return len(chunks)
    except Exception as exc:
        logger.error("Failed to index chunks into ChromaDB: %s", exc)
        raise VectorDBError(detail=f"ChromaDB indexing error: {exc}") from exc


def search_knowledge(
    query: str,
    top_k: Optional[int] = None,
    min_score: Optional[float] = None,
    category: Optional[str] = None,
    enable_hybrid: bool = True,
) -> List[Dict[str, Any]]:
    """Perform hybrid (dense semantic + lexical keyword) vector search in ChromaDB.

    Args:
        query: Query text.
        top_k: Max results.
        min_score: Minimum cosine similarity threshold.
        category: Optional metadata filter.
        enable_hybrid: Whether to blend semantic similarity with exact keyword matching.

    Returns:
        List of matched chunks with metadata and hybrid similarity scores.
    """
    if not query or not query.strip():
        return []

    if top_k is None:
        top_k = config.RETRIEVAL_TOP_K
    if min_score is None:
        min_score = config.RETRIEVAL_MIN_SCORE

    query_vec = embed_query(query)
    where_filter = {"category": category} if category else None

    # Fetch top candidates for reranking
    fetch_k = top_k * 2 if enable_hybrid else top_k

    try:
        raw_results = chroma_db.query_knowledge_chunks(
            query_text=query,
            top_k=fetch_k,
            where=where_filter,
            min_score=min_score,
            query_vector=query_vec,
        )
    except Exception as exc:
        logger.error("ChromaDB vector search failed: %s", exc)
        raise KnowledgeBaseError(detail=f"Vector search failed: {exc}") from exc

    if not enable_hybrid or not raw_results:
        return raw_results[:top_k]

    # Hybrid reranking: boost candidates that contain exact acronyms, codes, and key terms
    import re
    clean_q = query.lower()
    # Extract significant tokens (words >= 3 chars, acronyms, or codes with hyphens)
    query_tokens = set(re.findall(r"\b[A-Za-z0-9\-]{3,}\b", clean_q))
    # Extract uppercase codes from original query (e.g. CC-POL-9921, ISO, ULD)
    exact_codes = set(re.findall(r"\b[A-Z0-9\-]{3,}\b", query))

    reranked = []
    for item in raw_results:
        content = (item.get("content") or "").lower()
        title = (item.get("section_title") or item.get("title") or "").lower()
        orig_content = item.get("content") or ""
        sim_score = float(item.get("similarity_score", item.get("score", 0.0)))

        # Check exact code matches
        code_boost = 0.0
        for code in exact_codes:
            if code in orig_content:
                code_boost += 0.15

        # Check token overlap
        overlap_count = sum(1 for tok in query_tokens if tok in content or tok in title)
        token_ratio = overlap_count / max(1, len(query_tokens))
        lexical_score = min(1.0, (token_ratio * 0.7) + min(0.3, code_boost))

        # Hybrid fusion: 75% semantic, 25% lexical
        hybrid_score = round((sim_score * 0.75) + (lexical_score * 0.25), 4)

        scored_item = dict(item)
        scored_item["similarity_score"] = hybrid_score
        scored_item["semantic_score"] = sim_score
        scored_item["lexical_score"] = round(lexical_score, 4)
        reranked.append(scored_item)

    reranked.sort(key=lambda x: x["similarity_score"], reverse=True)
    return reranked[:top_k]


def get_vector_db_health() -> Dict[str, Any]:
    """Return health and status of the ChromaDB vector database."""
    return chroma_db.check_chroma_health()
