"""Enterprise Excel Data Ingestion & Validation Pipeline (Data_attach2.xlsx -> Supabase / SQLite).

Follows workbook README instructions:
  - Preserves UUID primary & foreign keys and normalized data types
  - Inserts Tier 1 -> Tier 2 -> Tier 3 -> Tier 4 respecting FK constraints
  - NEVER stores a 'delayed' column in enterprise_shipments; derives delayed
    status & delay_days strictly from shipment_delivery_history
  - Repeatable & idempotent (ON CONFLICT DO UPDATE upserts, batched)
  - Never drops or truncates existing production tables (shipments SHP-*, customers CUST-*)

Usage:
    python scripts/ingest_excel_supabase.py [--target auto|sqlite|supabase|both] [--file data/new_data/Data_attach2.xlsx]
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import openpyxl

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
for p in (str(_SRC), str(_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from logistics_chatbot.core import config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("ingest_excel_supabase")

# Worksheet -> Target Table Mapping (Strict Tiered Dependency Order)
TABLE_ORDER: List[Tuple[str, str, str]] = [
    # Tier 1: Dimensions & Registry
    ("Customers", "enterprise_customers", "customer_id"),
    ("Products", "products", "product_id"),
    ("Carriers", "carriers", "carrier_id"),
    ("Warehouses", "warehouses", "warehouse_id"),
    ("Routes", "routes", "route_id"),
    ("Vehicles", "vehicles", "vehicle_id"),
    ("Weather", "weather", "weather_id"),
    ("Customs", "customs", "customs_id"),
    ("AI_Model_Registry", "ai_model_registry", "model_id"),
    # Tier 2: Core Shipments Fact (no delayed column)
    ("Shipments", "enterprise_shipments", "shipment_id"),
    # Tier 3: Child History / Features / Inferences
    ("Shipment_Delivery_History", "shipment_delivery_history", "history_id"),
    ("AI_Feature_Store", "ai_feature_store", "feature_record_id"),
    ("AI_Inference_Log", "ai_inference_log", "inference_id"),
    # Tier 4: Leaf Alerts
    ("AI_Monitoring_Alerts", "ai_monitoring_alerts", "alert_id"),
]

# Foreign-key definitions for pre-insert referential validation: (sheet, fk_col, parent_sheet, parent_pk)
FK_RULES: List[Tuple[str, str, str, str]] = [
    ("Shipments", "customer_id", "Customers", "customer_id"),
    ("Shipments", "product_id", "Products", "product_id"),
    ("Shipments", "carrier_id", "Carriers", "carrier_id"),
    ("Shipments", "warehouse_id", "Warehouses", "warehouse_id"),
    ("Shipments", "route_id", "Routes", "route_id"),
    ("Shipments", "vehicle_id", "Vehicles", "vehicle_id"),
    ("Shipments", "customs_id", "Customs", "customs_id"),
    ("Shipments", "weather_id", "Weather", "weather_id"),
    ("Shipment_Delivery_History", "shipment_id", "Shipments", "shipment_id"),
    ("AI_Feature_Store", "shipment_id", "Shipments", "shipment_id"),
    ("AI_Inference_Log", "shipment_id", "Shipments", "shipment_id"),
    ("AI_Inference_Log", "model_id", "AI_Model_Registry", "model_id"),
    ("AI_Monitoring_Alerts", "shipment_id", "Shipments", "shipment_id"),
    ("AI_Monitoring_Alerts", "inference_id", "AI_Inference_Log", "inference_id"),
]


def _val_uuid(val: Any) -> str:
    return str(uuid.UUID(str(val).strip())).lower()


def _val_str(val: Any) -> str:
    s = "" if val is None else str(val).strip()
    if not s:
        raise ValueError("Required text value is empty")
    return s


def _val_opt_str(val: Any) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _val_int(val: Any) -> int:
    return int(val)


def _val_float(val: Any) -> float:
    return round(float(val), 6)


def _val_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    s = str(val).strip().lower()
    if s in ("true", "1", "yes", "y"):
        return True
    if s in ("false", "0", "no", "n"):
        return False
    raise ValueError(f"Invalid boolean literal: {val!r}")


def _val_date(val: Any) -> str:
    if isinstance(val, datetime):
        return val.date().isoformat()
    if isinstance(val, date):
        return val.isoformat()
    s = str(val).strip()[:10]
    return datetime.strptime(s, "%Y-%m-%d").date().isoformat()


def _val_timestamp(val: Any) -> str:
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    s = str(val).strip().replace("T", " ")[:19]
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")


def _val_json(val: Any) -> str:
    parsed = json.loads(str(val))
    return json.dumps(parsed, separators=(",", ":"))


COLUMN_SCHEMAS: Dict[str, List[Tuple[str, Callable[[Any], Any]]]] = {
    "Customers": [
        ("customer_id", _val_uuid), ("customer_name", _val_str), ("customer_type", _val_str),
        ("industry", _val_str), ("city", _val_str), ("state", _val_str), ("country", _val_str),
        ("registration_date", _val_date), ("customer_status", _val_str),
    ],
    "Products": [
        ("product_id", _val_uuid), ("product_name", _val_str), ("category", _val_str),
        ("hs_code", _val_str), ("hazardous", _val_bool), ("perishable", _val_bool),
        ("temperature_controlled", _val_bool), ("fragile", _val_bool),
        ("weight_per_unit", _val_float), ("supplier_name", _val_str),
    ],
    "Carriers": [
        ("carrier_id", _val_uuid), ("carrier_name", _val_str), ("carrier_type", _val_str),
        ("average_rating", _val_float), ("fleet_size", _val_int),
        ("years_of_service", _val_int), ("headquarters", _val_opt_str),
    ],
    "Warehouses": [
        ("warehouse_id", _val_uuid), ("warehouse_name", _val_str), ("city", _val_str),
        ("state", _val_str), ("warehouse_capacity", _val_int),
        ("current_utilization", _val_float), ("warehouse_type", _val_str),
    ],
    "Routes": [
        ("route_id", _val_uuid), ("origin_city", _val_str), ("destination_city", _val_str),
        ("origin_country", _val_str), ("destination_country", _val_str),
        ("origin_port", _val_str), ("destination_port", _val_str),
        ("distance_km", _val_float), ("average_transit_days", _val_int),
        ("route_risk", _val_str), ("traffic_index", _val_int),
    ],
    "Vehicles": [
        ("vehicle_id", _val_uuid), ("vehicle_number", _val_str), ("vehicle_type", _val_str),
        ("capacity_kg", _val_float), ("fuel_type", _val_str),
        ("maintenance_status", _val_str), ("vehicle_age", _val_int),
    ],
    "Weather": [
        ("weather_id", _val_uuid), ("city", _val_str), ("forecast_date", _val_date),
        ("weather_condition", _val_str), ("temperature", _val_float), ("rainfall", _val_float),
        ("humidity", _val_float), ("wind_speed", _val_float), ("visibility", _val_float),
    ],
    "Customs": [
        ("customs_id", _val_uuid), ("customs_required", _val_bool),
        ("documentation_complete", _val_bool), ("inspection_required", _val_bool),
        ("cargo_type", _val_str), ("destination_country", _val_str),
    ],
    "AI_Model_Registry": [
        ("model_id", _val_uuid), ("model_name", _val_str), ("model_version", _val_str),
        ("model_type", _val_str), ("training_dataset_version", _val_str),
        ("artifact_uri", _val_str), ("deployment_status", _val_str),
    ],
    "Shipments": [
        ("shipment_id", _val_uuid), ("booking_id", _val_str), ("customer_id", _val_uuid),
        ("product_id", _val_uuid), ("carrier_id", _val_uuid), ("warehouse_id", _val_uuid),
        ("route_id", _val_uuid), ("vehicle_id", _val_uuid), ("customs_id", _val_uuid),
        ("weather_id", _val_uuid), ("booking_date", _val_date), ("ship_date", _val_date),
        ("expected_delivery_date", _val_date), ("shipping_mode", _val_str),
        ("shipment_type", _val_str), ("priority", _val_str), ("weight_kg", _val_float),
        ("volume_cbm", _val_float), ("declared_value", _val_float),
        ("insurance", _val_bool), ("fragile", _val_bool),
    ],
    "Shipment_Delivery_History": [
        ("history_id", _val_uuid), ("shipment_id", _val_uuid),
        ("actual_delivery_date", _val_date), ("delivery_status", _val_str),
        ("delivery_attempts", _val_int),
    ],
    "AI_Feature_Store": [
        ("feature_record_id", _val_uuid), ("shipment_id", _val_uuid),
        ("feature_timestamp", _val_timestamp), ("route_delay_rate", _val_float),
        ("carrier_reliability_score", _val_float), ("weather_severity_score", _val_float),
        ("feature_vector_json", _val_json),
    ],
    "AI_Inference_Log": [
        ("inference_id", _val_uuid), ("shipment_id", _val_uuid), ("model_id", _val_uuid),
        ("prediction_timestamp", _val_timestamp), ("delay_probability", _val_float),
        ("risk_category", _val_str), ("latency_ms", _val_int),
    ],
    "AI_Monitoring_Alerts": [
        ("alert_id", _val_uuid), ("shipment_id", _val_uuid), ("inference_id", _val_uuid),
        ("alert_type", _val_str), ("severity", _val_str),
        ("recommended_action", _val_str), ("alert_status", _val_str),
    ],
}

SQLITE_ENTERPRISE_DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS enterprise_customers (
    customer_id TEXT PRIMARY KEY CHECK (length(customer_id) = 36),
    customer_name TEXT NOT NULL,
    customer_type TEXT NOT NULL,
    industry TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    country TEXT NOT NULL,
    registration_date TEXT NOT NULL,
    customer_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY CHECK (length(product_id) = 36),
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    hs_code TEXT NOT NULL,
    hazardous INTEGER NOT NULL CHECK (hazardous IN (0, 1)),
    perishable INTEGER NOT NULL CHECK (perishable IN (0, 1)),
    temperature_controlled INTEGER NOT NULL CHECK (temperature_controlled IN (0, 1)),
    fragile INTEGER NOT NULL CHECK (fragile IN (0, 1)),
    weight_per_unit REAL NOT NULL,
    supplier_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS carriers (
    carrier_id TEXT PRIMARY KEY CHECK (length(carrier_id) = 36),
    carrier_name TEXT NOT NULL,
    carrier_type TEXT NOT NULL,
    average_rating REAL,
    fleet_size INTEGER,
    years_of_service INTEGER,
    headquarters TEXT
);

CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id TEXT PRIMARY KEY CHECK (length(warehouse_id) = 36),
    warehouse_name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    warehouse_capacity INTEGER NOT NULL,
    current_utilization REAL,
    warehouse_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS routes (
    route_id TEXT PRIMARY KEY CHECK (length(route_id) = 36),
    origin_city TEXT NOT NULL,
    destination_city TEXT NOT NULL,
    origin_country TEXT NOT NULL,
    destination_country TEXT NOT NULL,
    origin_port TEXT NOT NULL,
    destination_port TEXT NOT NULL,
    distance_km REAL NOT NULL,
    average_transit_days INTEGER NOT NULL,
    route_risk TEXT NOT NULL,
    traffic_index INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id TEXT PRIMARY KEY CHECK (length(vehicle_id) = 36),
    vehicle_number TEXT NOT NULL,
    vehicle_type TEXT NOT NULL,
    capacity_kg REAL NOT NULL,
    fuel_type TEXT NOT NULL,
    maintenance_status TEXT NOT NULL,
    vehicle_age INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS weather (
    weather_id TEXT PRIMARY KEY CHECK (length(weather_id) = 36),
    city TEXT NOT NULL,
    forecast_date TEXT NOT NULL,
    weather_condition TEXT NOT NULL,
    temperature REAL,
    rainfall REAL,
    humidity REAL,
    wind_speed REAL,
    visibility REAL
);

CREATE TABLE IF NOT EXISTS customs (
    customs_id TEXT PRIMARY KEY CHECK (length(customs_id) = 36),
    customs_required INTEGER NOT NULL CHECK (customs_required IN (0, 1)),
    documentation_complete INTEGER NOT NULL CHECK (documentation_complete IN (0, 1)),
    inspection_required INTEGER NOT NULL CHECK (inspection_required IN (0, 1)),
    cargo_type TEXT NOT NULL,
    destination_country TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_model_registry (
    model_id TEXT PRIMARY KEY CHECK (length(model_id) = 36),
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    model_type TEXT NOT NULL,
    training_dataset_version TEXT NOT NULL,
    artifact_uri TEXT NOT NULL,
    deployment_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS enterprise_shipments (
    shipment_id TEXT PRIMARY KEY CHECK (length(shipment_id) = 36),
    booking_id TEXT NOT NULL UNIQUE,
    customer_id TEXT NOT NULL REFERENCES enterprise_customers(customer_id),
    product_id TEXT NOT NULL REFERENCES products(product_id),
    carrier_id TEXT NOT NULL REFERENCES carriers(carrier_id),
    warehouse_id TEXT NOT NULL REFERENCES warehouses(warehouse_id),
    route_id TEXT NOT NULL REFERENCES routes(route_id),
    vehicle_id TEXT NOT NULL REFERENCES vehicles(vehicle_id),
    customs_id TEXT NOT NULL REFERENCES customs(customs_id),
    weather_id TEXT NOT NULL REFERENCES weather(weather_id),
    booking_date TEXT NOT NULL,
    ship_date TEXT NOT NULL,
    expected_delivery_date TEXT NOT NULL,
    shipping_mode TEXT NOT NULL,
    shipment_type TEXT NOT NULL,
    priority TEXT NOT NULL,
    weight_kg REAL NOT NULL,
    volume_cbm REAL NOT NULL,
    declared_value REAL NOT NULL,
    insurance INTEGER NOT NULL CHECK (insurance IN (0, 1)),
    fragile INTEGER NOT NULL CHECK (fragile IN (0, 1))
);

CREATE TABLE IF NOT EXISTS shipment_delivery_history (
    history_id TEXT PRIMARY KEY CHECK (length(history_id) = 36),
    shipment_id TEXT NOT NULL REFERENCES enterprise_shipments(shipment_id),
    actual_delivery_date TEXT NOT NULL,
    delivery_status TEXT NOT NULL,
    delivery_attempts INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_feature_store (
    feature_record_id TEXT PRIMARY KEY CHECK (length(feature_record_id) = 36),
    shipment_id TEXT NOT NULL REFERENCES enterprise_shipments(shipment_id),
    feature_timestamp TEXT NOT NULL,
    route_delay_rate REAL NOT NULL,
    carrier_reliability_score REAL NOT NULL,
    weather_severity_score REAL NOT NULL,
    feature_vector_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_inference_log (
    inference_id TEXT PRIMARY KEY CHECK (length(inference_id) = 36),
    shipment_id TEXT NOT NULL REFERENCES enterprise_shipments(shipment_id),
    model_id TEXT NOT NULL REFERENCES ai_model_registry(model_id),
    prediction_timestamp TEXT NOT NULL,
    delay_probability REAL NOT NULL,
    risk_category TEXT NOT NULL,
    latency_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_monitoring_alerts (
    alert_id TEXT PRIMARY KEY CHECK (length(alert_id) = 36),
    shipment_id TEXT NOT NULL REFERENCES enterprise_shipments(shipment_id),
    inference_id TEXT NOT NULL REFERENCES ai_inference_log(inference_id),
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    alert_status TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sq_ent_ship_booking ON enterprise_shipments(booking_id);
CREATE INDEX IF NOT EXISTS idx_sq_ent_hist_ship ON shipment_delivery_history(shipment_id);
CREATE INDEX IF NOT EXISTS idx_sq_ent_feat_ship ON ai_feature_store(shipment_id);
CREATE INDEX IF NOT EXISTS idx_sq_ent_inf_ship ON ai_inference_log(shipment_id);
CREATE INDEX IF NOT EXISTS idx_sq_ent_alert_ship ON ai_monitoring_alerts(shipment_id);
CREATE INDEX IF NOT EXISTS idx_sq_ent_cust_name ON enterprise_customers(customer_name);
CREATE INDEX IF NOT EXISTS idx_sq_ent_carrier_name ON carriers(carrier_name);

CREATE VIEW IF NOT EXISTS v_enterprise_shipments_status AS
SELECT
    s.*,
    h.history_id,
    h.actual_delivery_date,
    h.delivery_status AS derived_status,
    h.delivery_attempts,
    CASE WHEN h.delivery_status = 'Delayed' THEN 1 ELSE 0 END AS is_delayed,
    MAX(0, CAST(julianday(h.actual_delivery_date) - julianday(s.expected_delivery_date) AS INTEGER)) AS delay_days
FROM enterprise_shipments s
LEFT JOIN shipment_delivery_history h
    ON h.shipment_id = s.shipment_id;
"""


