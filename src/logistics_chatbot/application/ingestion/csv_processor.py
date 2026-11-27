"""CSV Data Ingestion, Schema Identification, Validation, DB Upsert & Vector Indexing."""
from __future__ import annotations

import csv
import io
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from logistics_chatbot.core.constants import VALID_EMPLOYEE_STATUSES, VALID_SHIPMENT_STATUSES
from logistics_chatbot.infrastructure.database import repository as db
from logistics_chatbot.infrastructure.embeddings.sentence_transformer import embed_texts
from logistics_chatbot.infrastructure.vector_store import chroma_store

logger = logging.getLogger("logistics_chatbot.csv_processor")


def decode_csv_bytes(content_bytes: bytes) -> str:
    """Safely decode CSV bytes using standard encodings."""
    if not content_bytes or not content_bytes.strip():
        raise ValueError("The uploaded CSV file is empty or contains only whitespace.")
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"):
        try:
            decoded = content_bytes.decode(enc)
            if decoded.strip():
                return decoded
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError("Unable to decode CSV file. Please ensure the file has a valid text encoding.")


def parse_csv_records(text: str) -> Tuple[List[Dict[str, str]], List[str]]:
    """Parse CSV text into row dicts and header names."""
    f = io.StringIO(text)
    sample = text[:4096]
    delimiter = ","
    try:
        delimiter = csv.Sniffer().sniff(sample, delimiters=",\t;|").delimiter
    except Exception:
        delimiter = ","

    f.seek(0)
    reader = csv.DictReader(f, delimiter=delimiter)
    headers = [h.strip() for h in (reader.fieldnames or []) if h]
    if not headers:
        raise ValueError("CSV file contains no valid headers.")

    rows = []
    for line_num, r in enumerate(reader, start=2):
        cleaned_row = {k.strip(): (v.strip() if v is not None else "") for k, v in r.items() if k}
        if any(cleaned_row.values()):
            cleaned_row["_row_number"] = line_num
            rows.append(cleaned_row)

    if not rows:
        raise ValueError("CSV file contains headers but no data rows.")
    return rows, headers


def identify_data_category(headers: List[str], rows: List[Dict[str, str]]) -> str:
    """Identify dataset category from column headers and sample IDs."""
    h_set = {h.lower() for h in headers}

    if "doc_id" in h_set and ("content" in h_set or "section_title" in h_set or "tags" in h_set):
        return "operational_records"

    sample_ids = [r.get("doc_id", "") or r.get("id", "") for r in rows[:5]]
    if any(re.match(r"^OPS[-\s]?\d+", sid, re.IGNORECASE) for sid in sample_ids):
        return "operational_records"

    if any(k in h_set for k in ("shipment_id", "tracking_number", "tracking_id")):
        return "shipment_records"
    if ("origin" in h_set or "origin_hub" in h_set) and ("destination" in h_set or "destination_hub" in h_set) and "status" in h_set:
        return "shipment_records"

    if "employee_id" in h_set or (("department" in h_set or "job_title" in h_set or "shift" in h_set) and ("name" in h_set or "full_name" in h_set)):
        return "employee_records"

    if ("question" in h_set and "answer" in h_set) or ("topic" in h_set and "content" in h_set):
        return "logistics_knowledge"

    return "unknown"


def extract_operational_attributes(content: str, tags: str) -> Dict[str, str]:
    """Extract operational status, route, and risk details from narrative text."""
    attrs: Dict[str, str] = {
        "status": "Active",
        "origin": "N/A",
        "destination": "N/A",
        "risk_factors": "Standard handling",
        "assigned_employee": "Operations Coordinator (Dispatch Desk)",
    }

    status_match = re.search(r"status\s+is\s+['\"]?([^'\"\.\n]+)['\"]?", content, re.IGNORECASE)
    if status_match:
        attrs["status"] = status_match.group(1).strip().title()
    elif "awaiting-pickup" in tags.lower():
        attrs["status"] = "Awaiting Pickup"
    elif "transit-delay" in tags.lower():
        attrs["status"] = "Delayed"

    route_match = re.search(r"moving\s+from\s+([A-Za-z\s]+?)\s+to\s+([A-Za-z\s]+?)(?:\.|\sand|\shas)", content, re.IGNORECASE)
    if route_match:
        attrs["origin"] = route_match.group(1).strip()
        attrs["destination"] = route_match.group(2).strip()
    else:
        tag_parts = [t.strip() for t in tags.split(";") if t.strip()]
        if len(tag_parts) >= 3:
            attrs["origin"] = tag_parts[1].title()
            attrs["destination"] = tag_parts[2].title()

    risk_match = re.search(r"risk(?:\s+to\s+check)?\s+is\s+([^.\n]+)", content, re.IGNORECASE)
    if risk_match:
        attrs["risk_factors"] = risk_match.group(1).strip().capitalize()
    else:
        for t in tags.split(";"):
            if any(k in t for k in ("risk", "exposure", "delay", "damage", "mismatch")):
                attrs["risk_factors"] = t.replace("-", " ").capitalize()
                break

    return attrs


