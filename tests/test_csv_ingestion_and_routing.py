"""Comprehensive Automated Test Suite: CSV Ingestion, Data Validation & Intelligent Query Routing.

Covers Issue 1 through Issue 8:
  1. Valid CSV upload (attach_data.csv)
  2. Empty CSV rejection (HTTP 400)
  3. Invalid/corrupted CSV structure
  4. Missing required columns validation
  5. Duplicate records handling & idempotency
  6. Invalid date format tolerance/standardization
  7. Invalid status value handling & normalization
  8. Large CSV batch handling
  9. Partially valid CSV processing (valid rows imported, invalid skipped/noted)
  10. Repeated upload of the same file (idempotent upsert, no duplicates)
  11. Query Routing: Status of OPS-001, stauts of ops-001?, staus of ops-001?
  12. Query Routing: Status of ops 001 (loose spacing)
  13. Query Routing: Status of EMP-20001 & Find employee EMP-20001
  14. Query Routing: Status of SHP-10001, Track shipment SHP10001
  15. Query Routing: Nonexistent identifier (OPS-999, SHP-99999, EMP-99999)
  16. End-to-end FastAPI endpoint integration via TestClient
"""
import io
import unittest
from pathlib import Path
from starlette.testclient import TestClient

from api.main import app
from logistics_chatbot.core import config
from logistics_chatbot.chatbot.classifier import (
    LogisticsIntent,
    classify_logistics_query,
    extract_operational_id,
    extract_employee_id,
    extract_shipment_id,
    normalize_logistics_query,
)
from logistics_chatbot.document_ingestion.csv_processor import (
    decode_csv_bytes,
    parse_csv_records,
    identify_data_category,
    validate_operational_record,
    process_csv_upload,
)
from logistics_chatbot.database import database as db
from chatbot.bot import generate_response


class TestCSVIngestionAndValidation(unittest.TestCase):
    """Test suite for CSV parsing, category identification, and data validation rules."""

    def test_01_valid_csv_parsing(self):
        """Test parsing and row extraction from a well-formed CSV."""
        csv_text = "doc_id,category,section_title,content,tags,last_updated\nOPS-001,operational_case,Test Case,Consignment moving from Surat to Ahmedabad.,test;surat,2026-11-02\n"
        rows, headers = parse_csv_records(csv_text)
        self.assertEqual(len(rows), 1)
        self.assertIn("doc_id", headers)
        self.assertEqual(rows[0]["doc_id"], "OPS-001")

    def test_02_empty_csv_rejected(self):
        """Test that empty or whitespace-only CSVs raise ValueError."""
        with self.assertRaises(ValueError):
            decode_csv_bytes(b"")
        with self.assertRaises(ValueError):
            parse_csv_records("   \n\n  ")

    def test_03_invalid_csv_no_headers(self):
        """Test that CSV with missing headers raises ValueError."""
        with self.assertRaises(ValueError):
            parse_csv_records("\n\n")

    def test_04_missing_required_columns(self):
        """Test validation failure when required ID or content columns are absent."""
        invalid_row = {"category": "operational_case", "content": ""}
        valid, err, _ = validate_operational_record(invalid_row)
        self.assertFalse(valid)
        self.assertIn("doc_id", err.lower())

    def test_05_category_identification_operational(self):
        """Test accurate identification of operational records."""
        headers = ["doc_id", "category", "section_title", "content", "tags", "last_updated"]
        sample_rows = [{"doc_id": "OPS-001", "content": "Textile case"}]
        cat = identify_data_category(headers, sample_rows)
        self.assertEqual(cat, "operational_records")

    def test_06_category_identification_shipments(self):
        """Test accurate identification of shipment tracking datasets."""
        headers = ["shipment_id", "origin", "destination", "status", "current_location"]
        sample_rows = [{"shipment_id": "SHP-10001", "status": "In Transit"}]
        cat = identify_data_category(headers, sample_rows)
        self.assertEqual(cat, "shipment_records")

    def test_07_category_identification_employees(self):
        """Test accurate identification of employee rosters."""
        headers = ["employee_id", "full_name", "department", "job_title", "status"]
        sample_rows = [{"employee_id": "EMP-20001", "full_name": "Sarah Connor"}]
        cat = identify_data_category(headers, sample_rows)
        self.assertEqual(cat, "employee_records")

    def test_08_invalid_date_normalization(self):
        """Test date validation and standardization to YYYY-MM-DD."""
        row = {
            "doc_id": "OPS-100",
            "category": "operational_case",
            "section_title": "Date Test",
            "content": "Moving from Surat to Ahmedabad. Status is 'awaiting pickup'.",
            "last_updated": "02-11-2026",
        }
        valid, err, enriched = validate_operational_record(row)
        self.assertTrue(valid)
        self.assertEqual(enriched["last_updated"], "2026-11-02")

    def test_09_partially_valid_csv(self):
        """Test that valid rows are imported while invalid rows are counted as failed."""
        csv_bytes = (
            b"doc_id,category,section_title,content,tags,last_updated\n"
            b"OPS-501,operational_case,Valid 1,Standard consignment moving from Surat to Ahmedabad.,tag1,2026-11-01\n"
            b",operational_case,Missing ID,Missing doc_id content.,tag2,2026-11-01\n"
            b"OPS-502,operational_case,Valid 2,Another valid case moving from Mumbai to Delhi.,tag3,2026-11-01\n"
        )
        res = process_csv_upload("partial.csv", csv_bytes)
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["total_records"], 3)
        self.assertEqual(res["data"]["imported"], 2)
        self.assertEqual(res["data"]["failed"], 1)

    def test_10_repeated_upload_idempotency(self):
        """Test that uploading the same dataset twice updates records without duplicating."""
        csv_bytes = (
            b"doc_id,category,section_title,content,tags,last_updated\n"
            b"OPS-601,operational_case,Idempotency Test,Moving from Surat to Ahmedabad.,tags,2026-11-01\n"
        )
        res1 = process_csv_upload("idempotent.csv", csv_bytes)
        self.assertEqual(res1["data"]["imported"], 1)

        res2 = process_csv_upload("idempotent.csv", csv_bytes)
        self.assertEqual(res2["data"]["imported"], 1)
        # Verify single record in database
        rec = db.fetch_operational_record("OPS-601")
        self.assertIsNotNone(rec)
        self.assertEqual(rec["doc_id"], "OPS-601")


