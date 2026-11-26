"""Conversation memory, follow-up resolution, and session isolation tests."""
from __future__ import annotations

from unittest.mock import patch

import pytest


class TestConversationMemoryAndIsolation:
    def test_shipment_multi_turn_follow_up_and_switching(self, test_client, clean_sessions, unique_session_id):
        """TC-MEM-01: Multiple questions on one shipment & switching to a second shipment."""
        # Turn 1: Ask about SHP-10001
        r1 = test_client.post("/chat", json={"message": "Track SHP-10001", "session_id": unique_session_id})
        assert r1.status_code == 200
        assert "SHP-10001" in r1.json()["data"]["response"]

        # Turn 2: Pronoun follow-up about SHP-10001
        r2 = test_client.post("/chat", json={"message": "Where is it right now?", "session_id": unique_session_id})
        assert r2.status_code == 200
        assert "SHP-10001" in r2.json()["data"]["response"]

        # Turn 3: Switch shipment to SHP-10002
        r3 = test_client.post("/chat", json={"message": "Now check SHP-10002", "session_id": unique_session_id})
        assert r3.status_code == 200
        assert "SHP-10002" in r3.json()["data"]["response"]

        # Turn 4: Pronoun follow-up should resolve to SHP-10002 (not SHP-10001)
        r4 = test_client.post("/chat", json={"message": "Where is it stuck?", "session_id": unique_session_id})
        assert r4.status_code == 200
        assert "SHP-10002" in r4.json()["data"]["response"]
        assert "SHP-10001" not in r4.json()["data"]["response"]

    def test_employee_multi_turn_follow_up(self, test_client, clean_sessions, unique_session_id, sample_employee):
        """TC-MEM-02: Follow-up pronoun ('What shift does she work?') resolves EMP-20001 deterministically."""
        with patch("chatbot.bot.database.get_employee", return_value=sample_employee):
            r1 = test_client.post("/chat", json={"message": "Look up employee EMP-20001", "session_id": unique_session_id})
            assert r1.status_code == 200
            assert "Stella Davis" in r1.json()["data"]["response"]

            r2 = test_client.post("/chat", json={"message": "What shift does she work?", "session_id": unique_session_id})
            assert r2.status_code == 200
            body2 = r2.json()["data"]
            assert body2["response_type"] == "employee_lookup"
            assert "Swing Shift" in body2["response"]
            assert "EMP-20001" in body2["response"]

    def test_session_isolation_prevents_memory_leakage(self, test_client, clean_sessions, unique_session_id, another_session_id):
        """TC-MEM-03: Context in Session A never leaks into Session B."""
        r_a = test_client.post("/chat", json={"message": "Track SHP-10001", "session_id": unique_session_id})
        assert r_a.status_code == 200
        assert "SHP-10001" in r_a.json()["data"]["response"]

        # Session B asks ambiguous "Where is it right now?" -> should ask for shipment ID, NOT resolve SHP-10001
        r_b = test_client.post("/chat", json={"message": "Where is my shipment?", "session_id": another_session_id})
        assert r_b.status_code == 200
        assert r_b.json()["data"]["response_type"] == "clarification_request"
        assert "Mumbai" not in r_b.json()["data"]["response"]

    def test_conversation_history_persistence_in_store(self, test_client, clean_sessions, unique_session_id):
        """TC-MEM-04: ConversationStore retains exact turn sequence for a session."""
        test_client.post("/chat", json={"message": "Hello", "session_id": unique_session_id})
        test_client.post("/chat", json={"message": "Track SHP-10001", "session_id": unique_session_id})
        session = clean_sessions.get(unique_session_id)
        assert session is not None
        assert session.turn_count == 2
        assert len(session.messages) == 4
