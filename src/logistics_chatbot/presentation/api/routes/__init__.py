"""Route package aggregating HTTP endpoint routers."""
from logistics_chatbot.presentation.api.routes import (
    chat,
    documents,
    employees,
    health,
    shipments,
    web,
)

__all__ = ["chat", "documents", "employees", "health", "shipments", "web"]
