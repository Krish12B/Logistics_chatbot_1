"""ChromaDB Vector Database connector (Persistent, HTTP, and Cloud modes)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.api import ClientAPI
from chromadb.config import Settings

from logistics_chatbot.core import config
from logistics_chatbot.core.errors import VectorDBError
from logistics_chatbot.infrastructure.embeddings import sentence_transformer as embeddings
from logistics_chatbot.utils.helpers import compute_content_hash

logger = logging.getLogger("logistics_chatbot.chroma_db")

_chroma_client: Optional[ClientAPI] = None


def get_chroma_client(reset: bool = False) -> ClientAPI:
    """Return a live ChromaDB client instance (singleton)."""
    global _chroma_client

    if _chroma_client is not None and not reset:
        return _chroma_client

    mode = (config.CHROMA_MODE or "persistent").lower()

    try:
        if mode == "persistent":
            persist_dir = Path(config.CHROMA_PERSIST_DIRECTORY)
            persist_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Initializing ChromaDB PersistentClient at: %s", persist_dir)
            _chroma_client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=Settings(anonymized_telemetry=False),
            )
        elif mode == "http":
            logger.info(
                "Connecting to ChromaDB HTTP Server at %s:%s (SSL=%s)",
                config.CHROMA_HOST,
                config.CHROMA_PORT,
                config.CHROMA_SSL,
            )
            headers = {}
            if config.CHROMA_API_KEY:
                headers["X-Chroma-Token"] = config.CHROMA_API_KEY
            _chroma_client = chromadb.HttpClient(
                host=config.CHROMA_HOST,
                port=config.CHROMA_PORT,
                ssl=config.CHROMA_SSL,
                headers=headers if headers else None,
                settings=Settings(anonymized_telemetry=False),
            )
        elif mode == "cloud":
            logger.info(
                "Connecting to Chroma Cloud (tenant=%s, database=%s)",
                config.CHROMA_TENANT,
                config.CHROMA_DATABASE,
            )
            _chroma_client = chromadb.CloudClient(
                tenant=config.CHROMA_TENANT,
                database=config.CHROMA_DATABASE,
                api_key=config.CHROMA_API_KEY,
                settings=Settings(anonymized_telemetry=False),
            )
        else:
            raise VectorDBError(
                detail=f"Unsupported CHROMA_MODE: '{mode}'. Must be 'persistent', 'http', or 'cloud'."
            )

        _chroma_client.heartbeat()
        logger.info("ChromaDB connection verified successfully (%s mode)", mode)
        return _chroma_client

    except VectorDBError:
        raise
    except Exception as exc:
        logger.error("ChromaDB connection initialization failed: %s", exc)
        _chroma_client = None
        raise VectorDBError(detail=f"Failed to connect to ChromaDB ({mode} mode): {exc}") from exc


def check_chroma_health() -> Dict[str, Any]:
    """Perform a health check on the ChromaDB vector database."""
    mode = (config.CHROMA_MODE or "persistent").lower()
    collection_name = config.CHROMA_COLLECTION_NAME

    try:
        client = get_chroma_client()
        heartbeat = client.heartbeat()
        col = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        return {
            "status": "healthy",
            "mode": mode,
            "heartbeat": heartbeat,
            "collection_name": collection_name,
            "record_count": col.count(),
            "persist_directory": str(config.CHROMA_PERSIST_DIRECTORY) if mode == "persistent" else None,
        }
    except Exception as exc:
        logger.warning("ChromaDB health check failed: %s", exc)
        return {
            "status": "unhealthy",
            "mode": mode,
            "collection_name": collection_name,
            "error": str(exc),
        }


def close() -> None:
    """Reset cached ChromaDB client reference."""
    global _chroma_client
    _chroma_client = None
    logger.info("ChromaDB client connection reference reset")


def get_or_create_collection(name: Optional[str] = None, space: str = "cosine"):
    """Retrieve or create a ChromaDB collection with cosine distance metric."""
    collection_name = name or config.CHROMA_COLLECTION_NAME
    client = get_chroma_client()
    try:
        return client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": space},
        )
    except Exception as exc:
        raise VectorDBError(detail=f"Failed to get or create collection '{collection_name}': {exc}") from exc


get_chroma_collection = get_or_create_collection


def delete_collection(name: Optional[str] = None) -> bool:
    """Delete a collection by name."""
    collection_name = name or config.CHROMA_COLLECTION_NAME
    client = get_chroma_client()
    try:
        client.delete_collection(name=collection_name)
        logger.info("Deleted ChromaDB collection: %s", collection_name)
        return True
    except Exception as exc:
        logger.warning("Could not delete collection '%s': %s", collection_name, exc)
        return False


def delete_document_chunks(document_id: str, collection_name: Optional[str] = None) -> int:
    """Delete all ChromaDB chunks belonging to a given doc_id / document_id."""
    clean_id = (document_id or "").strip()
    if not clean_id:
        return 0
    col = get_or_create_collection(collection_name)
    total_deleted = 0
    for field in ("doc_id", "document_id"):
        try:
            existing = col.get(where={field: clean_id}, include=[])
            ids = existing.get("ids") or []
            if ids:
                col.delete(ids=ids)
                total_deleted += len(ids)
        except Exception as exc:
            logger.debug("ChromaDB delete notice on %s=%s: %s", field, clean_id, exc)
    if total_deleted:
        logger.info("Deleted %d ChromaDB chunks for document '%s'", total_deleted, clean_id)
    return total_deleted


def upsert_knowledge_chunks(
    chunks: List[Dict[str, Any]],
    collection_name: Optional[str] = None,
    batch_size: int = 100,
    embed_fn=None,
) -> int:
    """Upsert structured knowledge chunks into the ChromaDB collection."""
    if not chunks:
        return 0

    col = get_or_create_collection(collection_name)
    encoder = embed_fn or embeddings.embed_texts

    chunks_to_embed = [c for c in chunks if not c.get("embedding")]
    if chunks_to_embed:
        texts_to_embed = [f"{c.get('title', '')}\n{c.get('content', '')}".strip() for c in chunks_to_embed]
        generated_vectors = encoder(texts_to_embed)
        for c, vec in zip(chunks_to_embed, generated_vectors):
            c["embedding"] = vec

    total_upserted = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        ids: List[str] = []
        embeddings_list: List[List[float]] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for item in batch:
            doc_id = str(item.get("doc_id", "DOC-UNKNOWN"))
            chunk_idx = int(item.get("chunk_index", 0))
            chunk_id = str(item.get("chunk_id") or f"{doc_id}_{chunk_idx}")
            content = str(item.get("content", ""))
            title = str(item.get("title") or item.get("section_title") or "Untitled")
            source = str(item.get("source", "kb_long.csv"))
            doc_type = str(item.get("doc_type", "knowledge_article"))
            category = str(item.get("category", "general"))
            language = str(item.get("language", "en"))
            timestamp = str(item.get("timestamp") or item.get("last_updated") or now_iso)
            content_hash = str(item.get("content_hash") or compute_content_hash(f"{title}:{content}"))

            vec = item["embedding"]
            if len(vec) != config.EMBEDDING_DIM:
                raise VectorDBError(
                    detail=(
                        f"Embedding dimension mismatch for '{chunk_id}': got {len(vec)}, "
                        f"expected {config.EMBEDDING_DIM}"
                    )
                )

            metadata: Dict[str, Any] = {
                "doc_id": doc_id,
                "title": title,
                "source": source,
                "doc_type": doc_type,
                "category": category,
                "language": language,
                "chunk_index": chunk_idx,
                "timestamp": timestamp,
                "content_hash": content_hash,
            }
            optional_meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            for extra_key in (
                "document_id",
                "document_name",
                "source_file",
                "page_number",
                "section_name",
                "document_category",
                "upload_timestamp",
                "section_title",
                "chunk_id",
            ):
                val = item.get(extra_key) if item.get(extra_key) is not None else optional_meta.get(extra_key)
                if val is not None and isinstance(val, (str, int, float, bool)):
                    metadata[extra_key] = val

            ids.append(chunk_id)
            embeddings_list.append(vec)
            documents.append(content)
            metadatas.append(metadata)

        try:
            col.upsert(
                ids=ids,
                embeddings=embeddings_list,
                documents=documents,
                metadatas=metadatas,
            )
            total_upserted += len(batch)
        except Exception as exc:
            raise VectorDBError(
                detail=f"Failed to upsert batch into ChromaDB collection '{col.name}': {exc}"
            ) from exc

    logger.info("Successfully upserted %d chunks into ChromaDB", total_upserted)
    return total_upserted


def ingest_from_kb(
    rows: Optional[List[Dict[str, Any]]] = None,
    collection_name: Optional[str] = None,
    limit: Optional[int] = None,
) -> int:
    """Ingest knowledge base rows into ChromaDB."""
    if rows is None:
        from logistics_chatbot.application.ingestion.kb_loader import load_kb_rows

        rows = load_kb_rows()

    if limit and limit > 0:
        rows = rows[:limit]

    chunks: List[Dict[str, Any]] = []
    for idx, r in enumerate(rows):
        doc_id = r.get("doc_id") or f"DOC-{idx+1:04d}"
        title = r.get("section_title") or r.get("title") or "General Policy"
        content = r.get("content", "")
        category = r.get("category", "general")
        source = "kb_long.csv" if "DOC" in doc_id else "knowledge_base.json"
        doc_type = "faq" if "FAQ" in doc_id else "policy"

        chunks.append({
            "chunk_id": f"{doc_id}_0",
            "doc_id": doc_id,
            "title": title,
            "content": content,
            "category": category,
            "source": source,
            "doc_type": doc_type,
            "language": "en",
            "chunk_index": 0,
            "timestamp": str(r.get("last_updated", "2026-11-01")),
            "content_hash": compute_content_hash(f"{title}:{content}"),
        })

    return upsert_knowledge_chunks(chunks, collection_name=collection_name)


def query_knowledge_chunks(
    query_text: str,
    top_k: Optional[int] = None,
    where: Optional[Dict[str, Any]] = None,
    min_score: Optional[float] = None,
    collection_name: Optional[str] = None,
    query_vector: Optional[List[float]] = None,
) -> List[Dict[str, Any]]:
    """Perform semantic vector search in ChromaDB with cosine distance."""
    if not query_text or not query_text.strip():
        return []

    if top_k is None:
        top_k = config.RETRIEVAL_TOP_K
    if min_score is None:
        min_score = config.RETRIEVAL_MIN_SCORE

    try:
        col = get_or_create_collection(collection_name)
        if col.count() == 0:
            return []

        if query_vector is None:
            query_vector = embeddings.embed_query(query_text.strip())

        if not isinstance(query_vector, (list, tuple)) or not query_vector or not isinstance(query_vector[0], (int, float)):
            logger.debug("Query vector is not a dense float list (got %s), skipping ChromaDB query", type(query_vector))
            return []

        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [query_vector],
            "n_results": min(top_k * 2 if where else top_k, col.count()),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where

        results = col.query(**query_kwargs)

        out: List[Dict[str, Any]] = []
        ids_list = results.get("ids", [[]])[0]
        docs_list = results.get("documents", [[]])[0]
        metas_list = results.get("metadatas", [[]])[0]
        dists_list = results.get("distances", [[]])[0]

        for chunk_id, doc, meta, dist in zip(ids_list, docs_list, metas_list, dists_list):
            similarity = round(max(0.0, min(1.0, 1.0 - float(dist))), 4)
            if similarity < min_score:
                continue

            out.append({
                "chunk_id": chunk_id,
                "doc_id": meta.get("doc_id", chunk_id),
                "document_id": meta.get("document_id", meta.get("doc_id", chunk_id)),
                "document_name": meta.get("document_name", meta.get("title", "")),
                "source_file": meta.get("source_file", meta.get("source", "")),
                "page_number": meta.get("page_number"),
                "section_name": meta.get("section_name", meta.get("section_title", meta.get("title", ""))),
                "section_title": meta.get("section_title", meta.get("title", "")),
                "category": meta.get("category", "general"),
                "document_category": meta.get("document_category", meta.get("category", "general")),
                "content": doc,
                "score": similarity,
                "source": meta.get("source", ""),
                "doc_type": meta.get("doc_type", ""),
                "language": meta.get("language", "en"),
                "chunk_index": meta.get("chunk_index", 0),
                "timestamp": meta.get("timestamp", ""),
                "upload_timestamp": meta.get("upload_timestamp", meta.get("timestamp", "")),
                "content_hash": meta.get("content_hash", ""),
                "metadata": meta,
            })

        out.sort(key=lambda x: x["score"], reverse=True)
        return out[:top_k]

    except VectorDBError:
        raise
    except Exception as exc:
        logger.error("ChromaDB query failed: %s", exc)
        raise VectorDBError(detail=f"Semantic search in ChromaDB failed: {exc}") from exc
