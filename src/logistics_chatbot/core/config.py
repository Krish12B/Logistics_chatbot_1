"""Canonical settings and configuration for NexusFreight / FleetHarbor Logistics AI Chatbot.

Unifies all application paths, LLM settings, database connections, embedding settings,
ChromaDB storage, retrieval thresholds, server options, and logging settings.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# ── Path Anchors ─────────────────────────────────────────────────────
CORE_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = CORE_DIR.parent
SRC_DIR = PACKAGE_DIR.parent
PROJECT_ROOT = SRC_DIR.parent

# Load .env: check project root first, then package dir
_env_root = PROJECT_ROOT / ".env"
_env_pkg = PACKAGE_DIR / ".env"
load_dotenv(_env_root if _env_root.exists() else (_env_pkg if _env_pkg.exists() else None))


def _resolve_first(*candidates: Path) -> Path:
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


# ── Frontend & Documentation Directories ─────────────────────────────
FRONTEND_DIR = PROJECT_ROOT / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
STATIC_DIR = FRONTEND_DIR / "static"
DOCS_DIR = PROJECT_ROOT / "docs"
MIGRATIONS_SQL_DIR = PROJECT_ROOT / "migrations" / "sql"
REPORTS_DIR = _resolve_first(PROJECT_ROOT / "reports", PROJECT_ROOT / "tests" / "reports")

# ── Data Directories ─────────────────────────────────────────────────
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
GENERATED_DATA_DIR = DATA_DIR / "generated"
KB_DATA_DIR = DATA_DIR / "knowledge_base"
KB_MANUALS_DIR = _resolve_first(KB_DATA_DIR / "manuals", PROJECT_ROOT / "knowledge_base")
SOURCE_DOCS_DIR = _resolve_first(DATA_DIR / "source_documents", DATA_DIR / "new_data")
SQL_SEED_DIR = DATA_DIR / "sql"

# ── Operational Datasets & SQLite Storage ────────────────────────────
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

_raw_db_path = Path(os.getenv("SHIPMENT_DB_PATH", str(RAW_DATA_DIR / "shipments.db")))
DB_PATH = _raw_db_path if _raw_db_path.is_absolute() else (PROJECT_ROOT / _raw_db_path)

EMPLOYEES_CSV_PATH = _resolve_first(
    GENERATED_DATA_DIR / "employees_roster.csv",
    DATA_DIR / "employees_roster.csv",
)

# ── Knowledge Base Datasets ──────────────────────────────────────────
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

# ── Groq LLM Settings ────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
MAX_ANSWER_TOKENS = int(os.getenv("MAX_ANSWER_TOKENS", "1024"))
QUERY_MAX_LENGTH = int(os.getenv("QUERY_MAX_LENGTH", "2000"))

# ── Supabase PostgreSQL Settings ─────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "")
DB_POOL_MIN_CONN = int(os.getenv("DB_POOL_MIN_CONN", "1"))
DB_POOL_MAX_CONN = int(os.getenv("DB_POOL_MAX_CONN", "5"))
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))

# ── Embedding Model Settings ─────────────────────────────────────────
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_DIM = 384

# ── Retrieval Tuning ─────────────────────────────────────────────────
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
RETRIEVAL_MIN_SCORE = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.3"))
VECTOR_STORE = os.getenv("VECTOR_STORE", "auto").lower()

# ── ChromaDB Settings ────────────────────────────────────────────────
CHROMA_MODE = os.getenv("CHROMA_MODE", "persistent").lower()
_raw_chroma_dir = Path(os.getenv("CHROMA_PERSIST_DIRECTORY", str(DATA_DIR / "chroma_db")))
CHROMA_PERSIST_DIRECTORY = _raw_chroma_dir if _raw_chroma_dir.is_absolute() else (PROJECT_ROOT / _raw_chroma_dir)
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_SSL = os.getenv("CHROMA_SSL", "false").lower() in ("true", "1", "yes")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "logistics_knowledge_chunks")
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY", "")
CHROMA_TENANT = os.getenv("CHROMA_TENANT", "")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE", "")

# ── Server, Session & Upload Settings ────────────────────────────────
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024)))

# ── Hugging Face / Transformers Offline Optimization ─────────────────
if "HF_HUB_OFFLINE" not in os.environ:
    os.environ["HF_HUB_OFFLINE"] = "1"
if "TRANSFORMERS_OFFLINE" not in os.environ:
    os.environ["TRANSFORMERS_OFFLINE"] = "1"


@dataclass(frozen=True)
class SettingsSnapshot:
    """Immutable view of configuration settings for diagnostics."""
    project_name: str = "NexusFreight / FleetHarbor Logistics AI Chatbot"
    version: str = "2.0.0"
    project_root: Path = PROJECT_ROOT
    data_dir: Path = DATA_DIR
    frontend_dir: Path = FRONTEND_DIR
    db_path: Path = DB_PATH
    chroma_persist_directory: Path = CHROMA_PERSIST_DIRECTORY
    chroma_collection_name: str = CHROMA_COLLECTION_NAME
    groq_model: str = GROQ_MODEL
    embedding_model: str = EMBEDDING_MODEL
    embedding_dim: int = EMBEDDING_DIM
    retrieval_top_k: int = RETRIEVAL_TOP_K
    retrieval_min_score: float = RETRIEVAL_MIN_SCORE
    vector_store: str = VECTOR_STORE


def get_settings() -> SettingsSnapshot:
    """Return a current snapshot reflecting runtime environment/config attributes."""
    return SettingsSnapshot(
        db_path=DB_PATH,
        chroma_persist_directory=CHROMA_PERSIST_DIRECTORY,
        chroma_collection_name=CHROMA_COLLECTION_NAME,
        groq_model=GROQ_MODEL,
        embedding_model=EMBEDDING_MODEL,
        retrieval_top_k=RETRIEVAL_TOP_K,
        retrieval_min_score=RETRIEVAL_MIN_SCORE,
        vector_store=VECTOR_STORE,
    )
