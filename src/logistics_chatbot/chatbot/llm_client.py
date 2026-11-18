"""Groq API client: sends prompts to the LLM and handles errors with retries.

Features:
  - Exponential backoff retry on HTTP 429 (Rate Limit) and transient network failures
  - Typed error mapping into custom ChatbotError subclasses
  - Configurable timeouts and model selection
"""
from __future__ import annotations

import logging
import time
from typing import List

import groq
import httpx

from logistics_chatbot.core import config
from logistics_chatbot.core.errors import (
    LLMAuthError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUnavailableError,
)

logger = logging.getLogger("logistics_chatbot.llm_client")

_client = None

MAX_RETRIES = 2
INITIAL_BACKOFF_SECONDS = 1.0


def _get_client() -> groq.Groq:
    """Return a cached Groq client."""
    global _client
    if _client is not None:
        return _client

    api_key = config.GROQ_API_KEY
    if not api_key:
        raise LLMAuthError(detail="GROQ_API_KEY is not set in the environment / .env")

    _client = groq.Groq(
        api_key=api_key,
        timeout=config.LLM_TIMEOUT_SECONDS,
    )
    return _client


def _classify_error(exc: Exception) -> Exception:
    """Translate third-party exceptions into our custom typed errors."""
    if isinstance(exc, (LLMAuthError, LLMRateLimitError, LLMTimeoutError, LLMUnavailableError)):
        return exc

    if isinstance(exc, groq.AuthenticationError):
        return LLMAuthError(detail=f"Groq 401 Authentication failed: {exc}")

    if isinstance(exc, groq.RateLimitError):
        return LLMRateLimitError(detail=f"Groq 429 Rate limit exceeded: {exc}")

    if isinstance(exc, (groq.APITimeoutError, httpx.TimeoutException)):
        return LLMTimeoutError(detail=f"Groq API timeout: {exc}")

    if isinstance(exc, (groq.APIConnectionError, httpx.NetworkError)):
        return LLMUnavailableError(detail=f"Groq network/connection error: {exc}")

    if isinstance(exc, groq.APIStatusError):
        status = getattr(exc, "status_code", None)
        if status == 401:
            return LLMAuthError(detail=f"Groq status 401: {exc}")
        if status == 429:
            return LLMRateLimitError(detail=f"Groq status 429: {exc}")
        if status and status >= 500:
            return LLMUnavailableError(detail=f"Groq upstream {status}: {exc}")

    return LLMUnavailableError(detail=f"Unexpected LLM error: {type(exc).__name__}: {exc}")


def call_llm(messages: List[dict], temperature: float = 0.1, max_tokens: int = None) -> str:
    """Send a list of chat messages to Groq and return the assistant reply."""
    if not config.GROQ_API_KEY:
        raise LLMAuthError(detail="GROQ_API_KEY is not set in the environment / .env")

    if max_tokens is None:
        max_tokens = config.MAX_ANSWER_TOKENS

    client = groq.Groq(
        api_key=config.GROQ_API_KEY,
        timeout=config.LLM_TIMEOUT_SECONDS,
    )
    last_exc = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""

        except groq.APITimeoutError as exc:
            raise LLMTimeoutError(detail=f"Groq API timeout: {exc}") from exc

        except groq.AuthenticationError as exc:
            raise LLMAuthError(detail=f"Groq 401 Authentication failed: {exc}") from exc

        except groq.APIConnectionError as exc:
            raise LLMUnavailableError(detail=f"Groq connection error: {exc}") from exc

        except (groq.RateLimitError, httpx.NetworkError) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                sleep_time = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                logger.warning(
                    "Groq call failed (attempt %d/%d): %s. Retrying in %.1fs...",
                    attempt + 1,
                    MAX_RETRIES + 1,
                    exc,
                    sleep_time,
                )
                time.sleep(sleep_time)
            else:
                logger.error("Groq call exhausted all %d retries: %s", MAX_RETRIES + 1, exc)
                raise _classify_error(exc) from exc

        except Exception as exc:
            logger.error("Groq non-retryable error: %s", exc)
            raise _classify_error(exc) from exc

    if last_exc:
        raise _classify_error(last_exc)
    raise LLMUnavailableError(detail="No response received from Groq LLM")
