"""SQLite repository implementation for legacy 10K, employee, operational, and 14-table enterprise records."""
from __future__ import annotations

import logging
import re
from datetime import datetime as _dt
from pathlib import Path
from typing import Any, Optional

from logistics_chatbot.core import config
from logistics_chatbot.infrastructure.database.connection import (
    resolve_sqlite_db_path,
    sqlite_connection,
    target_sqlite_db_path,
)
from logistics_chatbot.utils.helpers import format_date

logger = logging.getLogger("logistics_chatbot.database.sqlite")

_ops_table_ready_paths: set[str] = set()

ENTERPRISE_SHIPMENT_SQL_SELECT = """
    SELECT
        s.shipment_id, s.booking_id, s.customer_id, s.product_id, s.carrier_id,
        s.warehouse_id, s.route_id, s.vehicle_id, s.customs_id, s.weather_id,
        s.booking_date, s.ship_date, s.expected_delivery_date, s.shipping_mode,
        s.shipment_type, s.priority, s.weight_kg, s.volume_cbm, s.declared_value,
        s.insurance, s.fragile,
        c.customer_name, c.customer_type, c.industry AS customer_industry,
        c.city AS customer_city, c.state AS customer_state, c.country AS customer_country,
        c.customer_status,
        p.product_name, p.category AS product_category, p.hs_code,
        p.hazardous AS product_hazardous, p.perishable AS product_perishable,
        p.temperature_controlled, p.supplier_name,
        cr.carrier_name, cr.carrier_type, cr.average_rating AS carrier_rating,
        cr.fleet_size, cr.years_of_service, cr.headquarters AS carrier_hq,
        w.warehouse_name, w.city AS warehouse_city, w.state AS warehouse_state,
        w.warehouse_capacity, w.current_utilization, w.warehouse_type,
        r.origin_city, r.destination_city, r.origin_country, r.destination_country,
        r.origin_port, r.destination_port, r.distance_km, r.average_transit_days,
        r.route_risk, r.traffic_index,
        v.vehicle_number, v.vehicle_type, v.capacity_kg AS vehicle_capacity_kg,
        v.fuel_type, v.maintenance_status, v.vehicle_age,
        wt.city AS weather_city, wt.forecast_date, wt.weather_condition,
        wt.temperature, wt.rainfall, wt.humidity, wt.wind_speed, wt.visibility,
        cu.customs_required, cu.documentation_complete, cu.inspection_required,
        cu.cargo_type, cu.destination_country AS customs_destination_country,
        h.history_id, h.actual_delivery_date, h.delivery_status AS derived_status,
        h.delivery_attempts
    FROM enterprise_shipments s
    JOIN enterprise_customers c ON c.customer_id = s.customer_id
    JOIN products p ON p.product_id = s.product_id
    JOIN carriers cr ON cr.carrier_id = s.carrier_id
    JOIN warehouses w ON w.warehouse_id = s.warehouse_id
    JOIN routes r ON r.route_id = s.route_id
    JOIN vehicles v ON v.vehicle_id = s.vehicle_id
    JOIN weather wt ON wt.weather_id = s.weather_id
    JOIN customs cu ON cu.customs_id = s.customs_id
    LEFT JOIN shipment_delivery_history h ON h.shipment_id = s.shipment_id
"""


