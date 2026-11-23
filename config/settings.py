"""Application settings and centralized configuration."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root and src/ are in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE if ENV_FILE.exists() else None)

class Settings:
    """Centralized configuration settings."""
    PROJECT_NAME: str = "AI-Powered Chatbot for the Logistics Industry"
    VERSION: str = "1.0.0"
    API_PREFIX: str = ""

    # Paths
    PROJECT_ROOT: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    KB_DATA_DIR: Path = DATA_DIR / "knowledge_base"
    CHROMA_PERSIST_DIRECTORY: Path = DATA_DIR / "chroma_db"

    # Datasets
    SHIPMENTS_CSV_PATH: Path = PROCESSED_DATA_DIR / "shipments.csv"
    KB_CSV_PATH: Path = KB_DATA_DIR / "kb_long.csv"
    LEGACY_FAQ_PATH: Path = KB_DATA_DIR / "knowledge_base.json"

    # Groq API
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    MAX_ANSWER_TOKENS: int = int(os.getenv("MAX_ANSWER_TOKENS", "512"))
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "30.0"))

    # Embeddings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIM: int = 384

    # ChromaDB
    CHROMA_MODE: str = os.getenv("CHROMA_MODE", "persistent")
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "logistics_knowledge_chunks")
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))
    CHROMA_SSL: bool = os.getenv("CHROMA_SSL", "false").lower() == "true"

    # Supabase (optional)
    SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Retrieval
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    RETRIEVAL_MIN_SCORE: float = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.3"))

settings = Settings()
