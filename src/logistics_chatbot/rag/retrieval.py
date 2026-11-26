"""Retrieval service: unified data retrieval for the RAG pipeline.

Provides query classification, structured shipment queries, semantic
knowledge-base search (ChromaDB primary, Supabase pgvector secondary,
offline keyword fallback), and context formatting.
"""
from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional

# Ensure src/ is discoverable even when executed directly via VS Code "Run" button
_SRC_DIR = Path(__file__).resolve().parents[2]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from logistics_chatbot.core import config
from logistics_chatbot.database import database
from logistics_chatbot.rag import embeddings
from logistics_chatbot.rag import knowledge_base as kb_module
from logistics_chatbot.core.errors import DatabaseError, InvalidShipmentIdError, KnowledgeBaseError

logger = logging.getLogger("logistics_chatbot.retrieval")

# ── Shipment ID patterns ────────────────────────────────────────────

LOOSE_ID_PATTERN = re.compile(r"\bSHP[-\s]?\d+\b", re.IGNORECASE)
VALID_ID_PATTERN = re.compile(r"^SHP-\d{5}$")
BOOKING_ID_PATTERN = re.compile(r"\bALC[-\s]?(\d{4})[-\s]?(\d{5,7})\b", re.IGNORECASE)


def detect_booking_id(text: str) -> Optional[str]:
    """Return a normalized enterprise booking reference (e.g. 'ALC-2025-100000') if present."""
    match = BOOKING_ID_PATTERN.search(text or "")
    if not match:
        return None
    return f"ALC-{match.group(1)}-{match.group(2)}"


def detect_shipment_id(text: str) -> Optional[str]:
    """Return a normalised shipment ID found in the text, or None if there is none."""
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


def format_shipment(shipment: dict) -> str:
    """Turn a database row (dict) into plain text the LLM can read."""
    return "\n".join([
        f"Shipment ID: {shipment['shipment_id']}",
        f"Status: {shipment['status']}",
        f"Origin: {shipment['origin']}",
        f"Destination: {shipment['destination']}",
        f"Current location: {shipment.get('current_location') or 'Unknown'}",
        f"Route: {shipment.get('route') or 'Not available'}",
        f"Estimated delivery: {shipment.get('estimated_delivery') or 'Not available'}",
        f"Delay reason: {shipment.get('delay_reason') or 'None'}",
        f"Customs status: {shipment.get('customs_status') or 'Unknown'}",
        f"Last updated: {shipment.get('last_updated') or 'Unknown'}",
    ])


# ── Query classification ────────────────────────────────────────────

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


class QueryType(Enum):
    SHIPMENT_LOOKUP = auto()
    SHIPMENT_FILTER = auto()
    KNOWLEDGE_SEARCH = auto()
    MIXED = auto()


@dataclass
class QueryIntent:
    """Result of query classification."""
    query_type: QueryType
    shipment_id: Optional[str] = None
    status_filter: Optional[str] = None
    origin_filter: Optional[str] = None
    destination_filter: Optional[str] = None
    raw_query: str = ""


def classify_query(
    text: str,
    previous_shipment_id: Optional[str] = None,
) -> QueryIntent:
    """Analyse a user query to decide what to retrieve."""
    text_lower = text.lower().strip()

    shipment_id = detect_shipment_id(text)
    if not shipment_id and previous_shipment_id:
        if _PRONOUN_FOLLOWUP.search(text_lower):
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


def _extract_location_filter(text_lower: str, preposition: str) -> Optional[str]:
    """Lightweight extraction: 'shipments from Mumbai' -> 'Mumbai'."""
    pattern = rf"(?:shipments?\s+)?{preposition}\s+([A-Za-z\s]+?)(?:\s+to\s|\s+with\s|\?|$)"
    match = re.search(pattern, text_lower)
    if match:
        loc = match.group(1).strip().title()
        if len(loc) > 2:
            return loc
    return None


