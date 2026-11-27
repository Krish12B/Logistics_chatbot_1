"""Chatbot orchestration: single-pass RAG + deterministic fast-path + streaming + CLI."""
from __future__ import annotations

import logging
import re
import sys
from typing import Dict, Iterator, List, Optional

from logistics_chatbot.application.chatbot.classifier import extract_booking_id, extract_employee_id
from logistics_chatbot.application.chatbot.conversation import ConversationStore
from logistics_chatbot.application.chatbot.deterministic_responses import resolve_deterministic_response
from logistics_chatbot.application.chatbot.response_formatter import clean_citation_brackets, map_source_display
from logistics_chatbot.application.prompts.system_prompt import HELP_TEXT, MAX_QUERY_LENGTH, SYSTEM_PROMPT
from logistics_chatbot.application.rag.context_builder import format_context, format_enterprise_shipment_context
from logistics_chatbot.application.rag.retriever import detect_shipment_id, retrieve, search_knowledge
from logistics_chatbot.core import config
from logistics_chatbot.core.constants import STOP_WORDS
from logistics_chatbot.core.errors import (
    ChatbotError,
    EmptyMessageError,
    InvalidShipmentIdError,
    LLMUnavailableError,
    QueryTooLongError,
)
from logistics_chatbot.domain.entities.models import ChatResult, QueryIntent, QueryType, RetrievedContext
from logistics_chatbot.infrastructure.database import repository as database
from logistics_chatbot.infrastructure.llm.groq_client import call_llm, stream_llm

logger = logging.getLogger("logistics_chatbot.orchestrator")

_conversation_store = ConversationStore()


def _has_sufficient_rag_evidence(clean_msg: str, context: Optional[RetrievedContext]) -> bool:
    """Reject weak low-relevance KB noise before invoking LLM when no DB record matched."""
    if context is None:
        return False
    if context.shipment or context.shipment_list:
        return True
    articles = context.knowledge_articles or []
    if not articles:
        return False

    scores: List[float] = []
    for art in articles:
        val = art.get("similarity_score", art.get("score"))
        if isinstance(val, (int, float)):
            scores.append(float(val))

    if not scores:
        return True
    if max(scores) >= 0.38:
        return True

    q_tokens = {t for t in re.findall(r"\b[a-z0-9\-]{3,}\b", clean_msg.lower()) if t not in STOP_WORDS}
    if not q_tokens:
        return False
    combined = " ".join(
        f"{a.get('section_title', '')} {a.get('section_name', '')} {a.get('content', '')}".lower()
        for a in articles
    )
    return any(tok in combined for tok in q_tokens)


def get_conversation_store() -> ConversationStore:
    """Return the global conversation store."""
    return _conversation_store


def build_context(question: str, previous_shipment_id: Optional[str] = None) -> str:
    """Collect and format retrieved facts for a user question."""
    ctx = retrieve(question, previous_shipment_id=previous_shipment_id)
    return format_context(ctx)


def _find_recent_shipment_id(session) -> Optional[str]:
    """Scan recent messages in conversation for previously mentioned shipment ID."""
    if not session or not session.messages:
        return None
    for msg in reversed(session.messages):
        try:
            sid = detect_shipment_id(msg.content)
            if sid:
                return sid
        except InvalidShipmentIdError:
            continue
    return None


def _extract_session_context(session_id: Optional[str]):
    """Retrieve conversation session plus most recent shipment/booking ID & employee ID."""
    session = None
    previous_shipment_id = None
    previous_employee_id = None
    if session_id:
        store = get_conversation_store()
        session = store.get_or_create(session_id)
        if session and session.messages:
            for past_msg in reversed(session.messages):
                if not previous_shipment_id:
                    booking_ref = extract_booking_id(past_msg.content)
                    if booking_ref:
                        previous_shipment_id = booking_ref
                if not previous_shipment_id:
                    try:
                        sid = detect_shipment_id(past_msg.content)
                        if sid:
                            previous_shipment_id = sid
                    except InvalidShipmentIdError:
                        pass
                if not previous_employee_id:
                    eid = extract_employee_id(past_msg.content)
                    if eid:
                        previous_employee_id = eid
                if previous_shipment_id and previous_employee_id:
                    break
    return session, previous_shipment_id, previous_employee_id


