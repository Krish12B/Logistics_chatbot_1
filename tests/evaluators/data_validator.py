"""Comprehensive automated data validator for FleetHarbor Logistics datasets.
Performs read-only structural, referential, and business-rule validation across:
  - SQLite database: data/raw/shipments.db (10,000 shipments, 500 employees, 100 customers, 10 hubs)
  - Processed CSV: data/processed/shipments.csv
  - Raw CSV: data/raw/shipments.csv
  - Knowledge Base: data/knowledge_base/kb_long.csv

Outputs: tests/reports/data_validation_report.json
"""
from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "raw" / "shipments.db"
CSV_PROCESSED = ROOT / "data" / "processed" / "shipments.csv"
CSV_RAW = ROOT / "data" / "raw" / "shipments.csv"
KB_CSV = ROOT / "data" / "knowledge_base" / "kb_long.csv"
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

VALID_STATUSES = {
    "in transit",
    "delivered",
    "delayed",
    "on hold - customs",
    "customs hold",
    "out for delivery",
    "pending",
    "cancelled",
}

ID_REGEX = re.compile(r"^SHP-\d{5}$")
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?$")


def validate_shipment_dataset() -> Dict[str, Any]:
    """Inspect and validate all shipment records in SQLite and CSV."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "database_path": str(DB_PATH),
        "total_records_checked": 0,
        "valid_records_count": 0,
        "invalid_records_count": 0,
        "records_with_warnings": 0,
        "summary": {},
        "issues_by_category": {
            "duplicate_ids": [],
            "invalid_id_formats": [],
            "missing_required_fields": [],
            "invalid_status_values": [],
            "date_format_inconsistencies": [],
            "business_rule_violations": [],
            "csv_database_discrepancies": [],
        },
        "proposed_corrections": [],
    }

    if not DB_PATH.exists():
        report["summary"]["error"] = f"Database file not found at {DB_PATH}"
        return report

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM shipments")
    rows = cur.fetchall()
    report["total_records_checked"] = len(rows)

    seen_ids = set()
    valid_count = 0
    invalid_count = 0
    warning_count = 0

    for idx, row in enumerate(rows, start=1):
        r = dict(row)
        sid = r.get("shipment_id", "")
        origin = r.get("origin", "")
        dest = r.get("destination", "")
        status = (r.get("status") or "").strip().lower()
        curr_loc = r.get("current_location", "")
        eta = r.get("estimated_delivery", "")
        updated = r.get("last_updated", "")
        delay = r.get("delay_reason", "")
        customs = r.get("customs_status", "")

        is_valid = True
        has_warning = False

        # 1. ID check
        if not sid:
            report["issues_by_category"]["missing_required_fields"].append({
                "row_index": idx,
                "field": "shipment_id",
                "detail": "Null or empty shipment_id"
            })
            is_valid = False
        elif not ID_REGEX.match(sid):
            report["issues_by_category"]["invalid_id_formats"].append({
                "shipment_id": sid,
                "detail": f"ID does not match standard pattern SHP-XXXXX"
            })
            is_valid = False

        if sid in seen_ids:
            report["issues_by_category"]["duplicate_ids"].append({
                "shipment_id": sid,
                "row_index": idx
            })
            is_valid = False
        seen_ids.add(sid)

        # 2. Required fields
        for req_field, val in [("origin", origin), ("destination", dest), ("status", status)]:
            if not val or not str(val).strip():
                report["issues_by_category"]["missing_required_fields"].append({
                    "shipment_id": sid,
                    "field": req_field,
                    "detail": f"Field '{req_field}' is empty or null"
                })
                is_valid = False

        # 3. Status value validity
        if status and status not in VALID_STATUSES:
            report["issues_by_category"]["invalid_status_values"].append({
                "shipment_id": sid,
                "status": status,
                "detail": f"Status '{status}' not in approved list of statuses"
            })
            is_valid = False

        # 4. Date validation
        if eta:
            if not DATE_REGEX.match(str(eta).strip()):
                report["issues_by_category"]["date_format_inconsistencies"].append({
                    "shipment_id": sid,
                    "field": "estimated_delivery",
                    "value": str(eta),
                    "detail": "Does not match YYYY-MM-DD format"
                })
                has_warning = True

        if updated:
            if not DATETIME_REGEX.match(str(updated).strip()):
                report["issues_by_category"]["date_format_inconsistencies"].append({
                    "shipment_id": sid,
                    "field": "last_updated",
                    "value": str(updated),
                    "detail": "Does not match YYYY-MM-DD or YYYY-MM-DD HH:MM format"
                })
                has_warning = True

        # 5. Business rules
        # If status is Delayed, delay_reason should ideally be populated
        if "delayed" in status and not delay:
            report["issues_by_category"]["business_rule_violations"].append({
                "shipment_id": sid,
                "rule": "Delayed status missing delay_reason",
                "detail": "Shipment is marked Delayed but delay_reason is empty"
            })
            has_warning = True

        # If status is Delivered, customs should normally be Cleared or Not required
        if "delivered" in status and "held" in (customs or "").lower():
            report["issues_by_category"]["business_rule_violations"].append({
                "shipment_id": sid,
                "rule": "Delivered with active customs hold",
                "detail": f"Shipment marked Delivered but customs_status is '{customs}'"
            })
            is_valid = False

        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1

        if has_warning:
            warning_count += 1

    # Cross-validate SQLite vs Processed CSV
    if CSV_PROCESSED.exists():
        with open(CSV_PROCESSED, "r", encoding="utf-8-sig") as fp:
            reader = csv.DictReader(fp)
            csv_rows = list(reader)
            csv_count = len(csv_rows)
            report["summary"]["processed_csv_records"] = csv_count
            report["summary"]["sqlite_records"] = len(rows)

            if csv_count != len(rows):
                report["issues_by_category"]["csv_database_discrepancies"].append({
                    "issue": "Record count mismatch",
                    "sqlite_count": len(rows),
                    "csv_count": csv_count,
                    "explanation": "Processed CSV contains subset (260 operational shipments) while SQLite database contains full 10,000 production records."
                })

    # Validate Employee Records
    cur.execute("SELECT count(*) FROM employees")
    emp_count = cur.fetchone()[0]
    cur.execute("SELECT count(DISTINCT employee_id) FROM employees")
    distinct_emp = cur.fetchone()[0]
    cur.execute("SELECT * FROM employees WHERE email IS NULL OR email = ''")
    missing_emp_email = len(cur.fetchall())

    report["summary"]["employee_table"] = {
        "total_records": emp_count,
        "unique_ids": distinct_emp,
        "missing_email_records": missing_emp_email,
        "status": "Healthy" if emp_count == distinct_emp and missing_emp_email == 0 else "Anomalies detected"
    }

    # Validate Hubs Records
    cur.execute("SELECT count(*) FROM hubs")
    hubs_count = cur.fetchone()[0]
    report["summary"]["hubs_table"] = {
        "total_records": hubs_count,
        "status": "Healthy" if hubs_count >= 10 else "Review needed"
    }

    # Summary numbers
    report["valid_records_count"] = valid_count
    report["invalid_records_count"] = invalid_count
    report["records_with_warnings"] = warning_count
    report["summary"]["data_integrity_score_pct"] = round((valid_count / max(1, len(rows))) * 100, 2)

    # Proposed Corrections Report (Read-only, no destructive updates)
    if report["issues_by_category"]["business_rule_violations"]:
        for br in report["issues_by_category"]["business_rule_violations"][:10]:
            report["proposed_corrections"].append({
                "target_table": "shipments",
                "shipment_id": br.get("shipment_id"),
                "proposed_action": "Set delay_reason to 'Carrier operational congestion' where missing on delayed status",
                "status": "PENDING_APPROVAL"
            })

    conn.close()

    # Save validation report
    out_file = REPORTS_DIR / "data_validation_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Data validation complete. Checked {report['total_records_checked']} records.")
    print(f"Valid: {valid_count} | Invalid: {invalid_count} | Warnings: {warning_count}")
    print(f"Integrity Score: {report['summary']['data_integrity_score_pct']}%")
    print(f"Report written to: {out_file}")

    return report


if __name__ == "__main__":
    validate_shipment_dataset()
