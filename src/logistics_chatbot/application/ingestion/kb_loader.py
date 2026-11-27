"""Knowledge base and shipment dataset loader (CSV, TXT manuals, legacy JSON, PostgreSQL sync)."""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Optional

from logistics_chatbot.core import config
from logistics_chatbot.infrastructure.database.csv_fallback import load_shipment_rows_from_files
from logistics_chatbot.infrastructure.database.repository import run_query
from logistics_chatbot.infrastructure.embeddings import sentence_transformer as embeddings
from logistics_chatbot.utils.helpers import to_pgvector

logger = logging.getLogger("logistics_chatbot.ingestion")


def load_shipment_rows() -> list[dict]:
    """Load shipment rows with parsed dates from shipments.csv or seed JSON."""
    return load_shipment_rows_from_files()


def _resolve_manuals_dir() -> Optional[Path]:
    """Return directory containing standalone operational *.txt manuals."""
    configured = getattr(config, "KB_MANUALS_DIR", None)
    if configured and Path(configured).exists():
        return Path(configured)
    for candidate in (config.KB_DATA_DIR / "manuals", config.PROJECT_ROOT / "knowledge_base"):
        if candidate.exists():
            return candidate
    return None


def load_kb_rows() -> list[dict]:
    """Load knowledge base rows combining CSV corpus, standalone TXT manuals, and legacy FAQs."""
    rows: list[dict] = []
    seen_ids: set[str] = set()

    # 1. Load CSV rows (kb_long.csv preferred)
    if config.KB_CSV_PATH.exists():
        with open(config.KB_CSV_PATH, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
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

    # 2. Load standalone operational manuals and SOPs (*.txt) split by section headers
    txt_dir = _resolve_manuals_dir()
    if txt_dir is not None and txt_dir.exists():
        for path in sorted(txt_dir.glob("*.txt")):
            try:
                raw = path.read_text(encoding="utf-8-sig", errors="replace").strip()
                if not raw:
                    continue
                sections: list[tuple[str, str]] = []
                current_title = path.stem.replace("_", " ").title()
                current_lines: list[str] = []
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

    texts = [knowledge_embedding_text(r) for r in rows]
    vectors = embeddings.embed_texts(texts)

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
