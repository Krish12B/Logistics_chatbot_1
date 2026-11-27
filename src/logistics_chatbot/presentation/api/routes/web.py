"""Web landing UI and static entry routes."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from logistics_chatbot.core import config
from logistics_chatbot.presentation.api.dependencies import get_api_endpoints

router = APIRouter(tags=["system"])


@router.get("/", summary="Web Chat UI & API Landing Page")
async def root_endpoint(request: Request):
    """Serve the interactive web chat UI in browsers or API catalog for JSON clients."""
    accept = request.headers.get("accept", "")
    if "application/json" in accept and "text/html" not in accept:
        return JSONResponse(
            content={
                "success": True,
                "message": "Logistics AI Chatbot API is online. Visit /docs for Swagger UI.",
                "data": get_api_endpoints(),
            }
        )

    index_path = config.TEMPLATES_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse(
            content="<h1>FleetHarbor AI</h1><p>Frontend template not found.</p>",
            status_code=500,
        )
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Return empty 204 so browsers do not log 404 favicon noise."""
    return Response(status_code=204)