def _prepare_rag_prompt(
    clean_msg: str,
    session,
    previous_shipment_id: Optional[str],
):
    """Run RAG retrieve() (or enterprise SQL + ChromaDB hybrid enrichment) once."""
    booking_ref = extract_booking_id(clean_msg)
    if not booking_ref and previous_shipment_id and (
        previous_shipment_id.upper().startswith("ALC-") or len(previous_shipment_id) == 36
    ):
        booking_ref = previous_shipment_id

    if booking_ref:
        ent = database.get_enterprise_shipment(booking_ref)
        if ent:
            rag_query = clean_msg
            low = clean_msg.lower()
            if "delay" in low:
                rag_query = f"{clean_msg} shipment delay causes route risk weather customs carrier reliability"
            elif "custom" in low:
                rag_query = f"{clean_msg} customs clearance export import documentation inspection hs code"
            elif "incoterm" in low:
                rag_query = f"{clean_msg} Incoterms 2020 buyer seller responsibility risk transfer"
            elif ent.get("is_delayed") or "guidance" in low or "recommend" in low:
                rag_query = f"{clean_msg} Allcargo customer support delay causes route risk escalation procedure"

            kb_res = search_knowledge(rag_query, top_k=4)
            articles = kb_res.articles if kb_res else []
            ctx = RetrievedContext(
                intent=QueryIntent(query_type=QueryType.MIXED, raw_query=clean_msg),
                shipment=ent,
                knowledge_articles=articles,
                source_doc_ids=[a.get("doc_id", "DOC") for a in articles if a.get("doc_id")],
            )
            raw_sources = [f"Enterprise Shipment Database ({ent['booking_id']})"] + list(ctx.source_doc_ids)
            ent_block = "ENTERPRISE SHIPMENT DATABASE RECORD:\n" + format_enterprise_shipment_context(ent)
            kb_lines = []
            for a in articles:
                did = a.get("doc_id", "DOC")
                ttl = a.get("section_title") or a.get("title") or ""
                kb_lines.append(f"[{did}] {ttl}\n{a.get('content', '')}")
            kb_block = "KNOWLEDGE BASE:\n" + "\n\n".join(kb_lines) if kb_lines else "KNOWLEDGE BASE:\n(No additional documents matched.)"
            formatted = f"{ent_block}\n\n{kb_block}"

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            if session:
                messages.extend(session.get_recent_messages(max_turns=3))
            messages.append({
                "role": "user",
                "content": (
                    f"CONTEXT:\n{formatted}\n\n"
                    f"USER QUESTION: {clean_msg}\n\n"
                    "FORMAT INSTRUCTIONS: Organize your answer clearly using these headings where applicable: "
                    "### Shipment Information, ### Operational Information, ### Knowledge-Based Explanation, ### Summary. "
                    "Clearly distinguish verified database records from general knowledge base guidance. "
                    "Never invent Incoterms or fields marked not stored in the record."
                ),
            })
            return ctx, formatted, messages, raw_sources

    context = retrieve(clean_msg, previous_shipment_id=previous_shipment_id)
    raw_sources = list(context.source_doc_ids) if context and context.source_doc_ids else []
    if context and getattr(context, "shipment_list", None) and not raw_sources:
        raw_sources.append("Shipment Database Registry")
    formatted = format_context(context) if context else ""
    if not formatted:
        return context, "", [], []

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if session:
        messages.extend(session.get_recent_messages(max_turns=3))
    messages.append({
        "role": "user",
        "content": (
            f"CONTEXT:\n{formatted}\n\n"
            f"USER QUESTION: {clean_msg}\n\n"
            "STRICT GROUNDING RULE: Answer strictly using verified facts in CONTEXT. "
            "Never invent, guess, or extrapolate counts, tracking IDs, locations, fees, or rules not explicitly stated in CONTEXT."
        ),
    })
    return context, formatted, messages, raw_sources


