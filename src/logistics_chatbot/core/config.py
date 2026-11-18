"""Core settings and configuration for the FleetHarbor Logistics AI Chatbot.

Values are dynamically loaded from environment variables and .env,
with fallbacks supporting zero-cloud local execution.
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Path anchors
CORE_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = CORE_DIR.parent
SRC_DIR = PACKAGE_DIR.parent
PROJECT_ROOT = SRC_DIR.parent

# Load .env: check project root first, then package dir
_env_root = PROJECT_ROOT / ".env"
_env_pkg = PACKAGE_DIR / ".env"
load_dotenv(_env_root if _env_root.exists() else _env_pkg)

# ── Data Directories ────────────────────────────────────────────────
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
KB_DATA_DIR = DATA_DIR / "knowledge_base"

# ── Operational Datasets ────────────────────────────────────────────
def _resolve_first(*candidates: Path) -> Path:
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]

SHIPMENTS_CSV_PATH = _resolve_first(
    PROCESSED_DATA_DIR / "shipments.csv",
    RAW_DATA_DIR / "shipments.csv",
    DATA_DIR / "shipments.csv",
)

SHIPMENT_SEED_PATH = _resolve_first(
    RAW_DATA_DIR / "shipments_seed.json",
    DATA_DIR / "shipments_seed.json",
)

SHIPMENT_PATH = SHIPMENTS_CSV_PATH if SHIPMENTS_CSV_PATH.exists() else SHIPMENT_SEED_PATH

DB_PATH = Path(os.getenv("SHIPMENT_DB_PATH", str(RAW_DATA_DIR / "shipments.db")))

# ── Knowledge Base Datasets ─────────────────────────────────────────
KB_CSV_PATH = _resolve_first(
    KB_DATA_DIR / "kb_long.csv",
    DATA_DIR / "kb_long.csv",
    KB_DATA_DIR / "knowledge_base.csv",
    DATA_DIR / "knowledge_base.csv",
)

LEGACY_FAQ_PATH = _resolve_first(
    KB_DATA_DIR / "knowledge_base.json",
    DATA_DIR / "knowledge_base.json",
)

KNOWLEDGE_BASE_CSV_PATH = _resolve_first(
    KB_DATA_DIR / "knowledge_base.csv",
    DATA_DIR / "knowledge_base.csv",
)
KNOWLEDGE_BASE_PATH = LEGACY_FAQ_PATH

# ── Groq LLM Settings ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "15"))
MAX_ANSWER_TOKENS = int(os.getenv("MAX_ANSWER_TOKENS", "400"))

# ── Supabase PostgreSQL Settings ───────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "")
DB_POOL_MIN_CONN = int(os.getenv("DB_POOL_MIN_CONN", "1"))
DB_POOL_MAX_CONN = int(os.getenv("DB_POOL_MAX_CONN", "5"))
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))

# ── Embedding Model Settings ────────────────────────────────────────
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_DIM = 384

# ── Retrieval Tuning ────────────────────────────────────────────────
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
RETRIEVAL_MIN_SCORE = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.3"))
VECTOR_STORE = os.getenv("VECTOR_STORE", "auto").lower()

# ── ChromaDB Settings ──────────────────────────────────────────────
CHROMA_MODE = os.getenv("CHROMA_MODE", "persistent").lower()
CHROMA_PERSIST_DIRECTORY = Path(os.getenv("CHROMA_PERSIST_DIRECTORY", str(DATA_DIR / "chroma_db")))
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_SSL = os.getenv("CHROMA_SSL", "false").lower() in ("true", "1", "yes")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "logistics_knowledge_chunks")
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY", "")
CHROMA_TENANT = os.getenv("CHROMA_TENANT", "")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE", "")
