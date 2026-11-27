"""Diagnostic and connectivity verification utility."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from logistics_chatbot.core import config
from logistics_chatbot.infrastructure.vector_store import chroma_store as chroma_db

print("=" * 60)
print("FLEETHARBOR LOGISTICS CHATBOT - CONNECTIVITY CHECK")
print("=" * 60)

# 1. Configuration Check
print("\n── 1. Configuration & Secrets ──")
groq_ok = bool(config.GROQ_API_KEY and not config.GROQ_API_KEY.startswith("your_"))
db_url_ok = bool(config.SUPABASE_DB_URL and "user:password" not in config.SUPABASE_DB_URL)

print(f"  GROQ_API_KEY:    {'✅ CONFIGURED' if groq_ok else '❌ NOT SET'}")
print(f"  GROQ_MODEL:      {config.GROQ_MODEL}")
print(f"  SUPABASE_DB_URL: {'✅ CONFIGURED' if db_url_ok else '⚠️ NOT SET (using local datasets)'}")
print(f"  EMBEDDING_MODEL: {config.EMBEDDING_MODEL} (dim={config.EMBEDDING_DIM})")
print(f"  CHROMA_MODE:     {config.CHROMA_MODE}")

# 2. ChromaDB Health Check
print("\n── 2. ChromaDB Vector Database ──")
try:
    c_health = chroma_db.check_chroma_health()
    print(f"  Status:          {'✅ HEALTHY' if c_health['status'] == 'healthy' else '❌ UNHEALTHY'}")
    print(f"  Heartbeat:       {c_health.get('heartbeat')}")
    print(f"  Collection:      {c_health.get('collection_name')}")
    print(f"  Record Count:    {c_health.get('record_count')}")
    print(f"  Persist Dir:     {c_health.get('persist_directory')}")
except Exception as exc:
    print(f"  ❌ ChromaDB check failed: {exc}")

# 3. Active Datasets Check
print("\n── 3. Active Datasets ──")
files = [
    ("kb_long.csv (primary KB)", config.KB_CSV_PATH),
    ("shipments.csv (primary)", config.SHIPMENTS_CSV_PATH),
    ("knowledge_base.json (legacy)", config.LEGACY_FAQ_PATH),
    ("shipments_seed.json (seed)", config.SHIPMENT_SEED_PATH),
    ("schema.sql (migration)", config.MIGRATIONS_SQL_DIR / "schema.sql"),
]
for label, p in files:
    status = "✅" if p.exists() else "❌"
    size = f"({p.stat().st_size:,} bytes)" if p.exists() else "(missing)"
    print(f"  {label:<30} {status} {p.name} {size}")

# 4. Database Check
print("\n── 4. Supabase PostgreSQL ──")
if db_url_ok:
    try:
        from logistics_chatbot.infrastructure.database import repository as database
        database.init_database()
        print("  ✅ Successfully connected to Supabase PostgreSQL and verified schema!")
    except Exception as exc:
        print(f"  ❌ Database check failed: {exc}")
else:
    print("  ℹ️ Set SUPABASE_DB_URL in .env to connect to live Supabase PostgreSQL.")
