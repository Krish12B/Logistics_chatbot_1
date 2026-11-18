"""Shipment support chatbot - Groq LLM + ChromaDB / Supabase RAG edition.

Architecture:
  - Retrieval layer: logistics_chatbot.rag.retrieval
  - Memory layer: logistics_chatbot.chatbot.conversation
  - LLM layer: logistics_chatbot.chatbot.llm_client
  - Data layer: logistics_chatbot.database.database
  - Vector layer: logistics_chatbot.vectorstores.chroma_db
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

# Ensure src/ is discoverable even when executed directly via VS Code "Run" button
_SRC_DIR = Path(__file__).resolve().parents[2]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from logistics_chatbot.core import config
from logistics_chatbot.core.errors import (
    ChatbotError,
    EmptyMessageError,
    LLMUnavailableError,
    QueryTooLongError,
)
from logistics_chatbot.core.prompts import HELP_TEXT, MAX_QUERY_LENGTH, SYSTEM_PROMPT
from logistics_chatbot.database import database
from logistics_chatbot.chatbot.conversation import ConversationStore
from logistics_chatbot.chatbot.llm_client import call_llm
from logistics_chatbot.rag.retrieval import (
    detect_shipment_id,
    format_context,
    retrieve,
)

logger = logging.getLogger("logistics_chatbot")

_conversation_store = ConversationStore()


def get_conversation_store() -> ConversationStore:
    """Return the global conversation store."""
    return _conversation_store


def build_context(
    question: str,
    previous_shipment_id: Optional[str] = None,
) -> str:
    """Collect every fact that might help answer the question."""
    ctx = retrieve(question, previous_shipment_id=previous_shipment_id)
    return format_context(ctx)


def _find_recent_shipment_id(session) -> Optional[str]:
    """Scan recent messages in conversation for previously mentioned shipment ID."""
    if not session or not session.messages:
        return None
    for msg in reversed(session.messages):
        sid = detect_shipment_id(msg.content)
        if sid:
            return sid
    return None


def chat(user_message: str | None, session_id: Optional[str] = None) -> str:
    """Answer one user message. Always returns a string and never raises.

    Args:
        user_message: The text of the user's question.
        session_id: Optional session identifier for multi-turn conversation memory.

    Returns:
        The assistant's grounded answer or a friendly error message.
    """
    try:
        if user_message is None or not user_message.strip():
            raise EmptyMessageError()

        question = user_message.strip()

        if len(question) > MAX_QUERY_LENGTH:
            raise QueryTooLongError()

        session = None
        previous_shipment_id = None
        if session_id:
            session = _conversation_store.get_or_create(session_id)
            previous_shipment_id = _find_recent_shipment_id(session)

        context = build_context(question, previous_shipment_id=previous_shipment_id)
        if not context:
            return HELP_TEXT

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if session:
            history = session.get_recent_messages(max_turns=3)
            messages.extend(history)

        messages.append({
            "role": "user",
            "content": f"CONTEXT:\n{context}\n\nUSER QUESTION: {question}",
        })

        answer = call_llm(messages).strip()
        if not answer:
            raise LLMUnavailableError(detail="Groq returned an empty reply")

        if session:
            session.add_message("user", question, context=context)
            session.add_message("assistant", answer)

        return answer

    except ChatbotError as exc:
        logger.warning("Handled error (%s): %s", type(exc).__name__, exc.detail or exc.user_message)
        return exc.user_message

    except Exception:
        logger.exception("Unexpected error while answering a message")
        return "Sorry, something unexpected went wrong on our side. Please try again in a moment."


def main():
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    for noisy in ("httpx", "sentence_transformers", "transformers", "urllib3", "huggingface_hub", "chromadb"):
        logging.getLogger(noisy).setLevel(logging.ERROR)

    if not config.GROQ_API_KEY:
        print("Warning: GROQ_API_KEY is not set. LLM responses will not work.")

    if config.SUPABASE_DB_URL:
        try:
            database.init_database()
            print("Connected to Supabase PostgreSQL.")
        except Exception as exc:
            print(f"Warning: Database check: {exc}")
    else:
        print("Running in local mode (using data/shipments.csv & data/knowledge_base/kb_long.csv).")
        print("Set SUPABASE_DB_URL in .env to connect to live Supabase PostgreSQL.")

    print(f"ShipBot is ready! (LLM: Groq {config.GROQ_MODEL})")
    print("Type your question, or 'exit' to quit.\n")

    cli_session_id = _conversation_store.new_session_id()

    while True:
        try:
            user_input = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.strip().lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        print(f"ShipBot: {chat(user_input, session_id=cli_session_id)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
