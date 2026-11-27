"""RAG retrieval, hybrid scoring, chunking overlap, and isolated ChromaDB tests."""
from __future__ import annotations

from unittest.mock import patch

import pytest


class TestDocumentChunkingAndOverlap:
    def test_chunk_overlap_preserved_between_adjacent_chunks(self):
        """TC-RAG-01: Adjacent chunks share trailing overlap context when overlap > 0."""
        from logistics_chatbot.application.ingestion.document_processor import split_text_into_chunks

        paragraphs = [f"Paragraph {i}: FleetHarbor handles protocol {i} with rule ABC-{i:03d}." for i in range(1, 16)]
        text = "\n\n".join(paragraphs)
        chunks = split_text_into_chunks(text, chunk_size=200, overlap=60)
        assert len(chunks) >= 2
        # The tail of chunk 0 should overlap into the start of chunk 1
        tail_words = chunks[0][-50:].strip().split()[-3:]
        assert any(w in chunks[1] for w in tail_words), f"Expected overlap from {tail_words} in next chunk: {chunks[1]}"

    def test_empty_text_chunking(self):
        """TC-RAG-02: Empty input produces no chunks."""
        from logistics_chatbot.application.ingestion.document_processor import split_text_into_chunks

        assert split_text_into_chunks("") == []

    def test_process_document_metadata_contains_title_and_hash(self):
        """TC-RAG-03: Processed chunks include 'title', 'section_title', 'doc_id', and 'content_hash'."""
        from logistics_chatbot.application.ingestion.document_processor import process_document

        chunks, doc_id = process_document("guide.txt", b"Customs compliance manual.\n\nAll commercial invoices require HS codes.")
        assert doc_id.startswith("DOC-")
        assert len(chunks) >= 1
        meta = chunks[0]["metadata"]
        assert meta["title"]
        assert meta["section_title"]
        assert meta["content_hash"]


class TestHybridSearchScoringAndIsolatedChroma:
    def test_search_knowledge_uses_chroma_semantic_score(self):
        """TC-RAG-04: hybrid_search.search_knowledge reads 'score' properly (semantic_score != 0)."""
        from logistics_chatbot.application.rag.hybrid_search import search_knowledge

        mock_raw = [{
            "chunk_id": "DOC-1_0",
            "doc_id": "DOC-1",
            "section_title": "Cold Chain Policy",
            "content": "Pharmaceutical shipments maintain 2C to 8C temperature control CC-POL-9921.",
            "score": 0.92,
            "category": "cold_chain",
        }]
        with patch("logistics_chatbot.application.rag.hybrid_search.embed_query", return_value=[0.1] * 384), \
             patch("logistics_chatbot.infrastructure.vector_store.chroma_store.query_knowledge_chunks", return_value=mock_raw):
            res = search_knowledge("cold chain temperature CC-POL-9921", top_k=3)

        assert len(res) == 1
        assert res[0]["semantic_score"] == 0.92
        assert res[0]["similarity_score"] > 0.7

    def test_isolated_chromadb_index_and_retrieve(self, isolated_chroma):
        """TC-RAG-05: Isolated temporary ChromaDB upserts uploaded document chunks and retrieves them cleanly."""
        from logistics_chatbot.application.ingestion.document_processor import process_document
        from logistics_chatbot.application.rag.hybrid_search import index_document_chunks
        from logistics_chatbot.infrastructure.vector_store import chroma_store as chroma_db

        content = b"Nuclear isotopes require Class 7 placards and Radiation Safety Officer approval RSO-778."
        chunks, doc_id = process_document("class7_rad.txt", content)
        fake_vec = [0.25] * 384

        with patch("logistics_chatbot.application.rag.hybrid_search.embed_texts", return_value=[fake_vec] * len(chunks)):
            count = index_document_chunks(chunks)
        assert count == len(chunks)

        with patch("logistics_chatbot.infrastructure.embeddings.sentence_transformer.embed_query", return_value=fake_vec):
            matches = chroma_db.query_knowledge_chunks("Class 7 RSO-778", top_k=2, min_score=0.2)
        assert len(matches) >= 1
        assert matches[0]["doc_id"] == doc_id
        assert matches[0]["section_title"]  # verifies title mapping works!
        assert "RSO-778" in matches[0]["content"]
