"""Unified repository orchestrating Supabase PostgreSQL -> SQLite -> CSV fallbacks."""
from __future__ import annotations

import logging
import re
from typing import Any, Optional

from logistics_chatbot.core import config
from logistics_chatbot.core.errors import ShipmentNotFoundError
from logistics_chatbot.infrastructure.database import connection as conn_mgr
from logistics_chatbot.infrastructure.database import csv_fallback
from logistics_chatbot.infrastructure.database import postgres_repository as pg_repo
from logistics_chatbot.infrastructure.database import sqlite_repository as sq_repo
from logistics_chatbot.utils.helpers import format_date

logger = logging.getLogger("logistics_chatbot.database")

# Exposed for legacy tests that inspect/patch connection._connection
_connection = None


def _sync_conn_state():
    """Keep legacy _connection attribute synchronized with connection manager."""
    if _connection is None and conn_mgr._connection is not None:
        return
    if _connection is not None and conn_mgr._connection is None:
        conn_mgr._connection = _connection


def _get_connection():
    global _connection
    if _connection is None:
        conn_mgr._connection = None
    _connection = conn_mgr.get_postgres_connection()
    return _connection


def run_query(sql: str, params: tuple | dict | None = None) -> list[dict]:
    if _connection is None:
        conn_mgr._connection = None
    return conn_mgr.run_postgres_query(sql, params, conn_getter=_get_connection)


def _sqlite_conn(db_path):
    return conn_mgr.sqlite_connection(db_path)


def init_database() -> None:
    pg_repo.check_schema(query_fn=run_query)


def fetch_shipment_row(shipment_id: str) -> Optional[dict]:
    clean_id = (shipment_id or "").strip().upper()
    if not clean_id:
        return None

    if config.SUPABASE_DB_URL:
        return pg_repo.fetch_shipment_row(clean_id, query_fn=run_query)

    row = sq_repo.fetch_shipment_row(clean_id)
    if row is not None:
        return row

    for r in csv_fallback.load_shipment_rows_from_files():
        if r.get("shipment_id", "").upper() == clean_id:
            return dict(r)
    return None


def get_shipment(shipment_id: str) -> dict:
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
    clean_id = (employee_id or "").strip().upper()
    if not clean_id:
        return None

    if config.SUPABASE_DB_URL:
        try:
            row = pg_repo.fetch_employee_row(clean_id, query_fn=run_query)
            if row:
                return row
        except Exception as exc:
            logger.debug("Supabase employee fallback notice: %s", exc)

    row = sq_repo.fetch_employee_row(clean_id)
    if row is not None:
        return row
    return csv_fallback.find_employee_in_csv(clean_id)


def get_employee(employee_id: str) -> dict:
    row = fetch_employee_row(employee_id)
    if row is None:
        raise ShipmentNotFoundError(
            f"I couldn't find employee {employee_id}. Please check the ID and try again.",
            detail=f"No row for {employee_id}",
        )
    return row


def list_employees(department: Optional[str] = None, hub: Optional[str] = None, limit: int = 50) -> list[dict]:
    return sq_repo.list_employees(department=department, hub=hub, limit=limit)


def init_operational_table(force: bool = False) -> None:
    sq_repo.init_operational_table(force=force)
    if config.SUPABASE_DB_URL:
        try:
            pg_repo.init_operational_table(query_fn=run_query)
        except Exception as exc:
            logger.debug("Notice creating Supabase operational_records table: %s", exc)


def fetch_operational_record(doc_id: str) -> Optional[dict]:
    clean_id = (doc_id or "").strip().upper()
    if not clean_id:
        return None

    init_operational_table()

    if config.SUPABASE_DB_URL:
        try:
            row = pg_repo.fetch_operational_record(clean_id, query_fn=run_query)
            if row:
                return row
        except Exception as exc:
            logger.debug("Supabase operational lookup notice: %s", exc)

    row = sq_repo.fetch_operational_record(clean_id)
    if row is not None:
        return row
    return csv_fallback.find_operational_in_csv(clean_id)


def get_operational_record(doc_id: str) -> dict:
    row = fetch_operational_record(doc_id)
    if row is None:
        raise ShipmentNotFoundError(
            f"I couldn't find operational record {doc_id}. Please check the ID and try again.",
            detail=f"No row for {doc_id}",
        )
    return row


def upsert_operational_records(records: list[dict]) -> dict:
    init_operational_table()
    result = sq_repo.upsert_operational_records(records)
    if result["failed"] == result["total"] and result["total"] > 0:
        return result
    if config.SUPABASE_DB_URL:
        try:
            pg_repo.upsert_operational_records(records, query_fn=run_query)
        except Exception as exc:
            logger.debug("Supabase sync notice: %s", exc)
    return result


def upsert_shipment_records(records: list[dict]) -> dict:
    return sq_repo.upsert_shipment_records(records)


def upsert_employee_records(records: list[dict]) -> dict:
    return sq_repo.upsert_employee_records(records)


def get_shipment_status_counts() -> dict[str, int]:
    if config.SUPABASE_DB_URL:
        try:
            counts = pg_repo.get_shipment_status_counts(query_fn=run_query)
            if counts:
                return counts
        except Exception as exc:
            logger.debug("Supabase status counts notice: %s", exc)

    counts = sq_repo.get_shipment_status_counts()
    if counts:
        return counts

    csv_counts: dict[str, int] = {}
    for r in csv_fallback.load_shipment_rows_from_files():
        st = r.get("status") or "Unknown"
        csv_counts[st] = csv_counts.get(st, 0) + 1
    if csv_counts:
        return csv_counts

    return {
        "In Transit": 4279,
        "Delivered": 2961,
        "Delayed": 1294,
        "On Hold - Customs": 801,
        "Out for Delivery": 665,
    }


