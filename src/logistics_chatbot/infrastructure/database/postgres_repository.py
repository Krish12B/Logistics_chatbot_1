"""PostgreSQL (Supabase) repository implementation."""
from __future__ import annotations

import logging
from typing import Any, Optional

from logistics_chatbot.core import config
from logistics_chatbot.core.errors import DatabaseError
from logistics_chatbot.infrastructure.database.connection import run_postgres_query
from logistics_chatbot.infrastructure.database.sqlite_repository import (
    ENTERPRISE_SHIPMENT_SQL_SELECT,
    enrich_enterprise_shipment_dict,
)

logger = logging.getLogger("logistics_chatbot.database.postgres")

SCHEMA_CHECK_SQL = """
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


def check_schema(query_fn=None) -> None:
    """Verify PostgreSQL schema objects (shipments, knowledge_base, match_knowledge)."""
    exec_query = query_fn or run_postgres_query
    rows = exec_query(SCHEMA_CHECK_SQL)
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
                "Run the SQL in migrations/sql/schema.sql (or docs/architecture/schema.sql) to create them."
            )
        )
    logger.info("Database schema verified: all required objects present")


def fetch_shipment_row(shipment_id: str, query_fn=None) -> Optional[dict]:
    exec_query = query_fn or run_postgres_query
    rows = exec_query("SELECT * FROM shipments WHERE shipment_id = %s", (shipment_id,))
    return rows[0] if rows else None


def fetch_employee_row(employee_id: str, query_fn=None) -> Optional[dict]:
    exec_query = query_fn or run_postgres_query
    rows = exec_query("SELECT * FROM employees WHERE employee_id = %s", (employee_id,))
    return rows[0] if rows else None


def init_operational_table(query_fn=None) -> None:
    exec_query = query_fn or run_postgres_query
    exec_query(
        """
        CREATE TABLE IF NOT EXISTS public.operational_records (
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
            last_updated DATE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )


def fetch_operational_record(doc_id: str, query_fn=None) -> Optional[dict]:
    exec_query = query_fn or run_postgres_query
    rows = exec_query("SELECT * FROM operational_records WHERE UPPER(doc_id) = %s", (doc_id,))
    return rows[0] if rows else None


