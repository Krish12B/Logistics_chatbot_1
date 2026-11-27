"""Ingestion and indexing script for all knowledge base documents into ChromaDB.
Indexes:
  - knowledge_base/company_profile_and_fleet_services.txt
  - knowledge_base/customer_rules_and_shipping_terms.txt
  - knowledge_base/employee_operations_and_warehouse_sop.txt
  - knowledge_base/customs_trade_compliance_and_crossborder_rules.txt
  - knowledge_base/pharma_cold_chain_and_gdp_manual.txt
  - knowledge_base/dangerous_goods_hazmat_and_packaging_rules.txt
  - data/knowledge_base/kb_long.csv newly augmented entries
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from logistics_chatbot.application.ingestion.document_processor import process_txt_document
from logistics_chatbot.application.rag.hybrid_search import get_chroma_collection, index_document_chunks, search_knowledge
from logistics_chatbot.infrastructure.vector_store import chroma_store as chroma_db

kb_dir = _ROOT / "data" / "knowledge_base" / "manuals"
total_indexed_chunks = 0

print("=" * 70)
print("INDEXING KNOWLEDGE BASE DOCUMENTS INTO CHROMADB VECTOR STORE")
print("=" * 70)

for txt_path in sorted(kb_dir.glob("*.txt")):
    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks, doc_id = process_txt_document(txt_path.name, text)
    print(f"File: {txt_path.name:55s} -> Doc ID: {doc_id} -> Chunks: {len(chunks)}")
    indexed = index_document_chunks(chunks)
    total_indexed_chunks += indexed

print("-" * 70)
print(f"Total chunks indexed from knowledge_base/*.txt: {total_indexed_chunks}")
coll = get_chroma_collection()
print(f"ChromaDB persistent collection count: {coll.count()}")
print("=" * 70)

# Quick semantic retrieval verification
test_queries = [
    "What are FleetHarbor core service offerings and headquarters?",
    "What is the customer claims filing procedure and compensation SLA?",
    "What are the employee forklift speed limits and safety rules?",
    "What documents are needed for customs clearance and how to resolve holds?",
    "Explain CC-POL-9921 temperature ranges for pharma and dry ice rules",
    "What are the dangerous goods classes and lithium battery air shipping rules?",
]

print("TESTING SEMANTIC SEARCH RETRIEVAL:")
for q in test_queries:
    results = search_knowledge(q, top_k=2)
    print(f"\nQuery: {q}")
    print(f"Found {len(results)} matches:")
    for r in results:
        title = r.get("metadata", {}).get("section_title") or r.get("metadata", {}).get("filename")
        score = r.get("similarity_score", 0.0)
        snippet = r.get("content", "")[:120].replace("\n", " ")
        print(f"  - [{score:.3f}] {title} | {snippet}...")
print("\nIndexing and retrieval verification completed successfully!")
