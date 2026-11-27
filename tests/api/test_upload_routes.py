"""Tests for POST /upload-doc and GET /health endpoints."""
from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fastapi.testclient import TestClient
from logistics_chatbot.main import app

client = TestClient(app)


class TestUploadEndpoint(unittest.TestCase):
    """Test suite for POST /upload-doc and GET /health."""

    def test_health_check_endpoint(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Logistics AI Chatbot API is running")

    @patch("logistics_chatbot.application.services.document_service.index_document_chunks")
    def test_valid_txt_upload_success(self, mock_index):
        mock_index.return_value = 3
        file_content = b"International Logistics Policy.\n\nAll express parcels require manifest clearance.\n\nDangerous goods are prohibited."
        response = client.post(
            "/upload-doc",
            files={"file": ("express_policy.txt", io.BytesIO(file_content), "text/plain")},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Document uploaded successfully")
        self.assertEqual(data["data"]["filename"], "express_policy.txt")
        self.assertEqual(data["data"]["chunks_created"], 3)
        self.assertEqual(data["data"]["status"], "Indexed Successfully")
        mock_index.assert_called_once()

    def test_invalid_file_extension_rejected(self):
        response = client.post(
            "/upload-doc",
            files={"file": ("report.exe", io.BytesIO(b"executable binary content"), "application/octet-stream")},
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("Unsupported file type", data["message"])

    @patch("logistics_chatbot.application.services.document_service.index_document_chunks", return_value=1)
    def test_valid_docx_upload_accepted(self, mock_index):
        import docx
        doc = docx.Document()
        doc.add_paragraph("Valid DOCX test paragraph for logistics policy.")
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        response = client.post(
            "/upload-doc",
            files={"file": ("policy.docx", buf, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["filename"], "policy.docx")
        self.assertEqual(data["data"]["status"], "Indexed Successfully")

    def test_empty_file_rejected(self):
        response = client.post(
            "/upload-doc",
            files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("empty", data["message"].lower())

    def test_whitespace_only_file_rejected(self):
        response = client.post(
            "/upload-doc",
            files={"file": ("blank.txt", io.BytesIO(b"   \n\n\t   "), "text/plain")},
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("empty", data["message"].lower())


if __name__ == "__main__":
    unittest.main()