def enrich_enterprise_shipment_dict(
    row: dict,
    alerts: list[dict],
    latest_feat: Optional[dict],
    latest_inf: Optional[dict],
) -> dict:
    """Normalize booleans and compute derived delay metrics from shipment_delivery_history."""
    rec = dict(row)
    for bcol in (
        "insurance",
        "fragile",
        "product_hazardous",
        "product_perishable",
        "temperature_controlled",
        "customs_required",
        "documentation_complete",
        "inspection_required",
    ):
        if bcol in rec and rec[bcol] is not None:
            rec[bcol] = bool(rec[bcol])

    derived_status = rec.get("derived_status") or "Pending"
    rec["is_delayed"] = derived_status.lower() == "delayed"
    rec["status"] = derived_status

    delay_days = 0
    try:
        exp_str = str(rec.get("expected_delivery_date") or "")[:10]
        act_str = str(rec.get("actual_delivery_date") or "")[:10]
        if exp_str and act_str:
            delay_days = max(
                0,
                (_dt.strptime(act_str, "%Y-%m-%d").date() - _dt.strptime(exp_str, "%Y-%m-%d").date()).days,
            )
    except Exception:
        delay_days = 0
    rec["delay_days"] = delay_days

    for dcol in ("booking_date", "ship_date", "expected_delivery_date", "actual_delivery_date", "forecast_date"):
        if rec.get(dcol) is not None:
            rec[dcol] = format_date(rec[dcol])

    rec["origin"] = f"{rec.get('origin_city', '')}, {rec.get('origin_country', '')}".strip(", ")
    rec["destination"] = f"{rec.get('destination_city', '')}, {rec.get('destination_country', '')}".strip(", ")
    rec["route"] = f"{rec.get('origin_port', '')} -> {rec.get('destination_port', '')}".strip(" ->")
    rec["estimated_delivery"] = rec.get("expected_delivery_date")

    rec["ai_features"] = dict(latest_feat) if latest_feat else {}
    rec["ai_inference"] = dict(latest_inf) if latest_inf else {}
    rec["alerts"] = [dict(a) for a in alerts]
    return rec


def fetch_shipment_row(shipment_id: str) -> Optional[dict]:
    """Indexed SQLite lookup for a legacy SHP-* shipment."""
    db_path = resolve_sqlite_db_path()
    if db_path is None:
        return None
    try:
        with sqlite_connection(db_path) as conn:
            row = conn.execute(
                "SELECT * FROM shipments WHERE shipment_id = ?",
                (shipment_id,),
            ).fetchone()
            return dict(row) if row else None
    except Exception as exc:
        logger.debug("SQLite shipment lookup notice: %s", exc)
        return None


def search_shipments(
    status: Optional[str] = None,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    limit: int = 10,
) -> Optional[list[dict]]:
    """Filter shipments in SQLite."""
    db_path = resolve_sqlite_db_path()
    if db_path is None:
        return None

    sq_conds: list[str] = []
    sq_params: list[Any] = []
    if status:
        sq_conds.append("status = ? COLLATE NOCASE")
        sq_params.append(status)
    if origin:
        sq_conds.append("LOWER(origin) LIKE LOWER(?)")
        sq_params.append(f"%{origin}%")
    if destination:
        sq_conds.append("LOWER(destination) LIKE LOWER(?)")
        sq_params.append(f"%{destination}%")
    sq_where = " AND ".join(sq_conds) if sq_conds else "1=1"
    sq_params.append(limit)
    sq_sql = f"SELECT * FROM shipments WHERE {sq_where} ORDER BY last_updated DESC LIMIT ?"

    try:
        with sqlite_connection(db_path) as conn:
            rows = [dict(r) for r in conn.execute(sq_sql, tuple(sq_params)).fetchall()]
        for r in rows:
            r["estimated_delivery"] = format_date(r.get("estimated_delivery"))
            r["last_updated"] = format_date(r.get("last_updated"))
        return rows
    except Exception as exc:
        logger.debug("SQLite search_shipments notice: %s", exc)
        return None


def get_shipment_status_counts() -> Optional[dict[str, int]]:
    db_path = resolve_sqlite_db_path()
    if db_path is None:
        return None
    try:
        with sqlite_connection(db_path) as conn:
            rows = conn.execute("SELECT status, COUNT(*) FROM shipments GROUP BY status").fetchall()
            if rows:
                return {row[0]: int(row[1]) for row in rows}
    except Exception as exc:
        logger.debug("SQLite status counts notice: %s", exc)
    return None


