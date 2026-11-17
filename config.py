"""Settings for the chatbot.

Values come from environment variables when they are set,
otherwise the defaults below are used.
"""
from dotenv import load_dotenv
load_dotenv()
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Where the data lives
DB_PATH = Path(os.getenv("SHIPMENT_DB_PATH", str(DATA_DIR / "shipments.db")))
KNOWLEDGE_BASE_PATH = DATA_DIR / "knowledge_base.json"
SHIPMENT_SEED_PATH = DATA_DIR / "shipments_seed.json"

# Groq (LLM) settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "15"))
MAX_ANSWER_TOKENS = 400
