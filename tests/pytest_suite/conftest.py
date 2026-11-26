"""Shared pytest fixtures for the FleetHarbor / NexusFreight Logistics AI Chatbot test suite."""
from __future__ import annotations

import shutil
import sys
import uuid
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root and src/ are in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def test_client():
    """Create a FastAPI TestClient for the main application."""
    from fastapi.testclient import TestClient
    from api.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def clean_sessions():
    """Clear in-memory conversation sessions before/after a test for strict isolation."""
    from logistics_chatbot.chatbot.chatbot import get_conversation_store

    store = get_conversation_store()
    for sid in list(store.list_sessions()):
        store.delete(sid)
    yield store
    for sid in list(store.list_sessions()):
        store.delete(sid)


@pytest.fixture
def sample_shipment() -> Dict[str, Any]:
    return {
        "shipment_id": "SHP-10001",
        "status": "In Transit",
        "origin": "Mumbai, India",
        "destination": "London, UK",
        "current_location": "Dubai Hub, UAE",
        "estimated_delivery": "2026-11-20",
        "last_updated": "2026-11-15 18:30",
        "route": "Mumbai Hub -> Dubai Hub -> London Heathrow Hub",
        "delay_reason": None,
        "customs_status": "Not yet required",
    }


@pytest.fixture
def sample_shipment_delayed() -> Dict[str, Any]:
    return {
        "shipment_id": "SHP-10002",
        "status": "Delayed",
        "origin": "Chennai, India",
        "destination": "Dubai, UAE",
        "current_location": "Jebel Ali Port, UAE",
        "estimated_delivery": "2026-11-19",
        "last_updated": "2026-11-16 08:00",
        "route": "Chennai Port -> Jebel Ali Port",
        "delay_reason": "Port congestion at Jebel Ali",
        "customs_status": "Cleared",
    }


@pytest.fixture
def sample_shipment_customs_hold() -> Dict[str, Any]:
    return {
        "shipment_id": "SHP-10003",
        "status": "On Hold - Customs",
        "origin": "Delhi, India",
        "destination": "New York, USA",
        "current_location": "JFK Airport, USA",
        "estimated_delivery": "2026-11-22",
        "last_updated": "2026-11-15 12:10",
        "route": "Delhi Hub -> Frankfurt Hub -> JFK Airport",
        "delay_reason": "Customs hold",
        "customs_status": "Held - awaiting commercial invoice",
    }


@pytest.fixture
def sample_employee() -> Dict[str, Any]:
    return {
        "employee_id": "EMP-20001",
        "full_name": "Stella Davis",
        "department": "Flight Operations & Airfreight",
        "job_title": "Airfreight Capacity Planner",
        "assigned_hub": "Tokyo Narita Air Cargo Center (Japan)",
        "shift": "Swing Shift (14:00 - 22:30)",
        "certification": "Certified Supply Chain Professional (CSCP)",
        "email": "stella.davis@fleetharbor.com",
        "phone_extension": "x4001",
        "status": "Active",
    }


@pytest.fixture
def mock_llm_response() -> str:
    return (
        "Based on the FleetHarbor logistics knowledge base, shipments requiring customs "
        "clearance must include a signed commercial invoice, packing list, and Bill of Lading."
    )


@pytest.fixture
def mock_llm(mock_llm_response):
    """Mock Groq LLM calls so tests run deterministically without network/API dependency."""
    with patch("logistics_chatbot.chatbot.llm_client.call_llm", return_value=mock_llm_response) as m_core_llm, \
         patch("logistics_chatbot.chatbot.chatbot.call_llm", return_value=mock_llm_response) as m_bot_llm:
        yield m_bot_llm


@pytest.fixture
def isolated_chroma(tmp_path):
    """Point ChromaDB to a temporary directory for isolated tests without touching production data."""
    from logistics_chatbot.core import config
    from logistics_chatbot.vectorstores import chroma_db

    orig_dir = config.CHROMA_PERSIST_DIRECTORY
    orig_mode = config.CHROMA_MODE
    orig_col = config.CHROMA_COLLECTION_NAME

    temp_chroma = tmp_path / "chroma_isolated"
    config.CHROMA_PERSIST_DIRECTORY = temp_chroma
    config.CHROMA_MODE = "persistent"
    config.CHROMA_COLLECTION_NAME = "test_isolated_chunks"
    chroma_db.close()

    yield temp_chroma

    chroma_db.close()
    config.CHROMA_PERSIST_DIRECTORY = orig_dir
    config.CHROMA_MODE = orig_mode
    config.CHROMA_COLLECTION_NAME = orig_col
    shutil.rmtree(temp_chroma, ignore_errors=True)


@pytest.fixture
def sample_txt_content() -> bytes:
    return (
        b"FleetHarbor Standard Operating Procedure: Cold Chain Cargo\n\n"
        b"All temperature-sensitive pharmaceutical shipments must maintain 2 to 8 degrees Celsius.\n\n"
        b"IoT temperature telemetry sensors are mandatory across all cold-chain corridors (CC-POL-9921).\n"
    )


@pytest.fixture
def sample_csv_content() -> bytes:
    return (
        b"doc_id,category,section_title,content,tags,last_updated\n"
        b"OPS-901,operational_case,Test Ops Case 1,Consignment moving from Surat to Ahmedabad. Status is 'in transit'.,test;surat;ahmedabad,2026-11-20\n"
        b"OPS-902,operational_case,Test Ops Case 2,Consignment moving from Mumbai to Delhi. Status is 'delayed'.,test;mumbai;delhi,2026-11-21\n"
    )


@pytest.fixture
def unique_session_id() -> str:
    return f"test-session-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def another_session_id() -> str:
    return f"test-session-alt-{uuid.uuid4().hex[:8]}"
