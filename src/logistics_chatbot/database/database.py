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
    """Fetch a raw shipment row from the database, falling back to local CSV."""
    if not config.SUPABASE_DB_URL:
        from logistics_chatbot.rag import ingestion
        for row in ingestion.load_shipment_rows():
            if row.get("shipment_id", "").upper() == shipment_id.upper():
                return dict(row)
        return None

    rows = run_query(
        "SELECT * FROM shipments WHERE shipment_id = %s",
        (shipment_id,),
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
