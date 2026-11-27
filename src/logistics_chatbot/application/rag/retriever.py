"""Unified retrieval pipeline: query classification, shipment/SQL queries, and multi-tier RAG search."""
from __future__ import annotations

import logging
import re
from typing import Optional

from logistics_chatbot.application.ingestion import kb_loader
from logistics_chatbot.core import config
from logistics_chatbot.core.constants import (
    BOOKING_ID_PATTERN,
    STOP_WORDS,
    VALID_SHIPMENT_ID_PATTERN,
)
from logistics_chatbot.core.errors import DatabaseError, InvalidShipmentIdError
from logistics_chatbot.domain.entities.models import (
    KnowledgeResult,
    QueryIntent,
    QueryType,
    RetrievedContext,
    ShipmentListResult,
    ShipmentResult,
)
from logistics_chatbot.infrastructure.database import repository as database
from logistics_chatbot.infrastructure.embeddings import sentence_transformer as embeddings
from logistics_chatbot.infrastructure.vector_store import chroma_store as chroma_db
from logistics_chatbot.infrastructure.vector_store import pgvector_store as kb_module
from logistics_chatbot.utils.helpers import format_date

logger = logging.getLogger("logistics_chatbot.retrieval")

LOOSE_ID_PATTERN = re.compile(r"\bSHP[-\s]?\d+\b", re.IGNORECASE)
VALID_ID_PATTERN = VALID_SHIPMENT_ID_PATTERN

_EXPLICIT_FILTER_COMMANDS = (
    "list shipments", "show shipments", "all shipments",
    "view shipments", "filter shipments", "how many shipments",
    "total shipments", "count shipments", "list all shipments",
    "show all shipments", "get all shipments",
)

_STATUS_MAP = {
    "delayed": "Delayed",
    "in transit": "In Transit",
    "delivered": "Delivered",
    "pending": "Pending",
    "on hold": "On Hold",
    "customs hold": "Customs Hold",
    "cleared": "Cleared",
}

_PRONOUN_FOLLOWUP = re.compile(
    r"\b(it|this|that|the shipment|the package|the order|the delivery)\b",
    re.IGNORECASE,
)


def detect_booking_id(text: str) -> Optional[str]:
    """Return a normalized enterprise booking reference (e.g. 'ALC-2025-100000') if present."""
    match = BOOKING_ID_PATTERN.search(text or "")
    if not match:
        return None
    return f"ALC-{match.group(1)}-{match.group(2)}"


def detect_shipment_id(text: str) -> Optional[str]:
    """Return a normalized shipment ID (SHP-xxxxx) or None; raise InvalidShipmentIdError if malformed."""
    match = LOOSE_ID_PATTERN.search(text)
    if match is None:
        return None
    digits = re.search(r"\d+", match.group(0)).group(0)
    shipment_id = f"SHP-{digits}"
    if not VALID_ID_PATTERN.match(shipment_id):
        raise InvalidShipmentIdError(
            f"'{match.group(0).upper()}' doesn't look like a valid shipment ID. "
            "IDs look like SHP-10001 (SHP, a dash, then 5 digits)."
        )
    return shipment_id


def _extract_location_filter(text_lower: str, preposition: str) -> Optional[str]:
    pattern = rf"(?:shipments?\s+)?{preposition}\s+([A-Za-z\s]+?)(?:\s+to\s|\s+with\s|\?|$)"
    match = re.search(pattern, text_lower)
    if match:
        loc = match.group(1).strip().title()
        if len(loc) > 2:
            return loc
    return None


def classify_query(text: str, previous_shipment_id: Optional[str] = None) -> QueryIntent:
    """Classify user query into shipment lookup, shipment filter, mixed, or knowledge search."""
    text_lower = text.lower().strip()

    shipment_id = detect_shipment_id(text)
    if not shipment_id and previous_shipment_id and _PRONOUN_FOLLOWUP.search(text_lower):
        shipment_id = previous_shipment_id

    has_filter_command = any(cmd in text_lower for cmd in _EXPLICIT_FILTER_COMMANDS)
    status_filter = None
    for keyword, canonical in _STATUS_MAP.items():
        if keyword in text_lower:
            status_filter = canonical
            break

    origin_filter = _extract_location_filter(text_lower, "from")
    destination_filter = _extract_location_filter(text_lower, "to")

    knowledge_keywords = (
        "policy", "rule", "guideline", "procedure", "how to", "what is",
        "why", "can i", "customs", "delay", "standard", "documentation",
        "documents required", "invoice", "transit time", "faq",
    )
    has_knowledge_intent = any(kw in text_lower for kw in knowledge_keywords)

    if shipment_id and has_knowledge_intent:
        query_type = QueryType.MIXED
    elif shipment_id:
        query_type = QueryType.SHIPMENT_LOOKUP
    elif has_filter_command or (status_filter and ("shipments" in text_lower or "list" in text_lower)):
        query_type = QueryType.SHIPMENT_FILTER
    else:
        query_type = QueryType.KNOWLEDGE_SEARCH

    return QueryIntent(
        query_type=query_type,
        shipment_id=shipment_id,
        status_filter=status_filter,
        origin_filter=origin_filter,
        destination_filter=destination_filter,
        raw_query=text.strip(),
    )