def load_and_validate_workbook(xlsx_path: Path) -> Dict[str, Any]:
    """Read, normalize, type-validate, and FK-verify all 14 Excel sheets cleanly."""
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Excel workbook not found: {xlsx_path}")

    wb = openpyxl.load_workbook(str(xlsx_path), read_only=True, data_only=True)
    parsed_sheets: Dict[str, List[Dict[str, Any]]] = {}
    pk_sets: Dict[str, set[str]] = {}
    validation_errors: List[Dict[str, Any]] = []

    for sheet_name, _tbl, pk_col in TABLE_ORDER:
        if sheet_name not in wb.sheetnames:
            raise ValueError(f"Expected worksheet '{sheet_name}' missing in {xlsx_path.name}")

        schema = COLUMN_SCHEMAS[sheet_name]
        ws = wb[sheet_name]
        rows_iter = ws.iter_rows(values_only=True)
        headers = next(rows_iter, None)
        if not headers:
            raise ValueError(f"Worksheet '{sheet_name}' has no header row")
        header_names = [str(h).strip() for h in headers]

        if sheet_name == "Shipments" and "delayed" in [h.lower() for h in header_names]:
            raise ValueError("Special rule violation: 'delayed' column found directly on Shipments sheet")

        idx_map = {name: i for i, name in enumerate(header_names)}
        valid_rows: List[Dict[str, Any]] = []
        seen_pks: set[str] = set()

        for row_num, raw_row in enumerate(rows_iter, start=2):
            if all(v is None for v in raw_row):
                continue
            record: Dict[str, Any] = {}
            row_ok = True
            for col_name, caster in schema:
                if col_name not in idx_map:
                    validation_errors.append({
                        "sheet": sheet_name, "row": row_num, "error": f"Missing column {col_name}"
                    })
                    row_ok = False
                    break
                raw_val = raw_row[idx_map[col_name]]
                try:
                    record[col_name] = caster(raw_val)
                except Exception as exc:
                    validation_errors.append({
                        "sheet": sheet_name, "row": row_num, "column": col_name, "error": str(exc)
                    })
                    row_ok = False
                    break

            if not row_ok:
                continue

            pk_val = record[pk_col]
            if pk_val in seen_pks:
                validation_errors.append({
                    "sheet": sheet_name, "row": row_num, "error": f"Duplicate PK {pk_val}"
                })
                continue
            seen_pks.add(pk_val)
            valid_rows.append(record)

        parsed_sheets[sheet_name] = valid_rows
        pk_sets[sheet_name] = seen_pks

    # Validate foreign-key integrity prior to DB insertion
    fk_report: List[Dict[str, Any]] = []
    for sheet_name, fk_col, parent_sheet, _parent_pk in FK_RULES:
        parent_pks = pk_sets[parent_sheet]
        orphans = [r[fk_col] for r in parsed_sheets[sheet_name] if r[fk_col] not in parent_pks]
        fk_report.append({
            "relationship": f"{sheet_name}.{fk_col} -> {parent_sheet}",
            "checked": len(parsed_sheets[sheet_name]),
            "orphans": len(orphans),
        })
        if orphans:
            raise ValueError(f"Referential integrity check failed for {sheet_name}.{fk_col}: {len(orphans)} orphans")

    # Derive delayed status from Shipment_Delivery_History (without storing in Shipments)
    ship_expected = {r["shipment_id"]: r["expected_delivery_date"] for r in parsed_sheets["Shipments"]}
    derived_stats = {"total": 0, "Delayed": 0, "Delivered": 0, "max_delay_days": 0}
    for h in parsed_sheets["Shipment_Delivery_History"]:
        derived_stats["total"] += 1
        st = h["delivery_status"]
        derived_stats[st] = derived_stats.get(st, 0) + 1
        exp_d = datetime.strptime(ship_expected[h["shipment_id"]], "%Y-%m-%d").date()
        act_d = datetime.strptime(h["actual_delivery_date"], "%Y-%m-%d").date()
        delay_d = max(0, (act_d - exp_d).days)
        if delay_d > derived_stats["max_delay_days"]:
            derived_stats["max_delay_days"] = delay_d

    return {
        "sheets": parsed_sheets,
        "validation_errors": validation_errors,
        "fk_report": fk_report,
        "derived_delay_stats": derived_stats,
    }