def validate_operational_record(row: Dict[str, str]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Validate and enrich an operational record."""
    doc_id = (row.get("doc_id") or row.get("id") or "").strip().upper()
    if not doc_id:
        return False, "Missing required 'doc_id'", {}

    ops_match = re.match(r"^OPS[-\s]?(\d+)$", doc_id)
    if ops_match:
        doc_id = f"OPS-{int(ops_match.group(1)):03d}"

    content = row.get("content", "").strip()
    if not content:
        return False, f"Row {doc_id} has empty 'content'", {}

    category = row.get("category", "operational_case").strip().lower()
    section_title = row.get("section_title", f"Operational Case {doc_id}").strip()
    tags = row.get("tags", "").strip()
    last_updated = row.get("last_updated", "").strip()

    if last_updated:
        try:
            datetime.strptime(last_updated, "%Y-%m-%d")
        except ValueError:
            try:
                last_updated = datetime.strptime(last_updated, "%d-%m-%Y").strftime("%Y-%m-%d")
            except ValueError:
                last_updated = datetime.now().strftime("%Y-%m-%d")
    else:
        last_updated = datetime.now().strftime("%Y-%m-%d")

    extracted = extract_operational_attributes(content, tags)
    record = {
        "doc_id": doc_id,
        "category": category,
        "section_title": section_title,
        "content": content,
        "tags": tags,
        "status": extracted["status"],
        "origin": extracted["origin"],
        "destination": extracted["destination"],
        "risk_factors": extracted["risk_factors"],
        "assigned_employee": extracted["assigned_employee"],
        "responsible_department": category.replace("_", " ").title(),
        "last_updated": last_updated,
    }
    return True, None, record


def validate_shipment_record(row: Dict[str, str]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Validate a shipment record."""
    sid = (row.get("shipment_id") or row.get("tracking_number") or "").strip().upper()
    if not sid:
        return False, "Missing 'shipment_id'", {}

    status = (row.get("status") or "In Transit").strip()
    if status.upper() not in VALID_SHIPMENT_STATUSES:
        status = "In Transit"

    origin = (row.get("origin") or row.get("origin_hub") or "Unknown").strip()
    destination = (row.get("destination") or row.get("destination_hub") or "Unknown").strip()

    record = {
        "shipment_id": sid,
        "origin": origin,
        "destination": destination,
        "status": status,
        "current_location": row.get("current_location", origin),
        "route": row.get("route", f"{origin} -> {destination}"),
        "estimated_delivery": row.get("estimated_delivery") or row.get("expected_delivery", ""),
        "delay_reason": row.get("delay_reason", ""),
        "customs_status": row.get("customs_status", "Cleared"),
        "last_updated": row.get("last_updated", datetime.now().strftime("%Y-%m-%d")),
    }
    return True, None, record


def validate_employee_record(row: Dict[str, str]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Validate an employee record."""
    eid = (row.get("employee_id") or "").strip().upper()
    if not eid:
        return False, "Missing 'employee_id'", {}

    full_name = row.get("full_name") or f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
    if not full_name:
        full_name = f"Employee {eid}"

    status = (row.get("status") or "Active").strip()
    if status.upper() not in VALID_EMPLOYEE_STATUSES:
        status = "Active"

    record = {
        "employee_id": eid,
        "full_name": full_name,
        "department": row.get("department", "Operations"),
        "job_title": row.get("job_title") or row.get("role", "Operations Specialist"),
        "assigned_hub": row.get("assigned_hub") or row.get("hub", "DXB-HUB-01"),
        "shift": row.get("shift", "Day Shift (08:00 - 17:00)"),
        "certification": row.get("certification", "Standard Operations Certified"),
        "email": row.get("email", f"{eid.lower()}@fleetharbor.com"),
        "phone_extension": row.get("phone_extension", "x4000"),
        "status": status,
    }
    return True, None, record


def index_operational_records_in_chroma(records: List[Dict[str, Any]], filename: str) -> int:
    """Index operational records into ChromaDB as semantic knowledge chunks."""
    if not records:
        return 0

    try:
        collection = chroma_store.get_or_create_collection()
    except Exception as exc:
        logger.warning("Notice accessing ChromaDB collection: %s", exc)
        return 0

    chunk_ids, documents, metadatas = [], [], []
    for r in records:
        doc_id = r["doc_id"]
        category = r["category"]
        title = r["section_title"]
        text = (
            f"Operational Case {doc_id} ({category}): {title}\n"
            f"Status: {r.get('status', 'Active')} | Route: {r.get('origin', '')} to {r.get('destination', '')}\n"
            f"Risk: {r.get('risk_factors', '')}\n"
            f"Content: {r['content']}"
        )
        chunk_ids.append(f"{doc_id}_chunk_0")
        documents.append(text)
        metadatas.append({
            "doc_id": doc_id,
            "category": category,
            "title": title,
            "tags": r.get("tags", ""),
            "source": filename,
            "last_updated": r.get("last_updated", ""),
        })

    try:
        vectors = embed_texts(documents)
        collection.upsert(ids=chunk_ids, embeddings=vectors, documents=documents, metadatas=metadatas)
        logger.info("Indexed %d operational records into ChromaDB vector store", len(records))
        return len(records)
    except Exception as exc:
        logger.error("ChromaDB indexing error for operational records: %s", exc)
        return 0


def _validate_and_dedupe(rows: List[Dict[str, str]], validator, id_key: str):
    valid_records, validation_errors = [], []
    skipped_records, failed_records = 0, 0
    seen_ids: set[str] = set()
    for r in rows:
        valid, err, record = validator(r)
        if not valid:
            failed_records += 1
            validation_errors.append(f"Row {r.get('_row_number', '?')}: {err}")
            continue
        rec_id = record[id_key]
        if rec_id in seen_ids:
            skipped_records += 1
            continue
        seen_ids.add(rec_id)
        valid_records.append(record)
    return valid_records, skipped_records, failed_records, validation_errors


def process_csv_upload(filename: str, content_bytes: bytes) -> Dict[str, Any]:
    """Master CSV workflow: decode, parse, classify, validate, upsert DB, and index ChromaDB."""
    decoded_text = decode_csv_bytes(content_bytes)
    rows, headers = parse_csv_records(decoded_text)
    total_records = len(rows)
    data_category = identify_data_category(headers, rows)
    logger.info("Uploaded CSV '%s' identified as category: %s (Total rows: %d)", filename, data_category, total_records)

    skipped_records = 0
    failed_records = 0
    validation_errors: List[str] = []

    if data_category == "operational_records":
        valid_records, skipped_records, failed_records, validation_errors = _validate_and_dedupe(
            rows, validate_operational_record, "doc_id"
        )
        db_res = db.upsert_operational_records(valid_records)
        imported_count = db_res.get("imported", 0)
        failed_records += db_res.get("failed", 0)
        chroma_count = index_operational_records_in_chroma(valid_records, filename)
        category_display = "Operational Records (OPS-Cases)"
        db_display = "SQLite (operational_records) & Supabase"
        kb_display = f"Indexed {chroma_count} records into ChromaDB for semantic retrieval"
    elif data_category == "shipment_records":
        valid_records, skipped_records, failed_records, validation_errors = _validate_and_dedupe(
            rows, validate_shipment_record, "shipment_id"
        )
        db_res = db.upsert_shipment_records(valid_records)
        imported_count = db_res.get("imported", 0)
        failed_records += db_res.get("failed", 0)
        chroma_count = 0
        category_display = "Shipment Tracking Records"
        db_display = "SQLite (shipments) & Supabase"
        kb_display = "Preserved in relational database (structured tracking)"
    elif data_category == "employee_records":
        valid_records, skipped_records, failed_records, validation_errors = _validate_and_dedupe(
            rows, validate_employee_record, "employee_id"
        )
        db_res = db.upsert_employee_records(valid_records)
        imported_count = db_res.get("imported", 0)
        failed_records += db_res.get("failed", 0)
        chroma_count = 0
        category_display = "Employee Personnel Roster"
        db_display = "SQLite (employees) & Supabase"
        kb_display = "Preserved in personnel directory"
    else:
        imported_count = total_records
        chroma_count = 0
        category_display = "General Logistics Knowledge"
        db_display = "Relational Database"
        kb_display = "Processed for reference"

    summary_text = (
        f"# 📊 CSV IMPORT SUMMARY\n\n"
        f"**File:** `{filename}`\n\n"
        f"| Metric | Count |\n"
        f"|---|---|\n"
        f"| **Total Records** | {total_records} |\n"
        f"| **Successfully Imported** | **{imported_count}** |\n"
        f"| **Skipped (Duplicates)** | {skipped_records} |\n"
        f"| **Failed (Invalid)** | {failed_records} |\n\n"
        f"- **Data Category:** {category_display}\n"
        f"- **Database Storage:** {db_display}\n"
        f"- **Knowledge Base (Vector RAG):** {kb_display}\n"
    )
    if validation_errors:
        summary_text += "\n### Validation Notices\n"
        for err in validation_errors[:5]:
            summary_text += f"- {err}\n"
        if len(validation_errors) > 5:
            summary_text += f"- ...and {len(validation_errors) - 5} more notices.\n"

    return {
        "success": True,
        "message": "CSV data successfully imported and integrated",
        "summary": summary_text,
        "data": {
            "filename": filename,
            "total_records": total_records,
            "imported": imported_count,
            "skipped": skipped_records,
            "failed": failed_records,
            "category": data_category,
            "chunks_created": chroma_count,
            "status": "Imported and Indexed Successfully",
        },
    }
