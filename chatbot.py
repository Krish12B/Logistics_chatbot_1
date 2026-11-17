"""Shipment support chatbot.

Flow for every user message:
  1. Check the message is not empty.
  2. Look for a shipment ID (e.g. SHP-10001) and fetch that record from the database.
  3. Search the FAQ knowledge base for relevant help text.
  4. Send the system prompt + the retrieved facts + the question to Groq.
  5. Return Groq's answer. If anything fails, return a friendly message instead.
"""
import logging
import re
import sys

import config
from database import get_shipment, init_database
from errors import (
    ChatbotError,
    EmptyMessageError,
    InvalidShipmentIdError,
    LLMUnavailableError,
)
from knowledge_base import search_faqs
from llm_client import call_llm

logger = logging.getLogger("shipment_chatbot")

SYSTEM_PROMPT = """You are ShipBot, the support assistant for SwiftFreight Logistics.
Rules you must always follow:
1. Answer ONLY using the information in the CONTEXT section of the message.
2. Never invent shipment details, dates, locations, or customs decisions.
3. If the CONTEXT does not contain the answer, say you don't have that information
   and suggest contacting the support team.
4. For shipment questions, mention the shipment ID, status, and estimated delivery.
5. Keep answers short (2 to 5 sentences), friendly, and in plain English.
6. Only discuss shipments, customs, delays, and delivery routes. Politely decline anything else.
"""

# Looser pattern: catches "SHP-10001", "shp 10001", "SHP10001", and "SHP-12" (too short)
LOOSE_ID_PATTERN = re.compile(r"\bSHP[-\s]?\d+\b", re.IGNORECASE)
# Strict pattern: a real ID is SHP- followed by exactly 5 digits
VALID_ID_PATTERN = re.compile(r"^SHP-\d{5}$")

HELP_TEXT = (
    "I can help with shipment status, delays, customs, and delivery routes. "
    "Include a shipment ID such as SHP-10001 to get details about a specific shipment."
)


def detect_shipment_id(text):
    """Return a normalised shipment ID found in the text, or None if there is none."""
    match = LOOSE_ID_PATTERN.search(text)
    if match is None:
        return None

    digits = re.search(r"\d+", match.group(0)).group(0)
    shipment_id = f"SHP-{digits}"
    if not VALID_ID_PATTERN.match(shipment_id):
        raise InvalidShipmentIdError(
            f"'{match.group(0).upper()}' doesn't look like a valid shipment ID. "
            "IDs look like SHP-10001 (SHP, a dash, then 5 digits)."
        )
    return shipment_id


def format_shipment(shipment):
    """Turn a database row into plain text the LLM can read."""
    return "\n".join([
        f"Shipment ID: {shipment['shipment_id']}",
        f"Status: {shipment['status']}",
        f"Origin: {shipment['origin']}",
        f"Destination: {shipment['destination']}",
        f"Current location: {shipment['current_location']}",
        f"Route: {shipment['route']}",
        f"Estimated delivery: {shipment['estimated_delivery']}",
        f"Delay reason: {shipment['delay_reason'] or 'None'}",
        f"Customs status: {shipment['customs_status']}",
        f"Last updated: {shipment['last_updated']}",
    ])


def build_context(question):
    """Collect every fact that might help answer the question."""
    parts = []

    shipment_id = detect_shipment_id(question)
    if shipment_id:
        shipment = get_shipment(shipment_id)
        parts.append("SHIPMENT RECORD:\n" + format_shipment(shipment))

    faq_answers = search_faqs(question)
    if faq_answers:
        parts.append("KNOWLEDGE BASE:\n" + "\n".join(faq_answers))

    return "\n\n".join(parts)


def chat(user_message):
    """Answer one user message. Always returns a string and never raises."""
    try:
        if user_message is None or not user_message.strip():
            raise EmptyMessageError()

        question = user_message.strip()
        context = build_context(question)
        if not context:
            return HELP_TEXT

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"CONTEXT:\n{context}\n\nUSER QUESTION: {question}"},
        ]
        answer = call_llm(messages).strip()
        if not answer:
            raise LLMUnavailableError(detail="Groq returned an empty reply")
        return answer

    except ChatbotError as exc:
        logger.warning("Handled error (%s): %s", type(exc).__name__, exc.detail or exc.user_message)
        return exc.user_message

    except Exception:  # Safety net: any bug we did not expect
        logger.exception("Unexpected error while answering a message")
        return "Sorry, something unexpected went wrong on our side. Please try again in a moment."


def main():
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    if not config.GROQ_API_KEY:
        print("Note: GROQ_API_KEY is not set. Shipment questions will return a setup message.")

    try:
        init_database()
    except ChatbotError as exc:
        print(exc.user_message)
        print(f"(technical detail: {exc.detail})")
        return 1

    print("ShipBot is ready. Type your question, or 'exit' to quit.")
    while True:
        try:
            user_input = input("\nYou: ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.strip().lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        print(f"ShipBot: {chat(user_input)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
