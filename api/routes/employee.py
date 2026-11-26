"""Employee route controller for retrieving personnel records and department assignments."""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse

from database.db import get_employee_by_id
from logistics_chatbot.core import config
import sqlite3

logger = logging.getLogger("logistics_chatbot.api.employee")
router = APIRouter(tags=["employee"])


@router.get(
    "/employee/{id}",
    summary="Retrieve employee details by ID",
    description="Fetches full name, department, job title, assigned hub, shift, certification, email, and extension.",
)
def get_employee_endpoint(
    id: str = Path(..., description="Unique employee identifier, e.g. EMP-20001", examples=["EMP-20001"])
) -> JSONResponse:
    clean_id = (id or "").strip().upper()
    if not clean_id:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": "Employee ID cannot be empty", "data": None},
        )

    try:
        record = get_employee_by_id(clean_id)
        if record is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": f"Employee {clean_id} not found", "data": None},
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "message": "Employee retrieved successfully", "data": record},
        )
    except Exception as exc:
        logger.exception("Error in /employee/%s: %s", clean_id, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "Internal error retrieving employee record", "data": None},
        )


@router.get(
    "/employees",
    summary="List employees with optional department or hub filters",
    description="Retrieves a list of up to 100 employees filtered by department or hub.",
)
def list_employees_endpoint(
    department: str = Query(None, description="Filter by department"),
    hub: str = Query(None, description="Filter by assigned hub"),
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
) -> JSONResponse:
    try:
        db_path = config.PROJECT_ROOT / "data" / "raw" / "shipments.db"
        if not db_path.exists():
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"success": False, "message": "Database not available", "data": []},
            )

        conditions = []
        params = []
        if department:
            conditions.append("LOWER(department) LIKE LOWER(?)")
            params.append(f"%{department}%")
        if hub:
            conditions.append("LOWER(assigned_hub) LIKE LOWER(?)")
            params.append(f"%{hub}%")

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"SELECT * FROM employees{where_clause} ORDER BY employee_id LIMIT ?"
        params.append(limit)

        from contextlib import closing
        with closing(sqlite3.connect(str(db_path))) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(query, tuple(params))
            rows = [dict(r) for r in cur.fetchall()]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "total": len(rows), "data": rows},
        )
    except Exception as exc:
        logger.exception("Error in /employees: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "Error listing employees", "data": []},
        )
