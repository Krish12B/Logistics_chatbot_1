"""Launch the NexusFreight / FleetHarbor Logistics AI Chatbot FastAPI web server."""
from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from logistics_chatbot.main import serve  # noqa: E402

if __name__ == "__main__":
    serve(host="127.0.0.1", port=8000, reload=True)