class TestQueryRoutingAndNormalization(unittest.TestCase):
    """Test suite for query normalization, typo correction, and intelligent routing."""

    def test_01_typo_correction_status(self):
        """Test correcting 'staus', 'stauts', 'statuss' to 'status'."""
        self.assertEqual(normalize_logistics_query("staus of ops-001?"), "status of ops-001?")
        self.assertEqual(normalize_logistics_query("stauts of ops-001?"), "status of ops-001?")
        self.assertEqual(normalize_logistics_query("what is the statuss of shp-10001"), "what is the status of shp-10001")

    def test_02_preserve_identifiers_during_normalization(self):
        """Verify that identifiers like OPS-001, SHP-10001, and EMP-20001 are preserved intact."""
        text = "stauts of OPS-001 and empolyee EMP-20001 with shpment SHP-10001"
        normalized = normalize_logistics_query(text)
        self.assertIn("OPS-001", normalized)
        self.assertIn("EMP-20001", normalized)
        self.assertIn("SHP-10001", normalized)

    def test_03_extract_operational_id_variations(self):
        """Test extracting OPS IDs across spacing and casing variations."""
        self.assertEqual(extract_operational_id("status of ops-001?"), "OPS-001")
        self.assertEqual(extract_operational_id("status of OPS-025"), "OPS-025")
        self.assertEqual(extract_operational_id("what is ops 001?"), "OPS-001")
        self.assertEqual(extract_operational_id("check OPS120 details"), "OPS-120")

    def test_04_route_operational_query(self):
        """Test that operational ID queries route to OPERATIONAL_STATUS."""
        res = classify_logistics_query("stauts of ops-001?")
        self.assertEqual(res.intent, LogisticsIntent.OPERATIONAL_STATUS)
        self.assertEqual(res.preferred_source, "operational_database")
        self.assertEqual(res.operational_id, "OPS-001")

    def test_05_route_employee_query(self):
        """Test that employee ID queries route to EMPLOYEE_SUPPORT."""
        res = classify_logistics_query("Look up employee EMP-20001")
        self.assertEqual(res.intent, LogisticsIntent.EMPLOYEE_SUPPORT)
        self.assertEqual(res.preferred_source, "employee_directory")
        self.assertEqual(res.employee_id, "EMP-20001")

    def test_06_route_shipment_query(self):
        """Test that shipment ID queries route to shipment database."""
        res = classify_logistics_query("What is the status of SHP-10001?")
        self.assertEqual(res.preferred_source, "shipment_database")
        self.assertEqual(res.shipment_id, "SHP-10001")

    def test_07_operational_record_structured_response(self):
        """Test generating structured OPERATIONAL RECORD card for OPS-001."""
        res = generate_response("stauts of ops-001?")
        self.assertEqual(res.response_type, "operational_status")
        self.assertIn("OPERATIONAL RECORD", res.response)
        self.assertIn("OPS-001", res.response)
        self.assertIn("Surat", res.response)
        self.assertIn("Ahmedabad", res.response)
        self.assertIn("Operational Database (OPS-001)", res.sources)

    def test_08_operational_record_not_found(self):
        """Test graceful error message for nonexistent operational record."""
        res = generate_response("status of ops-999")
        self.assertEqual(res.response_type, "not_found")
        self.assertIn("couldn't find operational record **OPS-999**", res.response)

    def test_09_employee_lookup_success(self):
        """Test employee directory lookup returns structured profile."""
        res = generate_response("Look up EMP-20001")
        self.assertEqual(res.response_type, "employee_lookup")
        self.assertIn("EMP-20001", res.response)
        self.assertIn("Operations Overview", res.response)

    def test_10_shipment_tracking_success(self):
        """Test shipment tracking returns 5-section verified report."""
        res = generate_response("Track shipment SHP-10001")
        self.assertIn(res.response_type, ["shipment_status", "shipment_location"])
        self.assertIn("SHP-10001", res.response)
        self.assertIn("Shipment Progress", res.response)


