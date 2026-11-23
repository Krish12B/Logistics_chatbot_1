"""Database layer: direct PostgreSQL connection to Supabase with local fallback.

Uses psycopg2 for a persistent connection with connection checking,
connection pooling, and schema verification.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import psycopg2
import psycopg2.extras

from logistics_chatbot.core import config
from logistics_chatbot.core.errors import DatabaseError, ShipmentNotFoundError
from logistics_chatbot.utils.helpers import format_date

logger = logging.getLogger("logistics_chatbot.database")

_connection = None

_SCHEMA_CHECK_SQL = """
SELECT
    EXISTS(
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'shipments'
    ) AS shipments_table,
    EXISTS(
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'knowledge_base'
    ) AS knowledge_table,
    EXISTS(
        SELECT 1 FROM information_schema.routines
        WHERE routine_schema = 'public' AND routine_name = 'match_knowledge'
    ) AS match_function;
"""


def _get_connection():
    """Return a live database connection, creating one if needed."""
    global _connection

    if _connection is not None:
        try:
            _connection.cursor().execute("SELECT 1")
            return _connection
        except Exception:
            try:
                _connection.close()
            except Exception:
                pass
            _connection = None

    db_url = config.SUPABASE_DB_URL
    if not db_url:
        raise DatabaseError(
            detail="SUPABASE_DB_URL is not set in the environment / .env"
        )

    try:
        _connection = psycopg2.connect(
            db_url,
            connect_timeout=config.DB_CONNECT_TIMEOUT,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        _connection.autocommit = True
        logger.info("Connected to Supabase PostgreSQL")
    except psycopg2.OperationalError as exc:
        raise DatabaseError(
            detail=f"Cannot connect to Supabase PostgreSQL: {exc}"
        ) from exc
    except Exception as exc:
        raise DatabaseError(
            detail=f"Database connection failed: {exc}"
        ) from exc

    return _connection


def run_query(sql: str, params: tuple | dict | None = None) -> list[dict]:
    """Execute a SQL query and return all rows as a list of dicts."""
    try:
        conn = _get_connection()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description is None:
                return []
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    except DatabaseError:
        raise
    except psycopg2.OperationalError as exc:
        raise DatabaseError(
            detail=f"PostgreSQL OperationalError during query execution: {exc}"
        ) from exc
    except Exception as exc:
        raise DatabaseError(
            detail=f"Query failed: {exc}"
        ) from exc


def init_database():
    """Verify that the database is reachable and has the required schema."""
    rows = run_query(_SCHEMA_CHECK_SQL)
    if not rows:
        raise DatabaseError(detail="Schema check query returned no rows")

    status = rows[0]
    missing = []
    if not status.get("shipments_table"):
        missing.append("shipments table")
    if not status.get("knowledge_table"):
        missing.append("knowledge_base table")
    if not status.get("match_function"):
        missing.append("match_knowledge function")

    if missing:
        raise DatabaseError(
            detail=(
                f"Missing database objects: {', '.join(missing)}. "
                "Run the SQL in docs/architecture/schema.sql to create them."
            )
        )

    logger.info("Database schema verified: all required objects present")


def fetch_shipment_row(shipment_id: str) -> Optional[dict]:
    """Fetch a raw shipment row from the database, falling back to local SQLite/CSV."""
    clean_id = (shipment_id or "").strip().upper()
    if not clean_id:
        return None

    if not config.SUPABASE_DB_URL:
        # 1. Fast indexed SQLite lookup (<0.5ms)
        try:
            import sqlite3
            db_path = config.PROJECT_ROOT / "data" / "raw" / "shipments.db"
            if db_path.exists():
                with sqlite3.connect(str(db_path)) as conn:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM shipments WHERE UPPER(shipment_id) = ?", (clean_id,))
                    row = cur.fetchone()
                    if row:
                        return dict(row)
        except Exception as exc:
            logger.debug("SQLite lookup fallback notice: %s", exc)

        # 2. Local CSV fallback
        from logistics_chatbot.rag import ingestion
        for row in ingestion.load_shipment_rows():
            if row.get("shipment_id", "").upper() == clean_id:
                return dict(row)
        return None

    rows = run_query(
        "SELECT * FROM shipments WHERE shipment_id = %s",
        (clean_id,),
    )
    return rows[0] if rows else None


def get_shipment(shipment_id: str) -> dict:
    """Fetch one shipment and return it with formatted dates."""
    row = fetch_shipment_row(shipment_id)
    if row is None:
        raise ShipmentNotFoundError(
            f"I couldn't find shipment {shipment_id}. Please check the ID and try again.",
            detail=f"No row for {shipment_id}",
        )

    row["estimated_delivery"] = format_date(row.get("estimated_delivery"))
    row["last_updated"] = format_date(row.get("last_updated"))
    return row


def fetch_employee_row(employee_id: str) -> Optional[dict]:
    """Fetch an employee row by ID from Supabase, SQLite, or CSV."""
    clean_id = (employee_id or "").strip().upper()
    if not clean_id:
        return None

    if config.SUPABASE_DB_URL:
        try:
            rows = run_query(
                "SELECT * FROM employees WHERE employee_id = %s",
                (clean_id,),
            )
            if rows:
                return rows[0]
        except Exception:
            pass

    # 1. Indexed SQLite lookup
    try:
        import sqlite3
        db_path = config.PROJECT_ROOT / "data" / "raw" / "shipments.db"
        if db_path.exists():
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM employees WHERE UPPER(employee_id) = ?", (clean_id,))
                row = cur.fetchone()
                if row:
                    return dict(row)
    except Exception:
        pass

    # 2. CSV fallback
    emp_csv = config.PROJECT_ROOT / "data" / "generated" / "employees_roster.csv"
    if emp_csv.exists():
        import csv
        with open(emp_csv, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if r.get("employee_id", "").upper() == clean_id:
                    return dict(r)
    return None


def get_employee(employee_id: str) -> dict:
    """Fetch one employee and return their details."""
    row = fetch_employee_row(employee_id)
    if row is None:
        raise ShipmentNotFoundError(
            f"I couldn't find employee {employee_id}. Please check the ID and try again.",
            detail=f"No row for {employee_id}",
        )
    return row


def close():
    """Close the database connection (call at shutdown)."""
    global _connection
    if _connection is not None:
        try:
            _connection.close()
        except Exception:
            pass
        _connection = None
        logger.info("Database connection closed")