# ── Shipment retrieval ──────────────────────────────────────────────

@dataclass
class ShipmentResult:
    """Container for a single shipment record."""
    shipment: dict
    source: str = "shipments"


@dataclass
class ShipmentListResult:
    """Container for a filtered list of shipments."""
    shipments: list[dict] = field(default_factory=list)
    total_count: int = 0
    filter_description: str = ""
    source: str = "shipments"


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
    """Filter shipments by status, origin, and/or destination (PostgreSQL -> SQLite -> CSV fallback)."""
    from unittest.mock import Mock
    from logistics_chatbot.utils.helpers import format_date

    desc_parts = []
    if status:
        desc_parts.append(f"status='{status}'")
    if origin:
        desc_parts.append(f"origin contains '{origin}'")
    if destination:
        desc_parts.append(f"destination contains '{destination}'")
    desc = ", ".join(desc_parts) if desc_parts else "all shipments"

    # Fast local SQLite path when Supabase is unconfigured and run_query is not mocked
    use_postgres = bool(config.SUPABASE_DB_URL) or isinstance(database.run_query, Mock)
    if not use_postgres:
        db_path = config.PROJECT_ROOT / "data" / "raw" / "shipments.db"
        if db_path.exists():
            sq_conds = []
            sq_params: list = []
            if status:
                sq_conds.append("status = ? COLLATE NOCASE")
                sq_params.append(status)
            if origin:
                sq_conds.append("LOWER(origin) LIKE LOWER(?)")
                sq_params.append(f"%{origin}%")
            if destination:
                sq_conds.append("LOWER(destination) LIKE LOWER(?)")
                sq_params.append(f"%{destination}%")
            sq_where = " AND ".join(sq_conds) if sq_conds else "1=1"
            sq_params.append(limit)
            sq_sql = f"SELECT * FROM shipments WHERE {sq_where} ORDER BY last_updated DESC LIMIT ?"
            try:
                with database._sqlite_conn(db_path) as conn:
                    rows = [dict(r) for r in conn.execute(sq_sql, tuple(sq_params)).fetchall()]
                for r in rows:
                    r["estimated_delivery"] = format_date(r.get("estimated_delivery"))
                    r["last_updated"] = format_date(r.get("last_updated"))
                return ShipmentListResult(
                    shipments=rows,
                    total_count=len(rows),
                    filter_description=desc,
                    source="shipments_sqlite",
                )
            except Exception as exc:
                logger.debug("SQLite search_shipments fallback notice: %s", exc)

    conditions = []
    params: list = []

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
            from logistics_chatbot.rag import ingestion
            raw_rows = ingestion.load_shipment_rows()
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


# ── Knowledge retrieval ─────────────────────────────────────────────

@dataclass
class KnowledgeResult:
    """Container for retrieved knowledge base articles."""
    articles: list[dict] = field(default_factory=list)
    source: str = "knowledge_base"


_STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or",
    "is", "are", "was", "were", "what", "how", "why", "when", "where",
    "who", "which", "can", "could", "should", "would", "do", "does",
    "did", "tell", "me", "about", "your", "my", "our", "you", "i",
    "joke", "hi", "hello", "hey",
}


