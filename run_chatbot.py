"""Launch the interactive CLI chat loop for the NexusFreight / FleetHarbor Logistics AI Chatbot."""
from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from logistics_chatbot.application.chatbot.orchestrator import main  # noqa: E402

if __name__ == "__main__":
    main()
