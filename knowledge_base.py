"""Searches the FAQ knowledge base (data/knowledge_base.json).

This is a simple keyword search: each FAQ has a list of keywords, and the
FAQs whose keywords appear in the user's question are returned.
"""
import json

import config
from errors import KnowledgeBaseError


def load_faqs():
    try:
        with open(config.KNOWLEDGE_BASE_PATH, encoding="utf-8") as f:
            return json.load(f)["faqs"]
    except (OSError, ValueError, KeyError) as exc:
        raise KnowledgeBaseError(detail=f"Could not load knowledge base: {exc}") from exc


def search_faqs(question, top_k=2):
    """Return the best-matching FAQ answers for a question (may be an empty list)."""
    text = question.lower()
    scored = []
    for faq in load_faqs():
        score = sum(1 for keyword in faq["keywords"] if keyword in text)
        if score > 0:
            scored.append((score, faq))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [f"FAQ ({faq['topic']}): {faq['answer']}" for _, faq in scored[:top_k]]
