"""Document upload, parsing, validation, and mocked ingestion tests (zero production mutations)."""
from __future__ import annotations

import io
from unittest.mock import patch

import pytest


class TestDocumentUploadEndpointMocked:
    def test_valid_txt_upload_indexed_mocked(self, test_client, sample_txt_content):
        """TC-DOC-01: Valid .txt upload parses chunks and calls indexer cleanly."""
        with patch("api.routes.upload.index_document_chunks", return_value=2) as m_index:
            resp = test_client.post(
                "/upload-doc",
                files={"file": ("cold_chain_policy.txt", io.BytesIO(sample_txt_content), "text/plain")},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["chunks_created"] == 2
        m_index.assert_called_once()
        chunks_arg = m_index.call_args[0][0]
        assert chunks_arg[0]["metadata"].get("title")  # compatible with chroma_db query_knowledge_chunks

    def test_valid_csv_upload_processed_mocked(self, test_client, sample_csv_content):
        """TC-DOC-02: Valid .csv upload delegates to process_csv_upload safely."""
        mock_csv_res = {
            "success": True,
            "message": "CSV data successfully imported and integrated",
            "summary": "# CSV IMPORT SUMMARY",
            "data": {
                "filename": "ops_test.csv",
                "total_records": 2,
                "imported": 2,
                "skipped": 0,
                "failed": 0,
                "category": "operational_records",
                "chunks_created": 2,
                "status": "Imported and Indexed Successfully",
            },
        }
        with patch("api.routes.upload.process_csv_upload", return_value=mock_csv_res) as m_csv:
            resp = test_client.post(
                "/upload-doc",
                files={"file": ("ops_test.csv", io.BytesIO(sample_csv_content), "text/csv")},
            )
        assert resp.status_code == 200
        assert resp.json()["data"]["imported"] == 2
        m_csv.assert_called_once()

    def test_empty_and_whitespace_files_rejected(self, test_client):
        """TC-DOC-03: Empty and whitespace-only files return 400."""
        for fname, data in [("empty.txt", b""), ("spaces.txt", b"   \n\t  ")]:
            resp = test_client.post(
                "/upload-doc",
                files={"file": (fname, io.BytesIO(data), "text/plain")},
            )
            assert resp.status_code == 400
            assert resp.json()["success"] is False

    def test_unsupported_extensions_rejected(self, test_client):
        """TC-DOC-04: Unsupported formats (.exe, .jpg, .zip) return 400."""
        for fname in ["payload.exe", "photo.jpg", "archive.zip"]:
            resp = test_client.post(
                "/upload-doc",
                files={"file": (fname, io.BytesIO(b"binarydata"), "application/octet-stream")},
            )
            assert resp.status_code == 400
            assert "Unsupported file type" in resp.json()["message"]

    def test_oversized_file_rejected_413(self, test_client):
        """TC-DOC-05: File > 10MB returns HTTP 413."""
        big_content = b"A" * (11 * 1024 * 1024)
        resp = test_client.post(
            "/upload-doc",
            files={"file": ("huge.txt", io.BytesIO(big_content), "text/plain")},
        )
        assert resp.status_code == 413

    def test_invalid_pdf_rejected_400(self, test_client):
        """TC-DOC-06: Corrupted PDF file returns 400 validation error."""
        resp = test_client.post(
            "/upload-doc",
            files={"file": ("corrupt.pdf", io.BytesIO(b"NOT_A_REAL_PDF_FILE"), "application/pdf")},
        )
        assert resp.status_code == 400
        assert resp.json()["success"] is False
