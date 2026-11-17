"""Everything that talks to the SQLite shipment database."""
import json
import sqlite3
from contextlib import closing

import config
from errors import DatabaseError, ShipmentNotFoundError

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id        TEXT PRIMARY KEY,
    origin             TEXT NOT NULL,
    destination        TEXT NOT NULL,
    status             TEXT NOT NULL,
    current_location   TEXT,
    route              TEXT,
    estimated_delivery TEXT,
    delay_reason       TEXT,
    customs_status     TEXT,
    last_updated       TEXT
)
"""

INSERT_SQL = """
INSERT INTO shipments (shipment_id, origin, destination, status, current_location,
                       route, estimated_delivery, delay_reason, customs_status, last_updated)
VALUES (:shipment_id, :origin, :destination, :status, :current_location,
        :route, :estimated_delivery, :delay_reason, :customs_status, :last_updated)
"""


def get_connection():
    """Open a database connection. Any failure becomes a DatabaseError."""
    try:
        connection = sqlite3.connect(config.DB_PATH)
    except sqlite3.Error as exc:
        raise DatabaseError(detail=f"Cannot open database {config.DB_PATH}: {exc}") from exc
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    """Create the shipments table and load the seed data the first time."""
    try:
        with closing(get_connection()) as conn:
            conn.execute(TABLE_SQL)
            (count,) = conn.execute("SELECT COUNT(*) FROM shipments").fetchone()
            if count == 0:
                with open(config.SHIPMENT_SEED_PATH, encoding="utf-8") as f:
                    conn.executemany(INSERT_SQL, json.load(f))
            conn.commit()
    except (sqlite3.Error, OSError, ValueError) as exc:
        raise DatabaseError(detail=f"Database setup failed: {exc}") from exc


def get_shipment(shipment_id):
    """Return one shipment as a dict, or raise ShipmentNotFoundError."""
    try:
        with closing(get_connection()) as conn:
            row = conn.execute(
                "SELECT * FROM shipments WHERE shipment_id = ?", (shipment_id,)
            ).fetchone()
    except sqlite3.Error as exc:
        raise DatabaseError(detail=f"Query failed: {exc}") from exc

    if row is None:
        raise ShipmentNotFoundError(
            f"I couldn't find shipment {shipment_id}. Please check the ID and try again.",
            detail=f"No row for {shipment_id}",
        )
    return dict(row)
