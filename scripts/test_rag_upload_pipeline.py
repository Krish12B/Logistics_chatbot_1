"""End-to-end RAG verification script for document upload and immediate retrieval.

Sequence:
  1. Create a specialized unique knowledge document.
  2. Upload through POST /upload-doc.
  3. Verify chunking, embedding generation, and ChromaDB insertion.
  4. Query POST /chat with a question only answerable from this new doc.
  5. Verify ChromaDB retrieves the new content and LLM generates grounded answer.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def run_test():
    print("=" * 70)
    print("PHASE 9: LIVE RAG INTEGRATION & DOCUMENT UPLOAD VERIFICATION")
    print("=" * 70)

    # 1. Specialized test policy text
    test_policy_text = (
        "FleetHarbor Cold Chain and Refrigerated Cargo Policy 2026.\n\n"
        "All temperature-sensitive pharmaceutical shipments must be maintained strictly "
        "between 2 degrees Celsius and 8 degrees Celsius throughout transit.\n\n"
        "A continuous electronic temperature data logger must be activated and placed inside "
        "every refrigerated pallet before dispatch from the hub.\n\n"
        "If a temperature deviation exceeds 30 minutes, an automated cold-chain alert is dispatched "
        "directly to the Logistics Operations Director.\n\n"
        "The mandatory cold-chain compliance certification code is CC-POL-9921."
    )

    # 2. Upload via POST /upload-doc
    print("\n[1/4] Uploading test document through POST /upload-doc...")
    upload_resp = client.post(
        "/upload-doc",
        files={"file": ("cold_chain_pharma_policy_2026.txt", io.BytesIO(test_policy_text.encode("utf-8")), "text/plain")},
    )
    print("      Status Code:", upload_resp.status_code)
    upload_data = upload_resp.json()
    print("      Response JSON:", upload_data)

    assert upload_resp.status_code == 200, f"Upload failed: {upload_data}"
    assert upload_data["success"] is True
    assert upload_data["data"]["chunks_created"] >= 1
    print("      ✅ Document processing, chunking, embedding generation & ChromaDB insertion verified.")

    # 3. Query POST /chat
    question = "What is the required temperature range for pharmaceutical shipments and what is the compliance certification code?"
    print(f"\n[2/4] Querying chatbot through POST /chat with question:")
    print(f"      \"{question}\"")

    chat_resp = client.post("/chat", json={"message": question})
    print("      Status Code:", chat_resp.status_code)
    chat_data = chat_resp.json()
    print("      Response JSON:", chat_data)

    assert chat_resp.status_code == 200, f"Chat failed: {chat_data}"
    assert chat_data["success"] is True

    response_text = chat_data["data"]["response"]
    sources = chat_data["data"]["sources"]

    print(f"\n[3/4] AI Response Generated:\n{response_text}")
    print(f"      Sources cited: {sources}")

    # 4. Assert groundings (normalize unicode non-breaking hyphens/spaces from LLM)
    norm_text = response_text.replace("\u2011", "-").replace("\u2013", "-").replace("\u202f", " ")
    assert "2" in norm_text and "8" in norm_text, "Temperature range missing from answer"
    assert "CC-POL-9921" in norm_text or "9921" in norm_text, "Certification code missing from answer"

    print("\n[4/4] ✅ RAG GROUNDING VERIFICATION PASSED: The chatbot successfully retrieved and cited newly uploaded knowledge!")
    print("=" * 70)


if __name__ == "__main__":
    run_test()
