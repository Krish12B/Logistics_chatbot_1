"""Database connection management for PostgreSQL (Supabase) and SQLite."""
from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import psycopg2
import psycopg2.extras

from logistics_chatbot.core import config
from logistics_chatbot.core.errors import DatabaseError

logger = logging.getLogger("logistics_chatbot.database.connection")

_connection = None


def resolve_sqlite_db_path() -> Optional[Path]:
    """Return existing local SQLite shipments/employees database path if present."""
    if getattr(config, "DB_PATH", None) and Path(config.DB_PATH).exists():
        return Path(config.DB_PATH)
    fallback = config.RAW_DATA_DIR / "shipments.db"
    return fallback if fallback.exists() else None


def target_sqlite_db_path() -> Path:
    """Return configured SQLite DB path for reads/writes (defaulting to data/raw/shipments.db)."""
    if getattr(config, "DB_PATH", None):
        return Path(config.DB_PATH)
    return config.RAW_DATA_DIR / "shipments.db"


@contextmanager
def sqlite_connection(db_path: Path | str | None = None):
    """Open a SQLite connection configured with Row factory and guarantee close()."""
    target = Path(db_path) if db_path is not None else target_sqlite_db_path()
    conn = sqlite3.connect(str(target), timeout=config.DB_CONNECT_TIMEOUT)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_postgres_connection():
    """Return a live PostgreSQL connection, creating one if needed."""
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
        raise DatabaseError(detail="SUPABASE_DB_URL is not set in the environment / .env")

    try:
        _connection = psycopg2.connect(
            db_url,
            connect_timeout=config.DB_CONNECT_TIMEOUT,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        _connection.autocommit = True
        logger.info("Connected to Supabase PostgreSQL")
    except psycopg2.OperationalError as exc:
        raise DatabaseError(detail=f"Cannot connect to Supabase PostgreSQL: {exc}") from exc
    except Exception as exc:
        raise DatabaseError(detail=f"Database connection failed: {exc}") from exc

    return _connection


def run_postgres_query(sql: str, params: tuple | dict | None = None, conn_getter=None) -> list[dict]:
    """Execute a SQL query against PostgreSQL and return all rows as dicts."""
    try:
        conn = conn_getter() if conn_getter is not None else get_postgres_connection()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description is None:
                return []
            return [dict(r) for r in cur.fetchall()]
    except DatabaseError:
        raise
    except psycopg2.OperationalError as exc:
        raise DatabaseError(detail=f"PostgreSQL OperationalError during query execution: {exc}") from exc
    except Exception as exc:
        raise DatabaseError(detail=f"Query failed: {exc}") from exc


def close_postgres_connection() -> None:
    """Close active PostgreSQL connection (call at shutdown)."""
    global _connection
    if _connection is not None:
        try:
            _connection.close()
        except Exception:
            pass
        _connection = None
        logger.info("Database connection closed")
