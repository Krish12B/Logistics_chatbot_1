"""Shipment database retrieval and API endpoint tests."""
from __future__ import annotations

from unittest.mock import patch

import pytest


class TestShipmentRetrieval:
    def test_valid_shipment_data_fields(self, test_client):
        """TC-SHP-01: Valid shipment SHP-10001 has all expected fields from SQLite."""
        resp = test_client.get("/shipment/SHP-10001")
        assert resp.status_code == 200
        data = resp.json()["data"]
        for field in ["shipment_id", "status", "origin", "destination", "current_location", "route", "estimated_delivery"]:
            assert field in data, f"Missing field: {field}"

    def test_multiple_valid_shipments_10k_range(self, test_client):
        """TC-SHP-02: Shipments across 10K dataset range (10001..20000) resolve cleanly."""
        for sid in ["SHP-10001", "SHP-15000", "SHP-20000"]:
            resp = test_client.get(f"/shipment/{sid}")
            assert resp.status_code == 200, f"Failed for {sid}"
            assert resp.json()["data"]["shipment_id"] == sid

    def test_shipment_case_insensitive_lookup(self, test_client):
        """TC-SHP-03: Lowercase shipment ID in path resolves properly."""
        resp = test_client.get("/shipment/shp-10001")
        assert resp.status_code == 200
        assert resp.json()["data"]["shipment_id"] == "SHP-10001"

    def test_shipment_out_of_range_returns_404(self, test_client):
        """TC-SHP-04: Out-of-range ID SHP-00001 returns 404."""
        resp = test_client.get("/shipment/SHP-00001")
        assert resp.status_code == 404
        assert resp.json()["success"] is False

    def test_search_shipments_uses_sqlite_when_no_supabase(self):
        """TC-SHP-05: search_shipments uses SQLite directly when SUPABASE_DB_URL is empty."""
        from logistics_chatbot.core import config
        from logistics_chatbot.application.rag.retriever import search_shipments

        with patch.object(config, "SUPABASE_DB_URL", ""):
            res = search_shipments(status="Delayed", limit=5)
        assert len(res.shipments) == 5
        assert res.source == "shipments_sqlite"
        assert all(s["status"].lower() == "delayed" for s in res.shipments)