def get_filtered_shipment_count(
    status: Optional[str] = None,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
) -> Optional[int]:
    db_path = resolve_sqlite_db_path()
    if db_path is None:
        return None
    try:
        with sqlite_connection(db_path) as conn:
            clauses, params = [], []
            if status:
                clauses.append("LOWER(status) LIKE LOWER(?)")
                params.append(f"%{status}%")
            if origin:
                clauses.append("LOWER(origin) LIKE LOWER(?)")
                params.append(f"%{origin}%")
            if destination:
                clauses.append("LOWER(destination) LIKE LOWER(?)")
                params.append(f"%{destination}%")
            where = " AND ".join(clauses) if clauses else "1=1"
            res = conn.execute(f"SELECT COUNT(*) FROM shipments WHERE {where}", params).fetchone()
            return int(res[0]) if res else 0
    except Exception as exc:
        logger.debug("SQLite filtered count notice: %s", exc)
        return None


def fetch_employee_row(employee_id: str) -> Optional[dict]:
    db_path = resolve_sqlite_db_path()
    if db_path is None:
        return None
    try:
        with sqlite_connection(db_path) as conn:
            row = conn.execute(
                "SELECT * FROM employees WHERE employee_id = ?",
                (employee_id,),
            ).fetchone()
            return dict(row) if row else None
    except Exception:
        return None


