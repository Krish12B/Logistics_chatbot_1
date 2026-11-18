"""Convenience runner for the FleetHarbor Logistics FastAPI server."""
import sys
from pathlib import Path
import uvicorn

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

if __name__ == "__main__":
    uvicorn.run("logistics_chatbot.api.app:app", host="127.0.0.1", port=8000, reload=True)
