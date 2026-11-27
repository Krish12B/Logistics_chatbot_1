"""Application employee use-case service."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from logistics_chatbot.core.errors import ShipmentNotFoundError
from logistics_chatbot.infrastructure.database import repository

logger = logging.getLogger("logistics_chatbot.services.employee")


def lookup_employee_by_id(employee_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve an employee record by ID (e.g., EMP-20001) or None if not found."""
    clean_id = (employee_id or "").strip().upper()
    if not clean_id:
        return None
    try:
        return repository.get_employee(clean_id)
    except ShipmentNotFoundError:
        return None
    except Exception as exc:
        logger.error("Error retrieving employee %s: %s", clean_id, exc)
        return None


def list_employees(
    department: Optional[str] = None,
    hub: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """List employees filtered by department or hub."""
    return repository.list_employees(department=department, hub=hub, limit=limit)
