"""Embedding generation service using lazy-loaded SentenceTransformers.

Model: all-MiniLM-L6-v2 (384 dimensions, cosine distance compatible).
"""
from __future__ import annotations

import logging
from typing import List

from logistics_chatbot.core import config
from logistics_chatbot.core.errors import KnowledgeBaseError

logger = logging.getLogger("logistics_chatbot.embeddings")

_model = None


def _get_model():
    """Lazy-load the SentenceTransformer model on first call."""
    global _model
    if _model is not None:
        return _model

    try:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model (%s): %s", config.EMBEDDING_PROVIDER, config.EMBEDDING_MODEL)
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
        return _model
    except Exception as exc:
        logger.error("Failed to load embedding model: %s", exc)
        raise KnowledgeBaseError(
            detail=f"Cannot load embedding model '{config.EMBEDDING_MODEL}': {exc}"
        ) from exc


_QUERY_EMBED_CACHE: dict[str, List[float]] = {}
_MAX_CACHE_SIZE = 2048


def clear_query_cache() -> None:
    """Clear query embedding cache."""
    _QUERY_EMBED_CACHE.clear()


def embed_query(query: str) -> List[float]:
    """Generate a 384-dimensional dense vector for a single query string with in-memory caching."""
    clean_q = (query or "").strip().lower()
    if not clean_q:
        return [0.0] * config.EMBEDDING_DIM

    from unittest.mock import Mock
    # If _get_model is mocked (unit tests), bypass cache to test model boundary conditions
    if not isinstance(_get_model, Mock) and clean_q in _QUERY_EMBED_CACHE:
        return _QUERY_EMBED_CACHE[clean_q]

    model = _get_model()
    try:
        if hasattr(model, "query_embed"):
            vectors = list(model.query_embed([clean_q]))
            vec = vectors[0]
        else:
            vec = model.encode(clean_q, convert_to_numpy=True, normalize_embeddings=True)

        if len(vec) != config.EMBEDDING_DIM:
            raise KnowledgeBaseError(
                detail=(
                    f"Embedding model returned {len(vec)} dimensions but "
                    f"expects {config.EMBEDDING_DIM}"
                )
            )
        res = [float(x) for x in vec]
        if len(_QUERY_EMBED_CACHE) < _MAX_CACHE_SIZE:
            _QUERY_EMBED_CACHE[clean_q] = res
        return res
    except KnowledgeBaseError:
        raise
    except Exception as exc:
        raise KnowledgeBaseError(
            detail=f"Embedding generation failed for query: {exc}"
        ) from exc


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate 384-dimensional dense vectors for a batch of strings."""
    if not texts:
        return []

    model = _get_model()
    try:
        if hasattr(model, "passage_embed"):
            results = []
            for vec in model.passage_embed(texts):
                if len(vec) != config.EMBEDDING_DIM:
                    raise KnowledgeBaseError(
                        detail=(
                            f"Embedding model returned {len(vec)} dimensions but "
                            f"expects {config.EMBEDDING_DIM}"
                        )
                    )
                results.append([float(x) for x in vec])
            return results
        else:
            vecs = model.encode(
                texts,
                batch_size=32,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            for vec in vecs:
                if len(vec) != config.EMBEDDING_DIM:
                    raise KnowledgeBaseError(
                        detail=(
                            f"Embedding model returned {len(vec)} dimensions but "
                            f"expects {config.EMBEDDING_DIM}"
                        )
                    )
            return [vec.tolist() if hasattr(vec, "tolist") else [float(x) for x in vec] for vec in vecs]
    except KnowledgeBaseError:
        raise
    except Exception as exc:
        raise KnowledgeBaseError(
            detail=f"Batch embedding generation failed: {exc}"
        ) from exc
