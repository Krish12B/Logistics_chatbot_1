"""Canonical application entrypoint exposing ASGI `app`, `create_app`, and `cli_main`."""
from __future__ import annotations

import uvicorn

from logistics_chatbot.core import config
from logistics_chatbot.presentation.api.app import app, create_app


def serve(
    host: str = config.SERVER_HOST,
    port: int = config.SERVER_PORT,
    reload: bool = False,
) -> None:
    """Launch the Uvicorn web server hosting the canonical FastAPI application."""
    uvicorn.run("logistics_chatbot.main:app", host=host, port=port, reload=reload)


__all__ = ["app", "create_app", "serve"]

if __name__ == "__main__":
    serve(reload=True)
