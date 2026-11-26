"""Document processing service: text decoding, validation, chunking, and metadata generation."""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
import io
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("logistics_chatbot.document_processor")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
MIN_CHUNK_LENGTH = 30
SUPPORTED_EXTENSIONS = (".txt", ".pdf", ".docx", ".csv")


def decode_bytes(content: bytes) -> str:
    """Decode raw bytes trying common text encodings."""
    if not content or not content.strip():
        raise ValueError("Uploaded document content is empty.")

    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            decoded = content.decode(enc)
            if decoded.strip():
                return decoded
        except (UnicodeDecodeError, LookupError):
            continue

    raise ValueError("Unable to decode document content. Please ensure the file contains valid text.")


def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF file bytes using pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        pages_text = []
        for idx, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            if txt.strip():
                pages_text.append(txt.strip())
        extracted = "\n\n".join(pages_text).strip()
        if not extracted:
            raise ValueError("PDF file contains no extractable text (it may be scanned/image-only).")
        return extracted
    except ImportError:
        raise ValueError("PDF parsing library (pypdf) is not installed on the system.")
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"Failed to parse PDF document: {exc}") from exc


def extract_text_from_docx(content: bytes) -> str:
    """Extract text from DOCX file bytes using python-docx."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(content))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        # Also extract table text
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
                if row_text:
                    paragraphs.append(row_text)
        extracted = "\n\n".join(paragraphs).strip()
        if not extracted:
            raise ValueError("DOCX file contains no extractable text.")
        return extracted
    except ImportError:
        raise ValueError("DOCX parsing library (python-docx) is not installed on the system.")
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"Failed to parse DOCX document: {exc}") from exc


def extract_text(filename: str, content: bytes | str) -> str:
    """Extract raw text from a document based on its file extension."""
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format '{ext}'. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    if isinstance(content, str):
        if not content.strip():
            raise ValueError("The uploaded document is empty or contains only whitespace.")
        return content.strip()

    if not content or len(content) == 0:
        raise ValueError("The uploaded document is empty.")

    if ext == ".txt":
        return decode_bytes(content)
    elif ext == ".pdf":
        return extract_text_from_pdf(content)
    elif ext == ".docx":
        return extract_text_from_docx(content)
    elif ext == ".csv":
        return decode_bytes(content)
    else:
        raise ValueError(f"Unsupported format: {ext}")


def compute_hash(text: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into semantic chunks respecting paragraphs, sentences, length boundaries, and overlap."""
    cleaned = re.sub(r"\r\n|\r", "\n", text).strip()
    if not cleaned:
        return []

    # First attempt to split on double newlines (paragraphs)
    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    raw_chunks: List[str] = []

    current_chunk: List[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        if para_len > chunk_size:
            # Flush existing accumulated paragraphs before splitting large paragraph
            if current_chunk:
                raw_chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            sub_units = [s.strip() for s in re.split(r"(?<=[.!?])\s+", para) if s.strip()]
            for unit in sub_units:
                if current_len + len(unit) + 1 > chunk_size and current_chunk:
                    raw_chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_len = 0
                current_chunk.append(unit)
                current_len += len(unit) + 1
        else:
            if current_len + para_len + 2 > chunk_size and current_chunk:
                raw_chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            current_chunk.append(para)
            current_len += para_len + 2

    if current_chunk:
        raw_chunks.append("\n\n".join(current_chunk))

    filtered = [c.strip() for c in raw_chunks if len(c.strip()) >= MIN_CHUNK_LENGTH]
    if not filtered and cleaned:
        return [cleaned]

    if overlap <= 0 or len(filtered) <= 1:
        return filtered

    # Prepend word-aligned trailing overlap from chunk[i-1] into chunk[i]
    overlapped_chunks: List[str] = [filtered[0]]
    for idx in range(1, len(filtered)):
        prev_text = filtered[idx - 1]
        tail = prev_text[-overlap:].lstrip()
        # Snap to nearest word boundary so we don't start mid-word
        if len(prev_text) > overlap and " " in tail:
            tail = tail.split(" ", 1)[1].strip()
        if tail and not filtered[idx].startswith(tail):
            overlapped_chunks.append(f"{tail}\n\n{filtered[idx]}")
        else:
            overlapped_chunks.append(filtered[idx])

    return overlapped_chunks


def process_document(
    filename: str,
    content: bytes | str,
) -> Tuple[List[Dict[str, Any]], str]:
    """Process, validate, chunk, and prepare metadata for an uploaded document (.txt, .pdf, .docx).

    Args:
        filename: Name of the uploaded file.
        content: Raw bytes or string content of the file.

    Returns:
        Tuple of (list of prepared chunk dicts, document_id)
    """
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Invalid file format '{filename}'. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")

    text = extract_text(filename, content)
    text = text.strip()
    if not text:
        raise ValueError("The uploaded document is empty or contains only whitespace.")

    doc_hash = compute_hash(text)[:12]
    doc_id = f"DOC-{doc_hash.upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    chunks = split_text_into_chunks(text)
    if not chunks:
        chunks = [text]

    processed_chunks: List[Dict[str, Any]] = []
    for idx, chunk_text in enumerate(chunks):
        chunk_id = f"{doc_id}-{idx + 1:03d}"
        part_title = f"{filename} (Part {idx + 1}/{len(chunks)})"
        metadata = {
            "doc_id": doc_id,
            "filename": filename,
            "chunk_id": chunk_id,
            "chunk_index": idx + 1,
            "total_chunks": len(chunks),
            "upload_timestamp": timestamp,
            "source": filename,
            "file_format": ext.lstrip("."),
            "character_count": len(chunk_text),
            "word_count": len(chunk_text.split()),
            "content_hash": compute_hash(chunk_text),
            "category": "uploaded_document",
            "title": part_title,
            "section_title": part_title,
            "status": "active",
        }
        processed_chunks.append({
            "chunk_id": chunk_id,
            "text": chunk_text,
            "metadata": metadata,
        })

    return processed_chunks, doc_id


def process_txt_document(
    filename: str,
    content: bytes | str,
) -> Tuple[List[Dict[str, Any]], str]:
    """Process, validate, chunk, and prepare metadata for an uploaded .txt document (backward compatible)."""
    if not filename.lower().endswith(".txt"):
        raise ValueError(f"Invalid file format '{filename}'. Only .txt documents are supported.")
    return process_document(filename, content)
