"""
Comprehensive live audit script for testing http://127.0.0.1:8000 across all endpoints.
"""
import urllib.request
import urllib.error
import json
import io

BASE_URL = "http://127.0.0.1:8000"
ERRORS = []
PASSES = []

def record_pass(test_name, details=""):
    PASSES.append(f"✅ {test_name}: {details}")
    print(f"PASS: {test_name} {details}")

def record_fail(test_name, details=""):
    ERRORS.append(f"❌ {test_name}: {details}")
    print(f"FAIL: {test_name} {details}")

def make_request(path, method="GET", data=None, headers=None):
    url = f"{BASE_URL}{path}"
    h = headers or {}
    body = None
    if data is not None:
        if isinstance(data, dict):
            body = json.dumps(data).encode("utf-8")
            if "Content-Type" not in h:
                h["Content-Type"] = "application/json"
        elif isinstance(data, bytes):
            body = data

    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            return resp.status, resp.headers, content
    except urllib.error.HTTPError as e:
        content = e.read()
        return e.code, e.headers, content
    except Exception as e:
        return 0, {}, str(e).encode("utf-8")

print("=" * 70)
print(f"AUDITING LIVE FASTAPI SERVER AT {BASE_URL}")
print("=" * 70)

# 1. Root / GET HTML
code, headers, body = make_request("/", headers={"Accept": "text/html"})
if code == 200 and b"FleetHarbor AI" in body and b"<!DOCTYPE html>" in body:
    record_pass("GET / (Web UI HTML)", f"Status {code}, {len(body)} bytes")
else:
    record_fail("GET / (Web UI HTML)", f"Status {code}, Body preview: {body[:200]}")

# 2. Root / GET JSON
code, headers, body = make_request("/", headers={"Accept": "application/json"})
if code == 200:
    try:
        j = json.loads(body.decode("utf-8"))
        if j.get("success") is True:
            record_pass("GET / (JSON API)", f"Status {code}, message: {j.get('message')}")
        else:
            record_fail("GET / (JSON API)", f"Invalid envelope: {j}")
    except Exception as e:
        record_fail("GET / (JSON API)", f"JSON parse error: {e}")
else:
    record_fail("GET / (JSON API)", f"Status {code}")

# 3. GET /health
code, headers, body = make_request("/health")
if code == 200 and b"Logistics AI Chatbot API is running" in body:
    record_pass("GET /health", f"Status {code}")
else:
    record_fail("GET /health", f"Status {code}, Body: {body.decode(errors='ignore')}")

# 4. GET /favicon.ico
code, headers, body = make_request("/favicon.ico")
if code == 204 or code == 200:
    record_pass("GET /favicon.ico", f"Status {code}")
else:
    record_fail("GET /favicon.ico", f"Status {code}")

# 5. GET /docs
code, headers, body = make_request("/docs")
if code == 200 and b"swagger" in body.lower():
    record_pass("GET /docs", f"Status {code}")
else:
    record_fail("GET /docs", f"Status {code}")

# 6. GET /openapi.json
code, headers, body = make_request("/openapi.json")
if code == 200:
    try:
        j = json.loads(body.decode("utf-8"))
        if "paths" in j and "/chat" in j["paths"]:
            record_pass("GET /openapi.json", f"Status {code}, {len(j['paths'])} paths defined")
        else:
            record_fail("GET /openapi.json", "Missing /chat in paths")
    except Exception as e:
        record_fail("GET /openapi.json", f"JSON parse error: {e}")
else:
    record_fail("GET /openapi.json", f"Status {code}")

# 7. GET /shipment/SHP-10001
code, headers, body = make_request("/shipment/SHP-10001")
if code == 200:
    try:
        j = json.loads(body.decode("utf-8"))
        if j.get("success") is True and j.get("data", {}).get("shipment_id") == "SHP-10001":
            record_pass("GET /shipment/SHP-10001", f"Found status: {j['data'].get('status')}")
        else:
            record_fail("GET /shipment/SHP-10001", f"Unexpected payload: {j}")
    except Exception as e:
        record_fail("GET /shipment/SHP-10001", f"JSON error: {e}")
else:
    record_fail("GET /shipment/SHP-10001", f"Status {code}")

# 8. GET /shipment/SHP-99999 (404)
code, headers, body = make_request("/shipment/SHP-99999")
if code == 404:
    try:
        j = json.loads(body.decode("utf-8"))
        if j.get("success") is False:
            record_pass("GET /shipment/SHP-99999 (404 check)", f"Status 404, message: {j.get('message')}")
        else:
            record_fail("GET /shipment/SHP-99999 (404 check)", f"success was not False: {j}")
    except Exception as e:
        record_fail("GET /shipment/SHP-99999 (404 check)", f"JSON parse error: {e}")
else:
    record_fail("GET /shipment/SHP-99999 (404 check)", f"Expected 404, got {code}")

# 9. POST /chat queries
chat_tests = [
    ("Greeting Query", "Hello", "greeting", None),
    ("Shipment Status Query", "What is the status of SHP-10001?", "shipment_status", "SHP-10001"),
    ("Shipment Location Query", "What is the location of SHP-10005?", "shipment_location", "SHP-10005"),
    ("Direct Definition Query", "What is In Transit?", "direct_answer", None),
    ("Cold Chain Rules", "What are the pharma cold-chain rules?", "general_knowledge", None),
]

for name, q, expected_type, expected_id in chat_tests:
    code, headers, body = make_request("/chat", method="POST", data={"message": q})
    if code == 200:
        try:
            j = json.loads(body.decode("utf-8"))
            if j.get("success") is True:
                data = j.get("data", {})
                resp_text = data.get("response", "")
                sources = data.get("sources", [])
                r_type = data.get("response_type")
                sid = data.get("shipment_id")
                record_pass(f"POST /chat ({name})", f"type={r_type}, sources={len(sources)}, preview={resp_text[:60]}...")
            else:
                record_fail(f"POST /chat ({name})", f"success was not True: {j}")
        except Exception as e:
            record_fail(f"POST /chat ({name})", f"JSON parse error: {e}")
    else:
        record_fail(f"POST /chat ({name})", f"Status {code}, body: {body.decode(errors='ignore')}")

# 10. POST /chat empty message rejection (422 / 400)
code, headers, body = make_request("/chat", method="POST", data={"message": "   "})
if code in (400, 422):
    record_pass("POST /chat (empty message validation)", f"Correctly rejected with HTTP {code}")
else:
    record_fail("POST /chat (empty message validation)", f"Expected 400/422, got {code}")

# 11. POST /upload-doc invalid extension rejection
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body_parts = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="invalid.pdf"\r\n'
    f"Content-Type: application/pdf\r\n\r\n"
    f"%PDF-1.4 mock pdf content\r\n"
    f"--{boundary}--\r\n"
).encode("utf-8")

code, headers, body = make_request(
    "/upload-doc",
    method="POST",
    data=body_parts,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
)
if code == 400:
    record_pass("POST /upload-doc (PDF rejection)", "Correctly rejected non-txt file with HTTP 400")
else:
    record_fail("POST /upload-doc (PDF rejection)", f"Expected 400, got {code}: {body.decode(errors='ignore')}")

print("\n" + "=" * 70)
print(f"AUDIT SUMMARY: {len(PASSES)} Passed, {len(ERRORS)} Failed")
print("=" * 70)
for p in PASSES:
    print(p)
for e in ERRORS:
    print(e)
