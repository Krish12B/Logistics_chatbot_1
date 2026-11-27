"""Playwright end-to-end browser tests for FleetHarbor Logistics AI Chatbot Web UI.

Tests:
  - Application loads cleanly with zero console/page errors
  - Message submission & API communication (/chat/stream)
  - Empty message validation in UI
  - History sidebar updates, search filter, click re-ask, delete
  - New Chat resets dialogue & sessionId while preserving Question History
  - Duplicate submission prevention while request is in flight
  - Captures real screenshots of test execution into tests/reports/screenshots/
"""
from __future__ import annotations

import socket
import threading
import time
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import uvicorn

SCREENSHOT_DIR = Path(__file__).resolve().parents[2] / "reports" / "screenshots"


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def live_server_url():
    """Run FastAPI app in a background thread on a free localhost port for Playwright tests."""
    from logistics_chatbot.main import app

    port = _get_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 15.0
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base_url}/health", timeout=1.0)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.2)
    else:
        server.should_exit = True
        pytest.fail("Live test server failed to start within 15s")

    yield base_url

    server.should_exit = True
    thread.join(timeout=5.0)


@pytest.fixture(scope="module")
def browser_instance():
    """Launch headless Edge (or Chromium fallback) via Playwright."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="msedge", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


class TestWebUIPlaywright:
    def test_frontend_load_send_history_new_chat_and_screenshots(self, live_server_url, browser_instance):
        """TC-UI-01..06: Full Playwright browser walkthrough with screenshots & console audit."""
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        context = browser_instance.new_context(viewport={"width": 1280, "height": 860})
        page = context.new_page()

        console_errors = []
        page_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        try:
            # 1. Verify application loads cleanly
            page.goto(live_server_url, wait_until="domcontentloaded", timeout=15000)
            assert "FleetHarbor AI" in page.title()
            page.wait_for_selector("#userInput", state="visible")
            page.wait_for_selector("#sendBtn", state="visible")
            page.wait_for_selector("#historySidebar", state="visible")
            page.screenshot(path=str(SCREENSHOT_DIR / "01_landing_page.png"), full_page=False)

            # Clear localStorage to start deterministic UI state
            page.evaluate("localStorage.clear(); renderHistoryList();")

            # 2. Verify empty submission is ignored cleanly (doesn't add empty user bubble)
            page.fill("#userInput", "   ")
            page.click("#sendBtn")
            user_msgs = page.locator(".msg.user").count()
            assert user_msgs == 0

            # 3. Send a shipment tracking message & verify API communication
            with page.expect_response(lambda r: "/chat" in r.url and r.request.method == "POST", timeout=10000) as resp_info:
                page.fill("#userInput", "Track SHP-10001")
                page.click("#sendBtn")
            api_resp = resp_info.value
            assert api_resp.status == 200

            page.wait_for_selector(".msg.bot >> text=SHP-10001", timeout=10000)
            assert page.locator("#historyCountBadge").inner_text() == "1"
            assert "Track SHP-10001" in page.locator("#historyList").inner_text()
            page.screenshot(path=str(SCREENSHOT_DIR / "02_shipment_response.png"), full_page=False)

            # 4. Send a second message & test history search
            with page.expect_response(lambda r: "/chat" in r.url and r.request.method == "POST", timeout=10000):
                page.fill("#userInput", "What is customs clearance?")
                page.click("#sendBtn")
            page.wait_for_selector(".msg.bot >> text=Customs Clearance", timeout=10000)
            assert page.locator("#historyCountBadge").inner_text() == "2"

            page.fill("#historySearchInput", "SHP-10001")
            assert page.locator(".history-item").count() == 1
            page.fill("#historySearchInput", "")
            assert page.locator(".history-item").count() == 2

            # 5. Test New Chat resets dialogue & sessionId while preserving Question History
            old_session_id = page.evaluate("sessionId")
            page.click("#newChatBtn")
            new_session_id = page.evaluate("sessionId")
            assert new_session_id != old_session_id
            assert page.locator(".msg.user").count() == 0
            assert "New Dialogue Started" in page.locator("#chatMessages").inner_text()
            assert page.locator("#historyCountBadge").inner_text() == "2"
            page.screenshot(path=str(SCREENSHOT_DIR / "03_new_chat_session.png"), full_page=False)

            # 6. Verify nonexistent shipment error handling in UI doesn't crash or show stack trace
            with page.expect_response(lambda r: "/chat" in r.url and r.request.method == "POST", timeout=10000) as nf_resp:
                page.fill("#userInput", "Track SHP-99999")
                page.click("#sendBtn")
            assert nf_resp.value.status == 200
            page.wait_for_selector(".msg.bot >> text=SHP-99999", timeout=10000)
            page.screenshot(path=str(SCREENSHOT_DIR / "04_not_found_handled.png"), full_page=False)

            # 7. Verify XSS script payload is safely escaped and New Chat clears typed input
            page.evaluate("window.__xssTriggered = false;")
            page.fill("#userInput", "<script>window.__xssTriggered=true;</script> Track SHP-10001")
            page.click("#sendBtn")
            page.wait_for_selector(".msg.bot >> text=Mumbai, India", timeout=10000)
            assert page.evaluate("window.__xssTriggered") is False

            page.fill("#userInput", "unsent draft")
            page.click("#newChatBtn")
            assert page.input_value("#userInput") == ""
            assert page.locator(".attach-chip").count() == 0

            # 8. Verify client-side length guard prevents oversized requests & displays clean notice
            too_long = "A" * 2100
            page.fill("#userInput", too_long)
            page.click("#sendBtn")
            page.wait_for_selector(".msg.bot >> text=2000 characters", timeout=5000)
            assert page_errors == [], f"Uncaught page errors: {page_errors}"
            assert console_errors == [], f"Browser console errors: {console_errors}"

            # 9. Verify failed /chat/stream HTTP error does NOT trigger a duplicate POST /chat call
            chat_requests = []
            page.on("request", lambda req: chat_requests.append(req.url) if "/chat" in req.url else None)
            page.route("**/chat/stream", lambda route: route.fulfill(
                status=500,
                content_type="application/json",
                body='{"success": false, "message": "Simulated upstream failure", "data": null}'
            ))
            page.fill("#userInput", "Check logistics policy fallback")
            page.click("#sendBtn")
            page.wait_for_selector(".msg.bot >> text=Simulated upstream failure", timeout=5000)
            assert len(chat_requests) == 1, f"Expected single /chat/stream call on HTTP 500 error, got {chat_requests}"
            page.unroute("**/chat/stream")
            page.screenshot(path=str(SCREENSHOT_DIR / "05_validation_and_xss_safe.png"), full_page=False)
        finally:
            context.close()
