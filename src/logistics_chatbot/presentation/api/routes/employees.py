"""Employee directory lookup HTTP routes."""
from __future__ import annotations

import logging
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query

from logistics_chatbot.application.services import employee_service

logger = logging.getLogger("logistics_chatbot.api.employees")
router = APIRouter(tags=["employee"])

_EMPLOYEE_ID_RE = re.compile(r"^EMP-[A-Za-z0-9_-]+$", re.IGNORECASE)


@router.get(
    "/employee/{id}",
    summary="Retrieve employee details by ID",
    description="Fetches full name, department, job title, assigned hub, shift, certification, email, and extension.",
)
async def get_employee_endpoint(
    id: str = Path(
        ...,
        description="Unique employee identifier, e.g. EMP-20001",
        json_schema_extra={"examples": ["EMP-20001"]},
    )
):
    """Return employee profile for a valid EMP-* identifier."""
    clean_id = (id or "").strip().upper()
    if not clean_id or not _EMPLOYEE_ID_RE.match(clean_id):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid employee ID format: '{id}'. Expected format like EMP-20001.",
        )

    emp = employee_service.lookup_employee_by_id(clean_id)
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee '{clean_id}' not found.")

    return {
        "success": True,
        "message": "Employee retrieved successfully",
        "data": emp,
    }


@router.get(
    "/employees",
    summary="List employees with optional department or hub filters",
    description="Retrieves a list of up to 500 employees filtered by department or hub.",
)
async def list_employees_endpoint(
    department: Optional[str] = Query(default=None, description="Filter by department"),
    hub: Optional[str] = Query(default=None, description="Filter by assigned hub"),
    limit: int = Query(default=50, ge=1, le=500, description="Max records to return"),
):
    """List employees filtered by department and/or logistics hub."""
    try:
        employees = employee_service.list_employees(
            department=department,
            hub=hub,
            limit=limit,
        )
    except FileNotFoundError as exc:
        logger.error("Employee data file unavailable: %s", exc)
        raise HTTPException(status_code=500, detail="Employee database is currently unavailable.")
    except Exception as exc:
        logger.exception("Error listing employees: %s", exc)
        raise HTTPException(status_code=500, detail="An internal error occurred while retrieving employees.")

    return {
        "success": True,
        "message": f"Retrieved {len(employees)} employees",
        "data": employees,
    }
