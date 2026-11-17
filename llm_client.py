"""Talks to the Groq API. Turns every Groq failure into one of our own error types."""
import config
from errors import LLMAuthError, LLMTimeoutError, LLMUnavailableError


def call_llm(messages):
    """Send chat messages to Groq and return the reply text."""
    if not config.GROQ_API_KEY:
        raise LLMAuthError(detail="GROQ_API_KEY environment variable is not set")

    try:
        from groq import (
            APIConnectionError,
            APIStatusError,
            APITimeoutError,
            AuthenticationError,
            Groq,
        )
    except ImportError as exc:
        raise LLMUnavailableError(detail="The 'groq' package is not installed") from exc

    client = Groq(api_key=config.GROQ_API_KEY, timeout=config.LLM_TIMEOUT_SECONDS)

    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=config.MAX_ANSWER_TOKENS,
        )
    # Order matters: APITimeoutError is a subclass of APIConnectionError,
    # so it must be checked first.
    except APITimeoutError as exc:
        raise LLMTimeoutError(detail=str(exc)) from exc
    except AuthenticationError as exc:
        raise LLMAuthError(detail=str(exc)) from exc
    except APIConnectionError as exc:
        raise LLMUnavailableError(detail=f"No connection to Groq: {exc}") from exc
    except APIStatusError as exc:
        raise LLMUnavailableError(detail=f"Groq returned an error: {exc}") from exc

    return response.choices[0].message.content or ""
