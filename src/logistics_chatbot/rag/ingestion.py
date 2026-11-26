"""Data ingestion pipeline: loads shipment records and knowledge base articles.

Supports:
  - load_shipment_rows()       -> loads shipments with parsed dates from CSV/JSON
  - load_kb_rows()             -> loads knowledge articles and merges legacy FAQs
  - knowledge_embedding_text() -> formats knowledge row for embedding
  - sync_shipments()           -> upserts shipment rows to PostgreSQL
  - sync_knowledge()           -> embeds and upserts knowledge rows to PostgreSQL pgvector
"""
from __future__ import annotations

import csv
import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, List, Optional

# Ensure src/ is discoverable even when executed directly via VS Code "Run" button
_SRC_DIR = Path(__file__).resolve().parents[2]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from logistics_chatbot.core import config
from logistics_chatbot.database.database import run_query
from logistics_chatbot.core.errors import DatabaseError, KnowledgeBaseError

logger = logging.getLogger("logistics_chatbot.ingestion")


def _parse_date(val: Any) -> Optional[date]:
    if not val:
        return None
    if isinstance(val, (date, datetime)):
        return val if isinstance(val, date) and not isinstance(val, datetime) else val.date()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(val).strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_datetime(val: Any) -> Optional[datetime]:
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    for fmt in ("%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(val).strip(), fmt)
        except ValueError:
            continue
    return None


def load_shipment_rows() -> list[dict]:
    """Load shipment rows with parsed dates. Prioritizes shipments.csv."""
    path = config.SHIPMENTS_CSV_PATH
    if not path.exists():
        path = config.SHIPMENT_SEED_PATH

    rows = []
    if path.suffix == ".json":
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        for item in raw:
            row = dict(item)
            row["estimated_delivery"] = _parse_date(row.get("estimated_delivery"))
            row["last_updated"] = _parse_datetime(row.get("last_updated"))
            rows.append(row)
    else:
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                row = dict(r)
                row["estimated_delivery"] = _parse_date(row.get("estimated_delivery"))
                row["last_updated"] = _parse_datetime(row.get("last_updated"))
                for k in ("delay_reason", "current_location", "route", "customs_status"):
                    if row.get(k) == "":
                        row[k] = None
                rows.append(row)
    return rows


def load_kb_rows() -> list[dict]:
    """Load knowledge base rows, combining CSV rows with legacy FAQs."""
    rows: list[dict] = []
    seen_ids: set[str] = set()

    # 1. Load CSV rows (kb_long.csv preferred)
    if config.KB_CSV_PATH.exists():
        with open(config.KB_CSV_PATH, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                doc_id = r.get("doc_id") or r.get("id") or f"DOC-{len(rows)+1:04d}"
                if doc_id in seen_ids:
                    continue
                seen_ids.add(doc_id)
                rows.append({
                    "doc_id": doc_id,
                    "category": r.get("category", r.get("topic", "general")),
                    "section_title": r.get("section_title", r.get("question", "")),
                    "content": r.get("content", r.get("answer", "")),
                    "tags": r.get("tags", r.get("keywords", "")),
                    "last_updated": r.get("last_updated", "2026-11-01"),
                })

    # 2. Load standalone operational manuals and SOPs (*.txt). These files were
    # previously present in the project but were not included in local fallback
    # retrieval, so questions about their contents could return no answer.
    txt_dir = config.PROJECT_ROOT / "knowledge_base"
    if txt_dir.exists():
        for path in sorted(txt_dir.glob("*.txt")):
            try:
                raw = path.read_text(encoding="utf-8-sig", errors="replace").strip()
                if not raw:
                    continue
                # Keep section boundaries so a focused question retrieves a
                # compact, relevant part of the manual instead of one huge file.
                sections = []
                current_title = path.stem.replace("_", " ").title()
                current_lines = []
                for line in raw.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        if current_lines:
                            sections.append((current_title, "\n".join(current_lines).strip()))
                            current_lines = []
                        current_title = stripped.lstrip("# ").strip() or current_title
                    elif stripped:
                        current_lines.append(stripped)
                if current_lines:
                    sections.append((current_title, "\n".join(current_lines).strip()))
                for section_no, (title, content) in enumerate(sections, start=1):
                    if not content:
                        continue
                    doc_id = f"TXT-{path.stem.upper()}-{section_no:03d}"
                    if doc_id in seen_ids:
                        continue
                    seen_ids.add(doc_id)
                    rows.append({
                        "doc_id": doc_id,
                        "category": "operational_manual",
                        "section_title": title,
                        "content": content,
                        "tags": f"{path.stem.replace('_', ' ')} {title}",
                        "last_updated": "2026-11-20",
                    })
            except Exception as exc:
                logger.warning("Could not read knowledge document %s: %s", path.name, exc)

    # 3. Merge legacy FAQs from knowledge_base.json
    if config.LEGACY_FAQ_PATH.exists():
        try:
            with open(config.LEGACY_FAQ_PATH, encoding="utf-8") as f:
                faqs = json.load(f).get("faqs", [])
            for faq in faqs:
                topic = faq.get("topic", "faq").upper()
                doc_id = f"FAQ-LEGACY-{topic}"
                if doc_id in seen_ids:
                    continue
                seen_ids.add(doc_id)
                rows.append({
                    "doc_id": doc_id,
                    "category": faq.get("topic", "faq"),
                    "section_title": faq.get("question", ""),
                    "content": faq.get("answer", ""),
                    "tags": ";".join(faq.get("keywords", [])),
                    "last_updated": "2026-11-01",
                })
        except Exception as exc:
            logger.warning("Could not read legacy FAQs: %s", exc)

    return rows


def knowledge_embedding_text(row: dict) -> str:
    """Format a knowledge row for embedding generation."""
    title = row.get("section_title", "")
    content = row.get("content", "")
    tags = row.get("tags", "")
    return f"{title}\n{content}\nTags: {tags}".strip()


def sync_shipments(rows: Optional[list[dict]] = None) -> int:
    """Upsert shipment records into Supabase PostgreSQL."""
    if rows is None:
        rows = load_shipment_rows()
    if not rows:
        raise ValueError("Cannot sync empty shipment rows")

    sql = """
    INSERT INTO shipments (
        shipment_id, origin, destination, status, current_location,
        route, estimated_delivery, delay_reason, customs_status, last_updated
    ) VALUES (
        %(shipment_id)s, %(origin)s, %(destination)s, %(status)s, %(current_location)s,
        %(route)s, %(estimated_delivery)s, %(delay_reason)s, %(customs_status)s, %(last_updated)s
    )
    ON CONFLICT (shipment_id) DO UPDATE SET
        origin = EXCLUDED.origin,
        destination = EXCLUDED.destination,
        status = EXCLUDED.status,
        current_location = EXCLUDED.current_location,
        route = EXCLUDED.route,
        estimated_delivery = EXCLUDED.estimated_delivery,
        delay_reason = EXCLUDED.delay_reason,
        customs_status = EXCLUDED.customs_status,
        last_updated = EXCLUDED.last_updated;
    """
    for row in rows:
        run_query(sql, row)
    return len(rows)


def sync_knowledge(rows: Optional[list[dict]] = None) -> int:
    """Embed and upsert knowledge base records into Supabase PostgreSQL."""
    if rows is None:
        rows = load_kb_rows()
    if not rows:
        raise ValueError("Cannot sync empty knowledge base rows")

    from logistics_chatbot.rag.embeddings import embed_texts
    from logistics_chatbot.utils.helpers import to_pgvector

    texts = [knowledge_embedding_text(r) for r in rows]
    vectors = embed_texts(texts)

    sql = """
    INSERT INTO knowledge_base (
        doc_id, category, section_title, content, tags, last_updated, embedding
    ) VALUES (
        %(doc_id)s, %(category)s, %(section_title)s, %(content)s, %(tags)s, %(last_updated)s,
        %(embedding)s::vector
    )
    ON CONFLICT (doc_id) DO UPDATE SET
        category = EXCLUDED.category,
        section_title = EXCLUDED.section_title,
        content = EXCLUDED.content,
        tags = EXCLUDED.tags,
        last_updated = EXCLUDED.last_updated,
        embedding = EXCLUDED.embedding;
    """

    for row, vec in zip(rows, vectors):
        payload = dict(row)
        payload["embedding"] = to_pgvector(vec)
        run_query(sql, payload)

    return len(rows)
