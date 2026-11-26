"""Ingest the 5 Logistics Reference PDFs from data/new_data into ChromaDB (and optional Supabase).

Usage:
    python scripts/ingest_new_pdfs.py [--dir data/new_data] [--target chroma|supabase|both] [--replace]
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
for p in (str(_SRC), str(_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from logistics_chatbot.core import config
from logistics_chatbot.rag import embeddings
from logistics_chatbot.vectorstores import chroma_db
from rag.document_processor import process_pdf_document
from rag.search import get_chroma_collection, index_document_chunks, search_knowledge

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("ingest_new_pdfs")


def verify_embedding_compatibility() -> int:
    """Confirm embedding model produces config.EMBEDDING_DIM (384) vectors cleanly."""
    probe = embeddings.embed_query("Incoterms 2020 EXW DDP customs clearance dimension check")
    if len(probe) != config.EMBEDDING_DIM:
        raise RuntimeError(
            f"Embedding model '{config.EMBEDDING_MODEL}' returned {len(probe)} dims, "
            f"expected {config.EMBEDDING_DIM}"
        )
    return len(probe)


def ingest_pdfs_to_chroma(
    pdf_dir: Path,
    replace_existing: bool = False,
) -> Dict[str, object]:
    """Load, chunk, embed, and upsert all PDF files inside pdf_dir into ChromaDB."""
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {pdf_dir}")

    dim = verify_embedding_compatibility()
    coll = get_chroma_collection()
    count_before = coll.count()

    processed_docs: List[Dict[str, object]] = []
    failed_docs: List[Dict[str, str]] = []
    total_chunks = 0

    for pdf_path in pdf_files:
        try:
            raw_bytes = pdf_path.read_bytes()
            chunks, doc_id = process_pdf_document(pdf_path.name, raw_bytes)
            if replace_existing:
                chroma_db.delete_document_chunks(doc_id)

            indexed = index_document_chunks(chunks)
            total_chunks += indexed
            processed_docs.append({
                "filename": pdf_path.name,
                "document_id": doc_id,
                "document_name": chunks[0]["metadata"]["document_name"],
                "category": chunks[0]["metadata"]["document_category"],
                "pages": max(c["metadata"]["page_number"] for c in chunks),
                "chunks": indexed,
            })
        except Exception as exc:
            logger.error("Failed processing PDF '%s': %s", pdf_path.name, exc)
            failed_docs.append({"filename": pdf_path.name, "error": str(exc)})

    count_after = coll.count()
    return {
        "embedding_model": config.EMBEDDING_MODEL,
        "embedding_dim": dim,
        "collection_name": config.CHROMA_COLLECTION_NAME,
        "count_before": count_before,
        "count_after": count_after,
        "documents": processed_docs,
        "failed": failed_docs,
        "total_chunks_upserted": total_chunks,
    }


def ingest_pdfs_to_supabase(docs_chunks: List[Dict[str, object]]) -> int:
    """Optionally mirror processed PDF documents and chunks to Supabase documents & knowledge_base."""
    if not config.SUPABASE_DB_URL:
        logger.warning("SUPABASE_DB_URL is not set; skipping Supabase pgvector PDF sync.")
        return 0

    from logistics_chatbot.database.database import run_query
    from logistics_chatbot.utils.helpers import to_pgvector

    upserted = 0
    texts = [c["text"] for c in docs_chunks]
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
    for chunk, vec in zip(docs_chunks, vectors):
        m = chunk["metadata"]
        run_query(sql, {
            "doc_id": chunk["chunk_id"],
            "category": m["document_category"],
            "section_title": m["section_title"],
            "content": chunk["text"],
            "tags": f"{m['document_name']};page-{m['page_number']};{m['section_name']}",
            "last_updated": m["upload_timestamp"][:10],
            "embedding": to_pgvector(vec),
        })
        upserted += 1
    return upserted


def run_retrieval_verification() -> List[Dict[str, object]]:
    """Verify semantic retrieval across the 8 required Phase 3 validation questions."""
    queries = [
        "What is the shipment booking process?",
        "How can customers track their shipments?",
        "What documents are required for international shipping?",
        "What is the difference between FOB and CIF?",
        "What are the common causes of shipment delays?",
        "How does customs clearance work?",
        "What is bonded warehousing?",
        "What should customers do when a shipment is delayed?",
    ]
    report = []
    for q in queries:
        hits = search_knowledge(q, top_k=3)
        report.append({
            "query": q,
            "match_count": len(hits),
            "top_matches": [
                {
                    "chunk_id": h.get("chunk_id"),
                    "document_name": h.get("document_name") or h.get("metadata", {}).get("document_name"),
                    "page_number": h.get("page_number") or h.get("metadata", {}).get("page_number"),
                    "section_name": h.get("section_name") or h.get("section_title"),
                    "score": h.get("similarity_score", h.get("score")),
                    "snippet": (h.get("content") or "")[:140].replace("\n", " "),
                }
                for h in hits
            ],
        })
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest new logistics PDFs into ChromaDB / Supabase")
    parser.add_argument("--dir", type=Path, default=_ROOT / "data" / "new_data", help="Directory containing PDFs")
    parser.add_argument("--target", choices=["chroma", "supabase", "both"], default="chroma")
    parser.add_argument("--replace", action="store_true", help="Delete existing doc chunks before re-upserting")
    args = parser.parse_args()

    print("=" * 72)
    print("NEXUSFREIGHT PDF KNOWLEDGE BASE INGESTION")
    print("=" * 72)

    if args.target in ("chroma", "both"):
        summary = ingest_pdfs_to_chroma(args.dir, replace_existing=args.replace)
        print(f"Embedding Model : {summary['embedding_model']} ({summary['embedding_dim']} dims)")
        print(f"Collection      : {summary['collection_name']}")
        print(f"Record Count    : {summary['count_before']} -> {summary['count_after']} "
              f"(+{summary['count_after'] - summary['count_before']} net)")
        print(f"Chunks Upserted : {summary['total_chunks_upserted']}")
        for d in summary["documents"]:
            print(f"  - {d['filename']} | id={d['document_id']} | cat={d['category']} "
                  f"| pages={d['pages']} | chunks={d['chunks']}")
        if summary["failed"]:
            print("Failed Documents:", summary["failed"])
            return 1

    if args.target in ("supabase", "both"):
        if not config.SUPABASE_DB_URL:
            print("Supabase PDF sync skipped: SUPABASE_DB_URL is not configured in .env.")
        else:
            all_chunks = []
            for pdf_path in sorted(args.dir.glob("*.pdf")):
                chunks, _ = process_pdf_document(pdf_path.name, pdf_path.read_bytes())
                all_chunks.extend(chunks)
            n_supa = ingest_pdfs_to_supabase(all_chunks)
            print(f"Supabase pgvector upserted chunks: {n_supa}")

    print("\n--- PHASE 3 RETRIEVAL VERIFICATION (TOP 3 PER QUERY) ---")
    for item in run_retrieval_verification():
        print(f"\nQ: {item['query']} (matches={item['match_count']})")
        for m in item["top_matches"]:
            print(f"  [{m['score']}] {m['chunk_id']} ({m['document_name']}, p.{m['page_number']} | {m['section_name']}): {m['snippet']}...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