def list_employees(
    department: Optional[str] = None,
    hub: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    db_path = resolve_sqlite_db_path()
    if db_path is None:
        raise FileNotFoundError("SQLite database not available")
    conditions: list[str] = []
    params: list[Any] = []
    if department:
        conditions.append("LOWER(department) LIKE LOWER(?)")
        params.append(f"%{department}%")
    if hub:
        conditions.append("LOWER(assigned_hub) LIKE LOWER(?)")
        params.append(f"%{hub}%")
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    query = f"SELECT * FROM employees{where_clause} ORDER BY employee_id LIMIT ?"
    params.append(limit)
    with sqlite_connection(db_path) as conn:
        return [dict(r) for r in conn.execute(query, tuple(params)).fetchall()]


def get_employee_counts() -> Optional[dict[str, Any]]:
    db_path = resolve_sqlite_db_path()
    if db_path is None:
        return None
    try:
        with sqlite_connection(db_path) as conn:
            rows = conn.execute("SELECT department, COUNT(*) FROM employees GROUP BY department").fetchall()
            if rows:
                dept_counts = {r[0]: int(r[1]) for r in rows}
                hub_row = conn.execute("SELECT COUNT(DISTINCT assigned_hub) FROM employees").fetchone()
                hub_count = int(hub_row[0]) if hub_row else 0
                return {"total": sum(dept_counts.values()), "by_department": dept_counts, "hub_count": hub_count}
    except Exception as exc:
        logger.debug("SQLite employee counts notice: %s", exc)
    return None


def get_employee_count_by_location(location: str) -> Optional[dict[str, Any]]:
    """Return SQLite employee counts filtered by assigned_hub substring."""
    db_path = resolve_sqlite_db_path()
    if db_path is None:
        return None
    clean_loc = (location or "").strip()
    if not clean_loc:
        return None
    try:
        with sqlite_connection(db_path) as conn:
            pattern = f"%{clean_loc}%"
            rows = conn.execute(
                "SELECT department, COUNT(*) FROM employees WHERE LOWER(assigned_hub) LIKE LOWER(?) GROUP BY department ORDER BY COUNT(*) DESC",
                (pattern,),
            ).fetchall()
            if not rows and clean_loc.lower().endswith(" hub"):
                clean_loc = clean_loc[:-4].strip()
                pattern = f"%{clean_loc}%"
                rows = conn.execute(
                    "SELECT department, COUNT(*) FROM employees WHERE LOWER(assigned_hub) LIKE LOWER(?) GROUP BY department ORDER BY COUNT(*) DESC",
                    (pattern,),
                ).fetchall()
            by_dept = {r[0]: int(r[1]) for r in rows}
            return {"location": clean_loc, "total": sum(by_dept.values()), "by_department": by_dept}
    except Exception as exc:
        logger.debug("SQLite employee location count notice: %s", exc)
        return None


def get_filtered_shipment_summary(
    status: Optional[str] = None,
    location: Optional[str] = None,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Return SQLite shipment status breakdown filtered by status, location, origin, and/or destination."""
    db_path = resolve_sqlite_db_path()
    if db_path is None:
        return None
    try:
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            clauses.append("LOWER(status) LIKE LOWER(?)")
            params.append(f"%{status}%")
        if origin:
            clauses.append("LOWER(origin) LIKE LOWER(?)")
            params.append(f"%{origin}%")
        if destination:
            clauses.append("LOWER(destination) LIKE LOWER(?)")
            params.append(f"%{destination}%")
        if location:
            clauses.append("LOWER(current_location) LIKE LOWER(?)")
            params.append(f"%{location}%")

        where_sql = " AND ".join(clauses) if clauses else "1=1"
        with sqlite_connection(db_path) as conn:
            rows = conn.execute(
                f"SELECT status, COUNT(*) FROM shipments WHERE {where_sql} GROUP BY status ORDER BY COUNT(*) DESC",
                tuple(params),
            ).fetchall()
            counts_by_status = {row[0]: int(row[1]) for row in rows}
            total = sum(counts_by_status.values())

            corridor_origin_count = None
            corridor_destination_count = None
            if location and not origin and not destination:
                extra_clauses = [f"LOWER(origin) LIKE LOWER(?)"]
                extra_params: list[Any] = [f"%{location}%"]
                if status:
                    extra_clauses.append("LOWER(status) LIKE LOWER(?)")
                    extra_params.append(f"%{status}%")
                corridor_origin_count = int(
                    conn.execute(
                        f"SELECT COUNT(*) FROM shipments WHERE {' AND '.join(extra_clauses)}",
                        tuple(extra_params),
                    ).fetchone()[0]
                )

                dest_clauses = [f"LOWER(destination) LIKE LOWER(?)"]
                dest_params: list[Any] = [f"%{location}%"]
                if status:
                    dest_clauses.append("LOWER(status) LIKE LOWER(?)")
                    dest_params.append(f"%{status}%")
                corridor_destination_count = int(
                    conn.execute(
                        f"SELECT COUNT(*) FROM shipments WHERE {' AND '.join(dest_clauses)}",
                        tuple(dest_params),
                    ).fetchone()[0]
                )

        return {
            "counts_by_status": counts_by_status,
            "total": total,
            "location": location,
            "origin": origin,
            "destination": destination,
            "status_filter": status,
            "corridor_origin_count": corridor_origin_count,
            "corridor_destination_count": corridor_destination_count,
        }
    except Exception as exc:
        logger.debug("SQLite filtered shipment summary notice: %s", exc)
        return None


def list_hubs() -> list[dict[str, Any]]:
    """Return global logistics hubs from SQLite hubs table."""
    db_path = resolve_sqlite_db_path()
    if db_path is None:
        return []
    try:
        with sqlite_connection(db_path) as conn:
            exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='hubs'"
            ).fetchone()
            if not exists:
                return []
            rows = conn.execute(
                "SELECT hub_code, facility_name, city_country, primary_transport_mode FROM hubs ORDER BY hub_code"
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception as exc:
        logger.debug("SQLite list_hubs notice: %s", exc)
        return []


def init_operational_table(force: bool = False) -> None:
    """Create operational_records table in SQLite if missing (memoized per DB path)."""
    db_path = target_sqlite_db_path()
    path_key = str(db_path.resolve())
    if not force and path_key in _ops_table_ready_paths:
        return
    try:
        if db_path.exists():
            with sqlite_connection(db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS operational_records (
                        doc_id TEXT PRIMARY KEY,
                        category TEXT NOT NULL,
                        section_title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        tags TEXT,
                        status TEXT,
                        origin TEXT,
                        destination TEXT,
                        assigned_employee TEXT,
                        responsible_department TEXT,
                        risk_factors TEXT,
                        last_updated TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_ops_doc_id ON operational_records(doc_id);")
                conn.commit()
                _ops_table_ready_paths.add(path_key)
    except Exception as exc:
        logger.warning("Notice creating SQLite operational_records table: %s", exc)


def fetch_operational_record(doc_id: str) -> Optional[dict]:
    init_operational_table()
    db_path = resolve_sqlite_db_path()
    if db_path is None:
        return None
    try:
        with sqlite_connection(db_path) as conn:
            row = conn.execute(
                "SELECT * FROM operational_records WHERE doc_id = ?",
                (doc_id,),
            ).fetchone()
            return dict(row) if row else None
    except Exception as exc:
        logger.debug("SQLite operational lookup notice: %s", exc)
        return None


def upsert_operational_records(records: list[dict]) -> dict:
    init_operational_table()
    total = len(records)
    imported = 0
    skipped = 0
    failed = 0
    errors: list[str] = []
    db_path = target_sqlite_db_path()

    try:
        with sqlite_connection(db_path) as conn:
            cur = conn.cursor()
            for r in records:
                doc_id = (r.get("doc_id") or "").strip().upper()
                if not doc_id:
                    skipped += 1
                    continue
                try:
                    cur.execute(
                        """
                        INSERT INTO operational_records (
                            doc_id, category, section_title, content, tags,
                            status, origin, destination, assigned_employee,
                            responsible_department, risk_factors, last_updated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(doc_id) DO UPDATE SET
                            category = excluded.category,
                            section_title = excluded.section_title,
                            content = excluded.content,
                            tags = excluded.tags,
                            status = excluded.status,
                            origin = excluded.origin,
                            destination = excluded.destination,
                            assigned_employee = excluded.assigned_employee,
                            responsible_department = excluded.responsible_department,
                            risk_factors = excluded.risk_factors,
                            last_updated = excluded.last_updated;
                        """,
                        (
                            doc_id,
                            r.get("category", "operational_case"),
                            r.get("section_title", f"Operational Case {doc_id}"),
                            r.get("content", ""),
                            r.get("tags", ""),
                            r.get("status", "Active"),
                            r.get("origin", "N/A"),
                            r.get("destination", "N/A"),
                            r.get("assigned_employee", "Operations Coordinator"),
                            r.get("responsible_department", r.get("category", "Operations")),
                            r.get("risk_factors", "Standard monitoring"),
                            r.get("last_updated", ""),
                        ),
                    )
                    imported += 1
                except Exception as exc:
                    failed += 1
                    errors.append(f"{doc_id}: {exc}")
            conn.commit()
    except Exception as exc:
        logger.error("Failed batch SQLite upsert: %s", exc)
        return {"total": total, "imported": 0, "skipped": skipped, "failed": total, "errors": [str(exc)]}

    return {"total": total, "imported": imported, "skipped": skipped, "failed": failed, "errors": errors}


def upsert_shipment_records(records: list[dict]) -> dict:
    total = len(records)
    imported = 0
    skipped = 0
    failed = 0
    errors: list[str] = []
    db_path = target_sqlite_db_path()

    try:
        with sqlite_connection(db_path) as conn:
            cur = conn.cursor()
            for r in records:
                sid = (r.get("shipment_id") or "").strip().upper()
                if not sid:
                    skipped += 1
                    continue
                try:
                    cur.execute(
                        """
                        INSERT INTO shipments (
                            shipment_id, origin, destination, status,
                            current_location, route, estimated_delivery,
                            delay_reason, customs_status, last_updated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(shipment_id) DO UPDATE SET
                            origin = excluded.origin,
                            destination = excluded.destination,
                            status = excluded.status,
                            current_location = excluded.current_location,
                            route = excluded.route,
                            estimated_delivery = excluded.estimated_delivery,
                            delay_reason = excluded.delay_reason,
                            customs_status = excluded.customs_status,
                            last_updated = excluded.last_updated;
                        """,
                        (
                            sid,
                            r.get("origin") or r.get("origin_hub", "N/A"),
                            r.get("destination") or r.get("destination_hub", "N/A"),
                            r.get("status", "In Transit"),
                            r.get("current_location", "In Transit"),
                            r.get("route", f"{r.get('origin', '')} -> {r.get('destination', '')}"),
                            r.get("estimated_delivery") or r.get("expected_delivery", ""),
                            r.get("delay_reason", ""),
                            r.get("customs_status", "Cleared"),
                            r.get("last_updated", ""),
                        ),
                    )
                    imported += 1
                except Exception as exc:
                    failed += 1
                    errors.append(f"{sid}: {exc}")
            conn.commit()
    except Exception as exc:
        logger.error("Failed batch shipment SQLite upsert: %s", exc)
        return {"total": total, "imported": 0, "skipped": skipped, "failed": total, "errors": [str(exc)]}

    return {"total": total, "imported": imported, "skipped": skipped, "failed": failed, "errors": errors}


def upsert_employee_records(records: list[dict]) -> dict:
    total = len(records)
    imported = 0
    skipped = 0
    failed = 0
    errors: list[str] = []
    db_path = target_sqlite_db_path()

    try:
        with sqlite_connection(db_path) as conn:
            cur = conn.cursor()
            for r in records:
                eid = (r.get("employee_id") or "").strip().upper()
                if not eid:
                    skipped += 1
                    continue
                try:
                    name = r.get("full_name") or f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
                    cur.execute(
                        """
                        INSERT INTO employees (
                            employee_id, full_name, department, job_title,
                            assigned_hub, shift, certification, email,
                            phone_extension, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(employee_id) DO UPDATE SET
                            full_name = excluded.full_name,
                            department = excluded.department,
                            job_title = excluded.job_title,
                            assigned_hub = excluded.assigned_hub,
                            shift = excluded.shift,
                            certification = excluded.certification,
                            email = excluded.email,
                            phone_extension = excluded.phone_extension,
                            status = excluded.status;
                        """,
                        (
                            eid,
                            name or "Employee",
                            r.get("department", "Operations"),
                            r.get("job_title") or r.get("role", "Specialist"),
                            r.get("assigned_hub") or r.get("hub", "DXB-HUB-01"),
                            r.get("shift", "Day Shift (08:00 - 17:00)"),
                            r.get("certification", "Standard Operations Certified"),
                            r.get("email", f"{eid.lower()}@fleetharbor.com"),
                            r.get("phone_extension", "x4000"),
                            r.get("status", "Active"),
                        ),
                    )
                    imported += 1
                except Exception as exc:
                    failed += 1
                    errors.append(f"{eid}: {exc}")
            conn.commit()
    except Exception as exc:
        logger.error("Failed batch employee SQLite upsert: %s", exc)
        return {"total": total, "imported": 0, "skipped": skipped, "failed": total, "errors": [str(exc)]}

    return {"total": total, "imported": imported, "skipped": skipped, "failed": failed, "errors": errors}


def get_enterprise_shipment(lookup_val: str, is_uuid: bool) -> Optional[dict]:
    db_path = resolve_sqlite_db_path()
    if db_path is None:
        return None
    try:
        with sqlite_connection(db_path) as conn:
            tbl_exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='enterprise_shipments'"
            ).fetchone()
            if not tbl_exists:
                return None
            where = "LOWER(s.shipment_id) = ?" if is_uuid else "UPPER(s.booking_id) = ?"
            row = conn.execute(f"{ENTERPRISE_SHIPMENT_SQL_SELECT} WHERE {where}", (lookup_val,)).fetchone()
            if not row:
                return None
            row_dict = dict(row)
            sid = row_dict["shipment_id"]
            feat_row = conn.execute(
                "SELECT route_delay_rate, carrier_reliability_score, weather_severity_score, feature_timestamp "
                "FROM ai_feature_store WHERE shipment_id = ? ORDER BY feature_timestamp DESC LIMIT 1",
                (sid,),
            ).fetchone()
            inf_row = conn.execute(
                "SELECT ai.delay_probability, ai.risk_category, ai.latency_ms, ai.prediction_timestamp, "
                "mr.model_name, mr.model_version, mr.deployment_status "
                "FROM ai_inference_log ai JOIN ai_model_registry mr ON mr.model_id = ai.model_id "
                "WHERE ai.shipment_id = ? ORDER BY ai.prediction_timestamp DESC LIMIT 1",
                (sid,),
            ).fetchone()
            alert_rows = conn.execute(
                "SELECT alert_type, severity, recommended_action, alert_status "
                "FROM ai_monitoring_alerts WHERE shipment_id = ? LIMIT 5",
                (sid,),
            ).fetchall()
            return enrich_enterprise_shipment_dict(
                row_dict,
                [dict(a) for a in alert_rows],
                dict(feat_row) if feat_row else None,
                dict(inf_row) if inf_row else None,
            )
    except Exception as exc:
        logger.warning("SQLite enterprise shipment lookup failed: %s", exc)
    return None


def search_enterprise_entity(entity_type: str, clean: str, limit: int = 5) -> list[dict]:
    db_path = resolve_sqlite_db_path()
    if db_path is None:
        return []

    etype = entity_type.lower().strip()
    if etype == "route" and "->" in clean:
        orig_q, dest_q = [p.strip() for p in clean.split("->", 1)]
        orig_p, dest_p = f"%{orig_q}%", f"%{dest_q}%"
        rt_sql = (
            "SELECT * FROM routes WHERE LOWER(origin_city) LIKE LOWER(?) "
            "AND LOWER(destination_city) LIKE LOWER(?) LIMIT ?"
        )
        try:
            with sqlite_connection(db_path) as conn:
                return [dict(r) for r in conn.execute(rt_sql, (orig_p, dest_p, limit)).fetchall()]
        except Exception as exc:
            logger.debug("SQLite paired route search notice: %s", exc)
            return []

    like_param = f"%{clean}%"
    sql_map = {
        "customer": (
            "SELECT * FROM enterprise_customers WHERE LOWER(customer_name) LIKE LOWER(?) "
            "OR LOWER(customer_id) = LOWER(?) LIMIT ?",
            (like_param, clean, limit),
        ),
        "carrier": (
            "SELECT * FROM carriers WHERE LOWER(carrier_name) LIKE LOWER(?) "
            "OR LOWER(carrier_id) = LOWER(?) LIMIT ?",
            (like_param, clean, limit),
        ),
        "warehouse": (
            "SELECT * FROM warehouses WHERE LOWER(warehouse_name) LIKE LOWER(?) "
            "OR LOWER(city) LIKE LOWER(?) OR LOWER(warehouse_id) = LOWER(?) LIMIT ?",
            (like_param, like_param, clean, limit),
        ),
        "route": (
            "SELECT * FROM routes WHERE LOWER(origin_city) LIKE LOWER(?) "
            "OR LOWER(destination_city) LIKE LOWER(?) OR LOWER(origin_port) LIKE LOWER(?) "
            "OR LOWER(destination_port) LIKE LOWER(?) LIMIT ?",
            (like_param, like_param, like_param, like_param, limit),
        ),
        "weather": (
            "SELECT * FROM weather WHERE LOWER(city) LIKE LOWER(?) ORDER BY forecast_date DESC LIMIT ?",
            (like_param, limit),
        ),
    }
    if etype not in sql_map:
        return []
    sql, params = sql_map[etype]
    try:
        with sqlite_connection(db_path) as conn:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]
    except Exception as exc:
        logger.debug("SQLite entity search notice: %s", exc)
        return []


def get_enterprise_summary_counts() -> dict[str, Any]:
    tables = [
        "enterprise_customers",
        "products",
        "carriers",
        "warehouses",
        "routes",
        "vehicles",
        "weather",
        "customs",
        "enterprise_shipments",
        "shipment_delivery_history",
        "ai_model_registry",
        "ai_feature_store",
        "ai_inference_log",
        "ai_monitoring_alerts",
    ]
    db_path = resolve_sqlite_db_path()
    out: dict[str, Any] = {"tables": {}, "derived_delivery_status": {}}
    if db_path is not None:
        try:
            with sqlite_connection(db_path) as conn:
                for t in tables:
                    exists = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (t,)
                    ).fetchone()
                    if exists:
                        out["tables"][t] = int(conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
                hist_exists = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='shipment_delivery_history'"
                ).fetchone()
                if hist_exists:
                    for st, cnt in conn.execute(
                        "SELECT delivery_status, COUNT(*) FROM shipment_delivery_history GROUP BY delivery_status"
                    ).fetchall():
                        out["derived_delivery_status"][st] = int(cnt)
        except Exception as exc:
            logger.debug("Enterprise summary count notice: %s", exc)
    return out