def upsert_operational_records(records: list[dict], query_fn=None) -> None:
    exec_query = query_fn or run_postgres_query
    for r in records:
        doc_id = (r.get("doc_id") or "").strip().upper()
        if not doc_id:
            continue
        exec_query(
            """
            INSERT INTO public.operational_records (
                doc_id, category, section_title, content, tags,
                status, origin, destination, assigned_employee,
                responsible_department, risk_factors, last_updated
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(doc_id) DO UPDATE SET
                category = EXCLUDED.category,
                section_title = EXCLUDED.section_title,
                content = EXCLUDED.content,
                tags = EXCLUDED.tags,
                status = EXCLUDED.status,
                origin = EXCLUDED.origin,
                destination = EXCLUDED.destination,
                assigned_employee = EXCLUDED.assigned_employee,
                responsible_department = EXCLUDED.responsible_department,
                risk_factors = EXCLUDED.risk_factors,
                last_updated = EXCLUDED.last_updated;
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
                r.get("last_updated") or None,
            ),
        )


def get_shipment_status_counts(query_fn=None) -> Optional[dict[str, int]]:
    exec_query = query_fn or run_postgres_query
    rows = exec_query("SELECT status, COUNT(*) AS count FROM shipments GROUP BY status")
    return {r["status"]: int(r["count"]) for r in rows} if rows else None


def get_employee_counts(query_fn=None) -> Optional[dict[str, Any]]:
    exec_query = query_fn or run_postgres_query
    rows = exec_query("SELECT department, COUNT(*) AS count FROM employees GROUP BY department")
    if not rows:
        return None
    dept_counts = {r["department"]: int(r["count"]) for r in rows}
    return {"total": sum(dept_counts.values()), "by_department": dept_counts}


def get_enterprise_shipment(lookup_val: str, is_uuid: bool, query_fn=None) -> Optional[dict]:
    exec_query = query_fn or run_postgres_query
    where = "s.shipment_id = %s::uuid" if is_uuid else "UPPER(s.booking_id) = %s"
    rows = exec_query(f"{ENTERPRISE_SHIPMENT_SQL_SELECT} WHERE {where}", (lookup_val,))
    if not rows:
        return None
    sid = str(rows[0]["shipment_id"])
    feats = exec_query(
        "SELECT route_delay_rate, carrier_reliability_score, weather_severity_score, feature_timestamp "
        "FROM ai_feature_store WHERE shipment_id = %s::uuid ORDER BY feature_timestamp DESC LIMIT 1",
        (sid,),
    )
    infs = exec_query(
        "SELECT ai.delay_probability, ai.risk_category, ai.latency_ms, ai.prediction_timestamp, "
        "mr.model_name, mr.model_version, mr.deployment_status "
        "FROM ai_inference_log ai JOIN ai_model_registry mr ON mr.model_id = ai.model_id "
        "WHERE ai.shipment_id = %s::uuid ORDER BY ai.prediction_timestamp DESC LIMIT 1",
        (sid,),
    )
    alerts = exec_query(
        "SELECT alert_type, severity, recommended_action, alert_status "
        "FROM ai_monitoring_alerts WHERE shipment_id = %s::uuid LIMIT 5",
        (sid,),
    )
    return enrich_enterprise_shipment_dict(
        rows[0],
        alerts,
        feats[0] if feats else None,
        infs[0] if infs else None,
    )


def search_enterprise_entity(entity_type: str, clean: str, limit: int = 5, query_fn=None) -> list[dict]:
    exec_query = query_fn or run_postgres_query
    etype = entity_type.lower().strip()
    if etype == "route" and "->" in clean:
        orig_q, dest_q = [p.strip() for p in clean.split("->", 1)]
        rt_sql = (
            "SELECT * FROM routes WHERE LOWER(origin_city) LIKE LOWER(%s) "
            "AND LOWER(destination_city) LIKE LOWER(%s) LIMIT %s"
        )
        return exec_query(rt_sql, (f"%{orig_q}%", f"%{dest_q}%", limit))

    like_param = f"%{clean}%"
    sql_map = {
        "customer": (
            "SELECT * FROM enterprise_customers WHERE LOWER(customer_name) LIKE LOWER(%s) "
            "OR LOWER(customer_id) = LOWER(%s) LIMIT %s",
            (like_param, clean, limit),
        ),
        "carrier": (
            "SELECT * FROM carriers WHERE LOWER(carrier_name) LIKE LOWER(%s) "
            "OR LOWER(carrier_id) = LOWER(%s) LIMIT %s",
            (like_param, clean, limit),
        ),
        "warehouse": (
            "SELECT * FROM warehouses WHERE LOWER(warehouse_name) LIKE LOWER(%s) "
            "OR LOWER(city) LIKE LOWER(%s) OR LOWER(warehouse_id) = LOWER(%s) LIMIT %s",
            (like_param, like_param, clean, limit),
        ),
        "route": (
            "SELECT * FROM routes WHERE LOWER(origin_city) LIKE LOWER(%s) "
            "OR LOWER(destination_city) LIKE LOWER(%s) OR LOWER(origin_port) LIKE LOWER(%s) "
            "OR LOWER(destination_port) LIKE LOWER(%s) LIMIT %s",
            (like_param, like_param, like_param, like_param, limit),
        ),
        "weather": (
            "SELECT * FROM weather WHERE LOWER(city) LIKE LOWER(%s) ORDER BY forecast_date DESC LIMIT %s",
            (like_param, limit),
        ),
    }
    if etype not in sql_map:
        return []
    sql, params = sql_map[etype]
    return exec_query(sql, params)