def _is_unavailable_text(text: str) -> bool:
    ans_lower = (text or "").lower()
    return any(
        phrase in ans_lower
        for phrase in (
            "information is not available",
            "not available in the fleetharbor",
            "outside the fleetharbor logistics domain",
            "temporarily unavailable",
            "cannot find",
            "i apologize",
            "sorry, something unexpected went wrong",
            "please contact our support team at support@fleetharbor.com",
        )
    )


def _invoke_llm(messages: List[Dict[str, str]]) -> str:
    """Invoke call_llm cleanly (patchable seam for hybrid tests)."""
    return call_llm(messages)


def generate_response(message: str, session_id: Optional[str] = None) -> ChatResult:
    """Process a user query through deterministic fast-path and single-pass RAG pipeline."""
    if not message or not message.strip():
        raise EmptyMessageError("Message cannot be empty. Please provide a question or shipment query.")

    clean_msg = message.strip()
    max_len = getattr(config, "QUERY_MAX_LENGTH", MAX_QUERY_LENGTH)
    if len(clean_msg) > max_len:
        raise QueryTooLongError()

    session, previous_shipment_id, previous_employee_id = _extract_session_context(session_id)

    det_res = resolve_deterministic_response(
        clean_msg, session, previous_shipment_id, previous_employee_id, db_repo=database
    )
    if det_res is not None:
        return det_res

    context, formatted_ctx, messages, raw_sources = _prepare_rag_prompt(
        clean_msg, session, previous_shipment_id
    )

    if not formatted_ctx or not _has_sufficient_rag_evidence(clean_msg, context):
        unavailable_msg = (
            "I apologize, but that information is not available in the FleetHarbor logistics knowledge base.\n\n"
            "I can help you with shipment tracking, delivery routes, customs clearance documentation, "
            "cold-chain cargo rules, and logistics policies. If you need specialized assistance, "
            "please contact the support team at support@fleetharbor.com."
        )
        if session:
            session.add_message("user", clean_msg)
            session.add_message("assistant", unavailable_msg)
        return ChatResult(response=unavailable_msg, sources=[], response_type="unavailable", shipment_id=None)

    answer = (_invoke_llm(messages) or "").strip()
    if not answer:
        raise LLMUnavailableError(detail="Groq returned an empty reply")

    clean_answer = clean_citation_brackets(answer)

    if _is_unavailable_text(clean_answer):
        if session:
            session.add_message("user", clean_msg, context=formatted_ctx)
            session.add_message("assistant", clean_answer)
        return ChatResult(response=clean_answer, sources=[], response_type="unavailable", shipment_id=None)

    deduped_sources = list(dict.fromkeys(map_source_display(s) for s in raw_sources))
    res_booking_id = (
        context.shipment.get("booking_id")
        if (context and isinstance(context.shipment, dict) and context.shipment.get("booking_id"))
        else None
    )

    if session:
        session.add_message("user", clean_msg, context=formatted_ctx)
        session.add_message("assistant", clean_answer)

    return ChatResult(
        response=clean_answer,
        sources=deduped_sources,
        response_type="hybrid_enterprise_rag" if res_booking_id else "general_knowledge",
        shipment_id=res_booking_id,
    )


