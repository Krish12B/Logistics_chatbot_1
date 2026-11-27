"""Database setup utility: executes SQL migrations in Supabase PostgreSQL."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from logistics_chatbot.core import config
from logistics_chatbot.infrastructure.database import repository as database

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("setup_database")


def main():
    print("=" * 65)
    print("FLEETHARBOR LOGISTICS - DATABASE SETUP & MIGRATION")
    print("=" * 65)

    if not config.SUPABASE_DB_URL:
        print("\n⚠️ SUPABASE_DB_URL is not set in your .env file.")
        print("To apply SQL schema to Supabase, configure SUPABASE_DB_URL in .env.")
        print("Schema file is available at: migrations/sql/schema.sql\n")
        return 0

    sql_file = config.MIGRATIONS_SQL_DIR / "schema.sql"
    if not sql_file.exists():
        sql_file = _ROOT / "migrations" / "sql" / "schema.sql"

    print(f"Reading schema from: {sql_file.name}...")
    sql_content = sql_file.read_text(encoding="utf-8")

    try:
        conn = database._get_connection()
        with conn.cursor() as cur:
            cur.execute(sql_content)
        print("✅ Schema migrations applied successfully to Supabase PostgreSQL.")
        database.init_database()
        print("✅ Database verification passed: shipments, knowledge_base, match_knowledge active.")
        return 0
    except Exception as exc:
        print(f"❌ Migration failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