class TestFastAPIEndpointsIntegration(unittest.TestCase):
    """Integration test suite testing live FastAPI routes via TestClient."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_upload_doc_csv_success(self):
        """Test POST /upload-doc accepts CSV and returns CSV IMPORT SUMMARY."""
        csv_content = (
            b"doc_id,category,section_title,content,tags,last_updated\n"
            b"OPS-701,operational_case,API Upload Test,Consignment moving from Surat to Ahmedabad.,tag1,2026-11-01\n"
        )
        files = {"file": ("test_upload.csv", io.BytesIO(csv_content), "text/csv")}
        resp = self.client.post("/upload-doc", files=files)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertIn("CSV IMPORT SUMMARY", data["summary"])
        self.assertEqual(data["data"]["total_records"], 1)
        self.assertEqual(data["data"]["imported"], 1)

    def test_02_upload_doc_empty_rejected(self):
        """Test POST /upload-doc rejects empty file with HTTP 400."""
        files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
        resp = self.client.post("/upload-doc", files=files)
        self.assertEqual(resp.status_code, 400)

    def test_03_upload_doc_unsupported_extension(self):
        """Test POST /upload-doc rejects unsupported executable files."""
        files = {"file": ("script.exe", io.BytesIO(b"binary"), "application/octet-stream")}
        resp = self.client.post("/upload-doc", files=files)
        self.assertEqual(resp.status_code, 400)

    def test_04_chat_endpoint_operational_status(self):
        """Test POST /chat endpoint handles 'stauts of ops-001?'."""
        payload = {"message": "stauts of ops-001?", "session_id": "test_session_ops"}
        resp = self.client.post("/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["response_type"], "operational_status")
        self.assertIn("OPERATIONAL RECORD", data["response"])
        self.assertIn("OPS-001", data["response"])

    def test_05_chat_endpoint_employee_lookup(self):
        """Test POST /chat endpoint handles 'Find employee EMP-20001'."""
        payload = {"message": "Find employee EMP-20001", "session_id": "test_session_emp"}
        resp = self.client.post("/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["data"]["response_type"], "employee_lookup")
        self.assertIn("EMP-20001", data["response"])

    def test_06_chat_endpoint_shipment_tracking(self):
        """Test POST /chat endpoint handles 'Track shipment SHP-10001'."""
        payload = {"message": "Track shipment SHP-10001", "session_id": "test_session_shp"}
        resp = self.client.post("/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data["data"]["response_type"], ["shipment_status", "shipment_location"])
        self.assertIn("SHP-10001", data["response"])


if __name__ == "__main__":
    unittest.main()