def stream_chat_response(message: str, session_id: Optional[str] = None) -> Iterator[dict]:
    """Generator yielding progressive SSE-compatible payload dictionaries."""
    clean_msg = (message or "").strip()
    if not clean_msg:
        msg = "Please type a question about your shipment or logistics operations."
        yield {"token": msg, "done": False}
        yield {"done": True, "response": msg, "sources": [], "response_type": "error"}
        return

    max_len = getattr(config, "QUERY_MAX_LENGTH", MAX_QUERY_LENGTH)
    if len(clean_msg) > max_len:
        msg = f"Query is too long. Please keep queries under {max_len} characters."
        yield {"token": msg, "done": False}
        yield {"done": True, "response": msg, "sources": [], "response_type": "error"}
        return

    try:
        session, previous_shipment_id, previous_employee_id = _extract_session_context(session_id)

        det_res = resolve_deterministic_response(
            clean_msg, session, previous_shipment_id, previous_employee_id, db_repo=database
        )
        if det_res is not None:
            yield {"token": det_res.response, "done": False}
            yield {
                "done": True,
                "response": det_res.response,
                "sources": det_res.sources,
                "response_type": det_res.response_type,
                "shipment_id": det_res.shipment_id,
            }
            return

        context, formatted_ctx, messages, raw_sources = _prepare_rag_prompt(
            clean_msg, session, previous_shipment_id
        )
        if not formatted_ctx or not _has_sufficient_rag_evidence(clean_msg, context):
            unavailable_msg = (
                "I apologize, but that information is not available in the FleetHarbor logistics knowledge base.\n\n"
                "I can help you with shipment tracking, delivery routes, customs clearance documentation, "
                "cold-chain cargo rules, and logistics policies. If you need specialized assistance, "
                "please contact the support team at support@fleetharbor.com."
            )
            if session:
                session.add_message("user", clean_msg)
                session.add_message("assistant", unavailable_msg)
            yield {"token": unavailable_msg, "done": False}
            yield {"done": True, "response": unavailable_msg, "sources": [], "response_type": "unavailable", "shipment_id": None}
            return

        accumulated_chunks: List[str] = []
        for token_chunk in stream_llm(messages):
            accumulated_chunks.append(token_chunk)
            yield {"token": token_chunk, "done": False}

        full_raw_text = "".join(accumulated_chunks)
        clean_text = clean_citation_brackets(full_raw_text)

        if _is_unavailable_text(clean_text):
            final_sources: List[str] = []
            final_type = "unavailable"
            res_booking_id = None
        else:
            final_sources = list(dict.fromkeys(map_source_display(s) for s in raw_sources))
            res_booking_id = (
                context.shipment.get("booking_id")
                if (context and isinstance(context.shipment, dict) and context.shipment.get("booking_id"))
                else None
            )
            final_type = "hybrid_enterprise_rag" if res_booking_id else "general_knowledge"

        if session:
            session.add_message("user", clean_msg, context=formatted_ctx)
            session.add_message("assistant", clean_text)

        yield {
            "done": True,
            "response": clean_text,
            "sources": final_sources,
            "response_type": final_type,
            "shipment_id": res_booking_id,
        }

    except ChatbotError as exc:
        logger.warning("Handled chatbot error during stream: %s", exc.detail or exc.user_message)
        yield {"token": exc.user_message, "done": False}
        yield {"done": True, "response": exc.user_message, "sources": [], "response_type": "error", "shipment_id": None}

    except Exception as exc:
        logger.exception("Unexpected error during chat stream: %s", exc)
        err_msg = "An operational error occurred while generating your answer. Please try again."
        yield {"token": err_msg, "done": False}
        yield {"done": True, "response": err_msg, "sources": [], "response_type": "error", "shipment_id": None}


def chat(message: str, session_id: Optional[str] = None) -> str:
    """Convenience single-string chat wrapper."""
    return generate_response(message, session_id=session_id).response


def rag_chat(user_message: Optional[str], session_id: Optional[str] = None) -> str:
    """Classic RAG-only chat pipeline (always grounds via build_context + LLM, never raises)."""
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
            messages.extend(session.get_recent_messages(max_turns=3))
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


def main() -> int:
    """Interactive terminal CLI entry point."""
    from logistics_chatbot.core.logging import configure_logging

    configure_logging(level=logging.WARNING, quiet_third_party=True)

    if not config.GROQ_API_KEY:
        print("Warning: GROQ_API_KEY is not set. LLM responses will not work.")

    if config.SUPABASE_DB_URL:
        try:
            database.init_database()
            print("Connected to Supabase PostgreSQL.")
        except Exception as exc:
            print(f"Warning: Database check: {exc}")
    else:
        print("Running in local mode (using SQLite/CSV & ChromaDB).")
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
