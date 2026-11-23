"""Embedding generation service for RAG vector retrieval."""
from __future__ import annotations

from typing import List
from logistics_chatbot.rag.embeddings import embed_query, embed_texts

__all__ = ["embed_query", "embed_texts"]
