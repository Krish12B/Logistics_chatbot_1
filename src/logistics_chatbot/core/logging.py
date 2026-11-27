"""Centralized structured logging configuration."""
from __future__ import annotations

import logging
import os

_DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_NOISY_LOGGERS = (
    "httpx",
    "sentence_transformers",
    "transformers",
    "urllib3",
    "huggingface_hub",
    "chromadb",
)


def configure_logging(level: str | int | None = None, quiet_third_party: bool = False) -> logging.Logger:
    """Configure application-wide logging cleanly and idempotently."""
    resolved_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=resolved_level, format=_DEFAULT_FORMAT)
    if quiet_third_party:
        for name in _NOISY_LOGGERS:
            logging.getLogger(name).setLevel(logging.ERROR)
    return logging.getLogger("logistics_chatbot")


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under logistics_chatbot."""
    if name.startswith("logistics_chatbot"):
        return logging.getLogger(name)
    return logging.getLogger(f"logistics_chatbot.{name}")