def _to_sqlite_val(val: Any) -> Any:
    if isinstance(val, bool):
        return 1 if val else 0
    return val


def ingest_into_sqlite(
    validated: Dict[str, Any],
    db_path: Path,
    batch_size: int = 500,
) -> Dict[str, int]:
    """Create enterprise schema and upsert all 14 Excel tables cleanly into SQLite."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    counts: Dict[str, int] = {}

    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(SQLITE_ENTERPRISE_DDL)
        conn.execute("PRAGMA foreign_keys = ON;")

        for sheet_name, table_name, pk_col in TABLE_ORDER:
            rows = validated["sheets"][sheet_name]
            cols = [c for c, _ in COLUMN_SCHEMAS[sheet_name]]
            col_list = ", ".join(cols)
            placeholders = ", ".join("?" for _ in cols)
            updates = ", ".join(f"{c} = excluded.{c}" for c in cols if c != pk_col)
            sql = (
                f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders}) "
                f"ON CONFLICT({pk_col}) DO UPDATE SET {updates}"
            )

            inserted = 0
            for start in range(0, len(rows), batch_size):
                batch = rows[start : start + batch_size]
                tuples = [tuple(_to_sqlite_val(r[c]) for c in cols) for r in batch]
                conn.executemany(sql, tuples)
                inserted += len(batch)
            conn.commit()
            verified_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            counts[table_name] = verified_count
            logger.info("SQLite upserted %-28s -> %d rows (verified total: %d)", table_name, inserted, verified_count)

    return counts


def ingest_into_supabase(
    validated: Dict[str, Any],
    batch_size: int = 500,
) -> Dict[str, int]:
    """Apply DDL migration and upsert all 14 Excel tables into Supabase PostgreSQL."""
    if not config.SUPABASE_DB_URL:
        raise RuntimeError(
            "SUPABASE_DB_URL is not configured in .env; cannot connect to live Supabase PostgreSQL."
        )

    import psycopg2
    import psycopg2.extras

    ddl_path = _ROOT / "docs" / "architecture" / "schema_v2_enterprise.sql"
    ddl_sql = ddl_path.read_text(encoding="utf-8")
    counts: Dict[str, int] = {}

    with psycopg2.connect(config.SUPABASE_DB_URL, connect_timeout=config.DB_CONNECT_TIMEOUT) as conn:
        with conn.cursor() as cur:
            cur.execute(ddl_sql)
            for sheet_name, table_name, pk_col in TABLE_ORDER:
                rows = validated["sheets"][sheet_name]
                cols = [c for c, _ in COLUMN_SCHEMAS[sheet_name]]
                col_list = ", ".join(cols)
                updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != pk_col)
                sql = (
                    f"INSERT INTO public.{table_name} ({col_list}) VALUES %s "
                    f"ON CONFLICT ({pk_col}) DO UPDATE SET {updates}"
                )
                for start in range(0, len(rows), batch_size):
                    batch = rows[start : start + batch_size]
                    tuples = [tuple(r[c] for c in cols) for r in batch]
                    psycopg2.extras.execute_values(cur, sql, tuples, page_size=batch_size)
                cur.execute(f"SELECT COUNT(*) FROM public.{table_name}")
                counts[table_name] = int(cur.fetchone()[0])
        conn.commit()
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate & ingest Data_attach2.xlsx into Supabase / SQLite")
    parser.add_argument("--file", type=Path, default=_ROOT / "data" / "new_data" / "Data_attach2.xlsx")
    parser.add_argument("--target", choices=["auto", "sqlite", "supabase", "both"], default="auto")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--report", type=Path, default=_ROOT / "tests" / "reports" / "excel_ingestion_report.json")
    args = parser.parse_args()

    print("=" * 72)
    print("NEXUSFREIGHT EXCEL RELATIONAL DATASET VALIDATION & INGESTION")
    print("=" * 72)

    validated = load_and_validate_workbook(args.file)
    total_rows = sum(len(v) for v in validated["sheets"].values())
    print(f"Workbook Validated : {args.file.name} ({len(validated['sheets'])} tables, {total_rows:,} rows)")
    print(f"Validation Errors  : {len(validated['validation_errors'])}")
    print(f"FK Checks Passed   : {len(validated['fk_report'])}/{len(validated['fk_report'])} (0 orphans)")
    print(f"Derived Delays     : {validated['derived_delay_stats']}")

    sqlite_counts: Dict[str, int] = {}
    supabase_counts: Dict[str, int] = {}
    supabase_status = "not_requested"

    run_sqlite = args.target in ("auto", "sqlite", "both")
    run_supa = args.target in ("supabase", "both") or (args.target == "auto" and bool(config.SUPABASE_DB_URL))

    if run_sqlite:
        db_path = config.DB_PATH if getattr(config, "DB_PATH", None) else (_ROOT / "data" / "raw" / "shipments.db")
        sqlite_counts = ingest_into_sqlite(validated, db_path, batch_size=args.batch_size)
        print(f"\nSQLite Import Complete ({sum(sqlite_counts.values()):,} verified rows in {db_path.name}).")

    if run_supa:
        if not config.SUPABASE_DB_URL:
            supabase_status = "blocked_missing_credentials"
            print("\nSupabase PostgreSQL Import BLOCKED: SUPABASE_DB_URL is empty in .env.")
        else:
            supabase_counts = ingest_into_supabase(validated, batch_size=args.batch_size)
            supabase_status = "completed"
            print(f"\nSupabase PostgreSQL Import Complete ({sum(supabase_counts.values()):,} verified rows).")
    else:
        supabase_status = "blocked_missing_credentials" if not config.SUPABASE_DB_URL else "skipped"

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({
            "workbook": str(args.file.name),
            "total_validated_rows": total_rows,
            "validation_errors": validated["validation_errors"],
            "fk_checks": validated["fk_report"],
            "derived_delay_stats": validated["derived_delay_stats"],
            "sqlite_table_counts": sqlite_counts,
            "supabase_status": supabase_status,
            "supabase_table_counts": supabase_counts,
        }, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