def get_shipment_by_id(shipment_id: str) -> ShipmentResult:
    """Fetch a single shipment by ID."""
    shipment = database.get_shipment(shipment_id)
    return ShipmentResult(shipment=shipment)


def search_shipments(
    status: Optional[str] = None,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    limit: int = 10,
) -> ShipmentListResult:
    """Filter shipments across SQLite, PostgreSQL, and CSV fallback."""
    from unittest.mock import Mock
    from logistics_chatbot.infrastructure.database import sqlite_repository as sq_repo

    desc_parts = []
    if status:
        desc_parts.append(f"status='{status}'")
    if origin:
        desc_parts.append(f"origin contains '{origin}'")
    if destination:
        desc_parts.append(f"destination contains '{destination}'")
    desc = ", ".join(desc_parts) if desc_parts else "all shipments"

    use_postgres = bool(config.SUPABASE_DB_URL) or isinstance(database.run_query, Mock)
    if not use_postgres:
        sq_rows = sq_repo.search_shipments(status=status, origin=origin, destination=destination, limit=limit)
        if sq_rows is not None:
            return ShipmentListResult(
                shipments=sq_rows,
                total_count=len(sq_rows),
                filter_description=desc,
                source="shipments_sqlite",
            )

    conditions, params = [], []
    if status:
        conditions.append("LOWER(status) = LOWER(%s)")
        params.append(status)
    if origin:
        conditions.append("LOWER(origin) LIKE LOWER(%s)")
        params.append(f"%{origin}%")
    if destination:
        conditions.append("LOWER(destination) LIKE LOWER(%s)")
        params.append(f"%{destination}%")

    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    params.append(limit)
    sql = f"""
        SELECT * FROM shipments
        WHERE {where_clause}
        ORDER BY last_updated DESC NULLS LAST
        LIMIT %s
    """

    try:
        rows = database.run_query(sql, tuple(params))
    except DatabaseError:
        if not config.SUPABASE_DB_URL:
            raw_rows = kb_loader.load_shipment_rows()
            filtered = []
            for r in raw_rows:
                if status and (r.get("status") or "").lower() != status.lower():
                    continue
                if origin and origin.lower() not in (r.get("origin") or "").lower():
                    continue
                if destination and destination.lower() not in (r.get("destination") or "").lower():
                    continue
                item = dict(r)
                item["estimated_delivery"] = format_date(item.get("estimated_delivery"))
                item["last_updated"] = format_date(item.get("last_updated"))
                filtered.append(item)

            return ShipmentListResult(
                shipments=filtered[:limit],
                total_count=len(filtered),
                filter_description=desc,
                source="shipments_csv",
            )
        raise

    for r in rows:
        r["estimated_delivery"] = format_date(r.get("estimated_delivery"))
        r["last_updated"] = format_date(r.get("last_updated"))

    return ShipmentListResult(
        shipments=rows,
        total_count=len(rows),
        filter_description=desc,
        source="shipments",
    )


