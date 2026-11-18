"""Tests for Supabase PostgreSQL connection and query handling.

Verifies:
  - Connection failure handling (unreachable host, invalid credentials, missing env var)
  - Schema inspection query execution
  - Real database connectivity and query execution when SUPABASE_DB_URL is configured
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import psycopg2

from logistics_chatbot.core import config
from logistics_chatbot.database import database
from logistics_chatbot.core.errors import DatabaseError, ShipmentNotFoundError


class SupabaseConnectionFailureTests(unittest.TestCase):
    """Test connection failure and error mapping."""

    def setUp(self):
        database._connection = None

    def tearDown(self):
        database.close()

    def test_missing_db_url_raises_database_error(self):
        """When SUPABASE_DB_URL is empty, DatabaseError is raised with clear explanation."""
        with patch.object(config, "SUPABASE_DB_URL", ""):
            with self.assertRaises(DatabaseError) as ctx:
                database.init_database()
            self.assertIn("SUPABASE_DB_URL is not set", ctx.exception.detail)

    def test_unreachable_host_raises_database_error(self):
        """When the host is unreachable, OperationalError is wrapped as DatabaseError."""
        bad_url = "postgresql://invalid_user:bad_password@127.0.0.1:1/nonexistent?connect_timeout=1"
        with patch.object(config, "SUPABASE_DB_URL", bad_url):
            with self.assertRaises(DatabaseError) as ctx:
                database._get_connection()
            self.assertIn("Cannot connect to Supabase PostgreSQL", ctx.exception.detail)

    def test_invalid_credentials_handling(self):
        """Authentication failures raise DatabaseError with user-safe message."""
        bad_url = "postgresql://wrong_user:wrong_pass@127.0.0.1:5432/wrong_db?connect_timeout=1"
        with patch.object(config, "SUPABASE_DB_URL", bad_url):
            with self.assertRaises(DatabaseError) as ctx:
                database._get_connection()
            self.assertEqual(
                ctx.exception.user_message,
                "I can't reach our shipment database right now. Please try again shortly."
            )

    def test_query_failure_is_mapped_to_database_error(self):
        """Database exceptions during queries become DatabaseError."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.DatabaseError("syntax error")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch.object(database, "_get_connection", return_value=mock_conn):
            with self.assertRaises(DatabaseError):
                database.run_query("SELECT bad syntax")


class SupabaseMockSchemaVerificationTests(unittest.TestCase):
    """Test schema verification logic using mocked query responses."""

    def test_all_objects_present_passes(self):
        """When shipments, knowledge_base, and match_knowledge exist, init succeeds."""
        mock_row = {
            "shipments_table": True,
            "knowledge_table": True,
            "match_function": True,
        }
        with patch.object(database, "run_query", return_value=[mock_row]):
            # Should not raise
            database.init_database()

    def test_missing_shipments_table_reports_error(self):
        """Missing shipments table is named in the error detail."""
        mock_row = {
            "shipments_table": False,
            "knowledge_table": True,
            "match_function": True,
        }
        with patch.object(database, "run_query", return_value=[mock_row]):
            with self.assertRaises(DatabaseError) as ctx:
                database.init_database()
            self.assertIn("shipments table", ctx.exception.detail)

    def test_missing_knowledge_and_function_reports_both(self):
        """All missing components are listed."""
        mock_row = {
            "shipments_table": True,
            "knowledge_table": False,
            "match_function": False,
        }
        with patch.object(database, "run_query", return_value=[mock_row]):
            with self.assertRaises(DatabaseError) as ctx:
                database.init_database()
            self.assertIn("knowledge_base table", ctx.exception.detail)
            self.assertIn("match_knowledge function", ctx.exception.detail)


class SupabaseLiveConnectionTests(unittest.TestCase):
    """Integration test against live Supabase instance."""

    def setUp(self):
        if not config.SUPABASE_DB_URL or "aws-0-" not in config.SUPABASE_DB_URL:
            self.skipTest("SUPABASE_DB_URL is not set to a live Supabase connection string")
        database._connection = None

    def tearDown(self):
        database.close()

    def test_live_supabase_ping(self):
        """Verify live database connectivity and ping."""
        conn = database._get_connection()
        self.assertIsNotNone(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ping")
            row = cur.fetchone()
            self.assertEqual(row["ping"], 1)

    def test_live_table_accessibility(self):
        """Verify shipments table is accessible."""
        rows = database.run_query("SELECT count(*) AS total FROM shipments")
        self.assertGreaterEqual(rows[0]["total"], 0)


if __name__ == "__main__":
    unittest.main()
