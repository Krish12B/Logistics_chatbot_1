"""Local CSV/JSON file fallback readers for infrastructure when SQL DBs are unavailable."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

from logistics_chatbot.core import config
from logistics_chatbot.utils.helpers import parse_date, parse_datetime


def load_shipment_rows_from_files() -> list[dict]:
    """Load shipment rows with parsed dates from CSV/JSON seed files."""
    path = config.SHIPMENTS_CSV_PATH
    if not path.exists():
        path = config.SHIPMENT_SEED_PATH
    if not path.exists():
        return []

    rows: list[dict] = []
    if path.suffix == ".json":
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        for item in raw:
            row = dict(item)
            row["estimated_delivery"] = parse_date(row.get("estimated_delivery"))
            row["last_updated"] = parse_datetime(row.get("last_updated"))
            rows.append(row)
    else:
        with open(path, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                row = dict(r)
                row["estimated_delivery"] = parse_date(row.get("estimated_delivery"))
                row["last_updated"] = parse_datetime(row.get("last_updated"))
                for k in ("delay_reason", "current_location", "route", "customs_status"):
                    if row.get(k) == "":
                        row[k] = None
                rows.append(row)
    return rows


def find_employee_in_csv(employee_id: str) -> Optional[dict]:
    """Look up an employee record in the generated roster CSV."""
    clean_id = (employee_id or "").strip().upper()
    emp_csv = config.EMPLOYEES_CSV_PATH
    if not emp_csv.exists():
        return None
    with open(emp_csv, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("employee_id", "").upper() == clean_id:
                return dict(r)
    return None


def find_operational_in_csv(doc_id: str) -> Optional[dict]:
    """Look up an operational record in fallback CSV files if present."""
    clean_id = (doc_id or "").strip().upper()
    candidates = [
        config.PROJECT_ROOT / "attach_data.csv",
        config.PROJECT_ROOT.parent / "attach_data.csv",
        config.RAW_DATA_DIR / "attach_data.csv",
    ]
    for csv_file in candidates:
        if csv_file.exists():
            try:
                with open(csv_file, encoding="utf-8-sig", newline="") as f:
                    for r in csv.DictReader(f):
                        if r.get("doc_id", "").strip().upper() == clean_id:
                            return dict(r)
            except Exception:
                continue
    return None
