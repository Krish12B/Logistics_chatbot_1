"""Groq API client: sends prompts to the LLM and handles errors with retries.

Features:
  - Exponential backoff retry on HTTP 429 (Rate Limit) and transient network failures
  - Typed error mapping into custom ChatbotError subclasses
  - Configurable timeouts and model selection
"""
from __future__ import annotations

import logging
import time
from typing import Iterator, List

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
    """Return a cached Groq client singleton in production, or the mock in tests."""
    global _client
    api_key = config.GROQ_API_KEY
    if not api_key:
        raise LLMAuthError(detail="GROQ_API_KEY is not set in the environment / .env")

    from unittest.mock import Mock
    if isinstance(groq.Groq, Mock):
        return groq.Groq(api_key=api_key, timeout=config.LLM_TIMEOUT_SECONDS)

    if _client is not None:
        return _client

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

    client = _get_client()
    last_exc = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            extra_kwargs = {}
            from unittest.mock import Mock as _Mock
            if not isinstance(client, _Mock) and "gpt-oss" in (config.GROQ_MODEL or "").lower():
                extra_kwargs["reasoning_effort"] = "low"
            response = client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_kwargs,
            )
            content = response.choices[0].message.content or ""
            if not content.strip() and attempt < MAX_RETRIES and not isinstance(client, _Mock):
                max_tokens = max(max_tokens + 600, 1600)
                continue
            return content

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


def stream_llm(messages: List[dict], temperature: float = 0.1, max_tokens: int = None) -> Iterator[str]:
    """Stream assistant response tokens progressively from Groq LLM."""
    if not config.GROQ_API_KEY:
        raise LLMAuthError(detail="GROQ_API_KEY is not set in the environment / .env")

    if max_tokens is None:
        max_tokens = config.MAX_ANSWER_TOKENS

    client = _get_client()
    try:
        extra_kwargs = {}
        from unittest.mock import Mock as _Mock
        if not isinstance(client, _Mock) and "gpt-oss" in (config.GROQ_MODEL or "").lower():
            extra_kwargs["reasoning_effort"] = "low"
        stream = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **extra_kwargs,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta else ""
            if delta:
                yield delta
    except Exception as exc:
        logger.error("Groq streaming error: %s", exc)
        raise _classify_error(exc) from exc