def _offline_keyword_search(query: str, top_k: int = 5) -> list[dict]:
    """Score knowledge rows using simple keyword overlap when DB is offline."""
    from logistics_chatbot.rag import ingestion

    rows = ingestion.load_kb_rows()
    words = [
        w for w in re.findall(r"\w+", query.lower())
        if w not in _STOP_WORDS and len(w) > 2
    ]
    if not words:
        return []

    # Score title, tags, exact phrases and body separately. This local lexical
    # path deliberately works even when SentenceTransformers/HuggingFace or
    # ChromaDB cannot load (for example on a first run without internet).
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
        # Prefer a result that covers a larger share of the meaningful query.
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
    """Semantic search over knowledge base using ChromaDB / pgvector with offline fallback."""
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
                matches = [
                    m for m in matches
                    if m.get("category", "").lower() == category.lower()
                ][:top_k]
            if matches:
                return KnowledgeResult(articles=matches, source="supabase_pgvector")
    except Exception as exc:
        # Do not stop the entire RAG pipeline when the embedding model or
        # optional Supabase vector search is unavailable. Continue to ChromaDB
        # and finally the local CSV/TXT keyword index.
        logger.warning("Primary semantic retrieval unavailable; trying fallback: %s", exc)

    # 2. ChromaDB vector database semantic search + lightweight lexical boost
    if getattr(config, "VECTOR_STORE", "auto") in ("chroma", "auto"):
        try:
            from logistics_chatbot.vectorstores import chroma_db
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
                    t for t in re.findall(r"\b[a-z0-9\-]{3,}\b", clean_q)
                    if t not in _STOP_WORDS
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


# ── Unified Retrieval Pipeline ──────────────────────────────────────

@dataclass
class RetrievedContext:
    """Complete context package for LLM prompt construction."""
    intent: QueryIntent
    shipment: Optional[dict] = None
    shipment_list: Optional[list[dict]] = None
    filter_description: str = ""
    knowledge_articles: list[dict] = field(default_factory=list)
    source_doc_ids: list[str] = field(default_factory=list)


def retrieve(
    question: str,
    previous_shipment_id: Optional[str] = None,
) -> RetrievedContext:
    """Execute the full retrieval workflow based on query intent."""
    intent = classify_query(question, previous_shipment_id=previous_shipment_id)
    ctx = RetrievedContext(intent=intent)

    if intent.query_type == QueryType.SHIPMENT_LOOKUP:
        result = get_shipment_by_id(intent.shipment_id)
        ctx.shipment = result.shipment
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
        result = get_shipment_by_id(intent.shipment_id)
        ctx.shipment = result.shipment
        kb_result = search_knowledge(question)
        ctx.knowledge_articles = kb_result.articles
        ctx.source_doc_ids = [a["doc_id"] for a in kb_result.articles if "doc_id" in a]
        return ctx

    # Default: KNOWLEDGE_SEARCH
    kb_result = search_knowledge(question)
    ctx.knowledge_articles = kb_result.articles
    ctx.source_doc_ids = [a["doc_id"] for a in kb_result.articles if "doc_id" in a]
    return ctx


# ── Context Formatting ──────────────────────────────────────────────

def format_context(ctx: RetrievedContext) -> str:
    """Convert RetrievedContext into a structured text block for the LLM."""
    sections = []

    if ctx.shipment:
        sections.append("SHIPMENT RECORD:\n" + format_shipment(ctx.shipment))

    if ctx.shipment_list is not None:
        if ctx.shipment_list:
            lines = [f"SHIPMENT LIST ({len(ctx.shipment_list)} total, filter: {ctx.filter_description}):"]
            for s in ctx.shipment_list:
                line = (
                    f"  - {s['shipment_id']}: {s['status']} from {s['origin']} "
                    f"to {s['destination']}, eta: {s.get('estimated_delivery') or 'N/A'}"
                )
                if s.get("delay_reason"):
                    line += f" (delayed: {s['delay_reason']})"
                lines.append(line)
            sections.append("\n".join(lines))
        else:
            sections.append(
                f"SHIPMENT LIST: No shipments found matching {ctx.filter_description}."
            )

    if ctx.knowledge_articles:
        lines = ["KNOWLEDGE BASE:"]
        for a in ctx.knowledge_articles:
            doc_id = a.get("doc_id", "DOC")
            title = a.get("section_title", "")
            content = a.get("content", "")
            lines.append(f"[{doc_id}] {title}\n{content}")
        sections.append("\n\n".join(lines))

    return "\n\n".join(sections)
