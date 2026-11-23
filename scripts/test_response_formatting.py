"""
Test script to inspect current responses for all 8 test queries.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from chatbot.bot import generate_response

test_queries = [
    ("Test 1: Greeting", "Hello"),
    ("Test 2: Shipment Status", "What is the status of SHP-10001?"),
    ("Test 3: Shipment Location", "What is the location of SHP-10005?"),
    ("Test 4: Shipment Lifecycle", "Explain the shipment lifecycle"),
    ("Test 5: Pharma Cold-Chain Rules", "What are the pharma cold-chain rules?"),
    ("Test 6: Customs Clearance Documents", "What documents are required for customs clearance?"),
    ("Test 7: Direct Definition", "What is In Transit?"),
    ("Test 8: Unavailable Information", "Tell me something unavailable in the knowledge base, like quantum computing rules in Antarctica"),
]

for label, query in test_queries:
    print("=" * 70)
    print(f"RUNNING: {label}")
    print(f"QUERY:   {query}")
    print("-" * 70)
    try:
        resp, sources = generate_response(query)
        print("RESPONSE:\n" + resp)
        print(f"\nSOURCES: {sources}")
    except Exception as e:
        print(f"ERROR: {e}")
print("=" * 70)
