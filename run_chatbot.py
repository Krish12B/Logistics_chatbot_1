"""Convenience runner for the interactive FleetHarbor Logistics Chatbot CLI."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from logistics_chatbot.chatbot.chatbot import main

if __name__ == "__main__":
    sys.exit(main())