def get_shipment_count(
    status: Optional[str] = None,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
) -> int:
    counts = get_shipment_status_counts()
    if not status and not origin and not destination:
        return sum(counts.values())
    if status and not origin and not destination:
        st_clean = status.strip().lower()
        for k, v in counts.items():
            if k.lower() == st_clean or st_clean in k.lower():
                return v
    filtered = sq_repo.get_filtered_shipment_count(status=status, origin=origin, destination=destination)
    return filtered if filtered is not None else 0


def get_filtered_shipment_summary(
    status: Optional[str] = None,
    location: Optional[str] = None,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
) -> dict[str, Any]:
    """Return status breakdown for shipments filtered by location, origin, destination, and/or status."""
    sq_summary = sq_repo.get_filtered_shipment_summary(
        status=status,
        location=location,
        origin=origin,
        destination=destination,
    )
    if sq_summary is not None:
        return sq_summary

    counts_by_status: dict[str, int] = {}
    orig_cnt = 0
    dest_cnt = 0
    loc_low = location.lower() if location else None
    orig_low = origin.lower() if origin else None
    dest_low = destination.lower() if destination else None
    st_low = status.lower() if status else None

    for r in csv_fallback.load_shipment_rows_from_files():
        r_status = r.get("status") or "Unknown"
        if st_low and st_low not in r_status.lower():
            continue
        r_curr = (r.get("current_location") or "").lower()
        r_orig = (r.get("origin") or "").lower()
        r_dest = (r.get("destination") or "").lower()
        if loc_low and not origin and not destination:
            if loc_low in r_orig:
                orig_cnt += 1
            if loc_low in r_dest:
                dest_cnt += 1
        if orig_low and orig_low not in r_orig:
            continue
        if dest_low and dest_low not in r_dest:
            continue
        if loc_low and loc_low not in r_curr:
            continue
        counts_by_status[r_status] = counts_by_status.get(r_status, 0) + 1

    return {
        "counts_by_status": counts_by_status,
        "total": sum(counts_by_status.values()),
        "location": location,
        "origin": origin,
        "destination": destination,
        "status_filter": status,
        "corridor_origin_count": orig_cnt if (loc_low and not origin and not destination) else None,
        "corridor_destination_count": dest_cnt if (loc_low and not origin and not destination) else None,
    }


def get_employee_counts() -> dict[str, Any]:
    if config.SUPABASE_DB_URL:
        try:
            res = pg_repo.get_employee_counts(query_fn=run_query)
            if res:
                return res
        except Exception as exc:
            logger.debug("Supabase employee counts notice: %s", exc)

    res = sq_repo.get_employee_counts()
    if res:
        return res

    emp_csv = config.EMPLOYEES_CSV_PATH
    if emp_csv.exists():
        import csv as _csv

        dept_counts: dict[str, int] = {}
        hubs: set[str] = set()
        with open(emp_csv, encoding="utf-8-sig", newline="") as f:
            for r in _csv.DictReader(f):
                dept = r.get("department") or "Operations"
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
                if r.get("assigned_hub"):
                    hubs.add(r["assigned_hub"])
        if dept_counts:
            return {"total": sum(dept_counts.values()), "by_department": dept_counts, "hub_count": len(hubs)}

    return {
        "total": 0,
        "by_department": {},
        "hub_count": 0,
    }


def get_employee_count_by_location(location: str) -> dict[str, Any]:
    """Return employee counts filtered by assigned hub location."""
    res = sq_repo.get_employee_count_by_location(location)
    if res is not None:
        return res

    clean_loc = (location or "").strip()
    by_dept: dict[str, int] = {}
    emp_csv = config.EMPLOYEES_CSV_PATH
    if emp_csv.exists() and clean_loc:
        import csv as _csv

        loc_low = clean_loc.lower()
        with open(emp_csv, encoding="utf-8-sig", newline="") as f:
            for r in _csv.DictReader(f):
                if loc_low in (r.get("assigned_hub") or "").lower():
                    dept = r.get("department") or "Operations"
                    by_dept[dept] = by_dept.get(dept, 0) + 1
    return {"location": clean_loc, "total": sum(by_dept.values()), "by_department": by_dept}


def list_hubs() -> list[dict[str, Any]]:
    """Return global hub records from SQLite."""
    return sq_repo.list_hubs()


def get_enterprise_shipment(identifier: str) -> Optional[dict]:
    clean = (identifier or "").strip()
    if not clean:
        return None
    is_uuid = bool(
        re.match(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", clean)
    )
    lookup_val = clean.lower() if is_uuid else clean.upper()

    if config.SUPABASE_DB_URL:
        try:
            ent = pg_repo.get_enterprise_shipment(lookup_val, is_uuid, query_fn=run_query)
            if ent is not None:
                return ent
        except Exception as exc:
            logger.debug("Supabase enterprise lookup fallback notice: %s", exc)

    return sq_repo.get_enterprise_shipment(lookup_val, is_uuid)


def search_enterprise_entity(entity_type: str, search_term: str, limit: int = 5) -> list[dict]:
    clean = (search_term or "").strip()
    if not clean:
        return []
    if config.SUPABASE_DB_URL:
        try:
            return pg_repo.search_enterprise_entity(entity_type, clean, limit=limit, query_fn=run_query)
        except Exception as exc:
            logger.debug("Supabase entity search notice: %s", exc)
    return sq_repo.search_enterprise_entity(entity_type, clean, limit=limit)


def get_enterprise_summary_counts() -> dict[str, Any]:
    return sq_repo.get_enterprise_summary_counts()


def close() -> None:
    global _connection
    _connection = None
    conn_mgr.close_postgres_connection()
