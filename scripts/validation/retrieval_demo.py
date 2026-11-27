"""Retrieval demonstration: prints the exact context generated for sample logistics questions."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from logistics_chatbot.core import config
from logistics_chatbot.application.chatbot.orchestrator import build_context

print("=" * 70)
print("FLEETHARBOR LOGISTICS - RETRIEVAL DEMO")
print("=" * 70)

if not config.SUPABASE_DB_URL:
    print("\nℹ️ SUPABASE_DB_URL is not set. Running in local/ChromaDB mode...\n")
else:
    try:
        from logistics_chatbot.infrastructure.database import repository as database
        database.init_database()
        print("Connected to Supabase PostgreSQL.\n")
    except Exception as exc:
        print(f"Warning: Database check: {exc}\n")

questions = [
    "What is the status of SHP-10001?",
    "Why is SHP-10002 delayed?",
    "Has SHP-10003 cleared customs?",
    "What is the delivery route for SHP-10001?",
    "What causes shipment delays?",
]

for question in questions:
    print("=" * 70)
    print("QUESTION:", question)
    print("-" * 70)
    try:
        context = build_context(question)
        print(context if context else "(No context matched)")
    except Exception as exc:
        print(f"(Retrieval failed: {exc})")
    print()