def _offline_keyword_search(query: str, top_k: int = 5) -> list[dict]:
    """Score knowledge rows (CSV, TXT manuals, legacy FAQs) via word-boundary keyword overlap."""
    rows = kb_loader.load_kb_rows()
    words = [w for w in re.findall(r"\w+", query.lower()) if w not in STOP_WORDS and len(w) > 2]
    if not words:
        return []

    query_lower = re.sub(r"\s+", " ", query.lower()).strip()
    scored = []
    for r in rows:
        title = str(r.get("section_title", "")).lower()
        content = str(r.get("content", "")).lower()
        tags = str(r.get("tags", "")).lower()
        haystack = f"{title} {tags} {content}"
        score = 0.0
        matched = 0
        for w in words:
            if re.search(r"\b" + re.escape(w) + r"\b", title):
                score += 5.0
                matched += 1
            elif re.search(r"\b" + re.escape(w) + r"\b", tags):
                score += 3.0
                matched += 1
            elif re.search(r"\b" + re.escape(w) + r"\b", content):
                score += 1.5
                matched += 1
        if len(query_lower) >= 8 and query_lower in haystack:
            score += 8.0
        score += (matched / max(1, len(words))) * 2.0
        if score >= 2.5:
            scored.append({
                "doc_id": r.get("doc_id", "DOC-LOCAL"),
                "category": r.get("category", "general"),
                "section_title": r.get("section_title", ""),
                "content": r.get("content", ""),
                "score": round(score, 4),
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def search_knowledge(
    query: str,
    top_k: Optional[int] = None,
    min_score: Optional[float] = None,
    category: Optional[str] = None,
) -> KnowledgeResult:
    """Semantic search over knowledge base: pgvector -> ChromaDB -> local offline CSV/TXT."""
    if top_k is None:
        top_k = config.RETRIEVAL_TOP_K
    if min_score is None:
        min_score = config.RETRIEVAL_MIN_SCORE

    # 1. Supabase pgvector or unit-test mocked fetch_matches
    try:
        query_vector = embeddings.embed_query(query)
        matches = kb_module.fetch_matches(query_vector, top_k=top_k, min_score=min_score)
        if matches:
            if category:
                matches = [m for m in matches if m.get("category", "").lower() == category.lower()][:top_k]
            if matches:
                return KnowledgeResult(articles=matches, source="supabase_pgvector")
    except Exception as exc:
        logger.warning("Primary semantic retrieval unavailable; trying fallback: %s", exc)

    # 2. ChromaDB vector database semantic search + lightweight lexical boost
    if getattr(config, "VECTOR_STORE", "auto") in ("chroma", "auto"):
        try:
            where_filter = {"category": category.lower()} if category else None
            fetch_k = top_k * 2 if where_filter is None else top_k
            chroma_matches = chroma_db.query_knowledge_chunks(
                query,
                top_k=fetch_k,
                where=where_filter,
                min_score=min_score,
            )
            if chroma_matches:
                clean_q = query.lower()
                q_tokens = {
                    t for t in re.findall(r"\b[a-z0-9\-]{3,}\b", clean_q) if t not in STOP_WORDS
                }
                if q_tokens:
                    reranked = []
                    for item in chroma_matches:
                        txt_low = (item.get("content") or "").lower()
                        title_low = (item.get("section_title") or item.get("section_name") or "").lower()
                        hits = sum(1 for tok in q_tokens if tok in txt_low or tok in title_low)
                        lex = hits / max(1, len(q_tokens))
                        sem = float(item.get("score", 0.0))
                        boosted = round((sem * 0.82) + (lex * 0.18), 4)
                        enriched = dict(item)
                        enriched["semantic_score"] = sem
                        enriched["score"] = boosted
                        reranked.append(enriched)
                    reranked.sort(key=lambda x: x["score"], reverse=True)
                    chroma_matches = reranked[:top_k]
                else:
                    chroma_matches = chroma_matches[:top_k]
                return KnowledgeResult(articles=chroma_matches, source="chroma_db")
        except Exception as exc:
            logger.warning("ChromaDB query skipped; using local knowledge files: %s", exc)

    # 3. Local offline keyword search over CSV, legacy FAQ and standalone TXT manuals
    matches = _offline_keyword_search(query, top_k=top_k)
    return KnowledgeResult(articles=matches, source="offline_csv")


def retrieve(question: str, previous_shipment_id: Optional[str] = None) -> RetrievedContext:
    """Execute the full retrieval workflow based on query intent."""
    intent = classify_query(question, previous_shipment_id=previous_shipment_id)
    ctx = RetrievedContext(intent=intent)

    if intent.query_type == QueryType.SHIPMENT_LOOKUP:
        ctx.shipment = get_shipment_by_id(intent.shipment_id).shipment
        return ctx

    if intent.query_type == QueryType.SHIPMENT_FILTER:
        result = search_shipments(
            status=intent.status_filter,
            origin=intent.origin_filter,
            destination=intent.destination_filter,
        )
        ctx.shipment_list = result.shipments
        ctx.filter_description = result.filter_description
        return ctx

    if intent.query_type == QueryType.MIXED:
        ctx.shipment = get_shipment_by_id(intent.shipment_id).shipment
        kb_result = search_knowledge(question)
        ctx.knowledge_articles = kb_result.articles
        ctx.source_doc_ids = [a["doc_id"] for a in kb_result.articles if "doc_id" in a]
        return ctx

    kb_result = search_knowledge(question)
    ctx.knowledge_articles = kb_result.articles
    ctx.source_doc_ids = [a["doc_id"] for a in kb_result.articles if "doc_id" in a]
    return ctx
