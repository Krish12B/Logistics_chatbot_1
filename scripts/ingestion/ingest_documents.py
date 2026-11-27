"""Document & data ingestion utility for ChromaDB and Supabase PostgreSQL.

Usage:
    python scripts/ingest_documents.py [--target chroma|supabase|both] [--limit N]
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from logistics_chatbot.core import config
from logistics_chatbot.infrastructure.database import repository as database
from logistics_chatbot.application.ingestion import kb_loader as ingestion
from logistics_chatbot.infrastructure.vector_store import chroma_store as chroma_db

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("ingest_documents")


def main():
    parser = argparse.ArgumentParser(description="Ingest logistics knowledge base and shipment records")
    parser.add_argument("--target", choices=["chroma", "supabase", "both"], default="chroma", help="Target vector/database store")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of articles to ingest")
    args = parser.parse_args()

    print("=" * 65)
    print("FLEETHARBOR LOGISTICS - DOCUMENT & KNOWLEDGE INGESTION")
    print(f"Target: {args.target.upper()} | Limit: {args.limit or 'All'}")
    print("=" * 65)

    # 1. Ingest to ChromaDB
    if args.target in ("chroma", "both"):
        print("\n1. Ingesting knowledge chunks into ChromaDB...")
        try:
            count = chroma_db.ingest_from_kb(limit=args.limit)
            print(f"   ✅ Upserted {count} chunks into ChromaDB collection '{config.CHROMA_COLLECTION_NAME}'")
        except Exception as exc:
            print(f"   ❌ ChromaDB ingestion failed: {exc}")
            if args.target == "chroma":
                return 1

    # 2. Ingest to Supabase
    if args.target in ("supabase", "both"):
        print("\n2. Ingesting records into Supabase PostgreSQL...")
        if not config.SUPABASE_DB_URL:
            print("   ⚠️ SUPABASE_DB_URL is not set in .env. Skipping Supabase ingestion.")
        else:
            try:
                database.init_database()
                shipments = ingestion.load_shipment_rows()
                s_count = ingestion.sync_shipments(shipments)
                print(f"   ✅ Upserted {s_count} shipments into 'shipments' table.")

                kb_rows = ingestion.load_kb_rows()
                if args.limit:
                    kb_rows = kb_rows[:args.limit]
                k_count = ingestion.sync_knowledge(kb_rows)
                print(f"   ✅ Upserted {k_count} knowledge records into 'knowledge_base' table.")
            except Exception as exc:
                print(f"   ❌ Supabase ingestion failed: {exc}")
                return 1

    print("\nIngestion pipeline complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
