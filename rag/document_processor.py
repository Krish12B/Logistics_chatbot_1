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
PDF_CHUNK_SIZE = 750
PDF_CHUNK_OVERLAP = 110
MIN_CHUNK_LENGTH = 30
SUPPORTED_EXTENSIONS = (".txt", ".pdf", ".docx", ".csv")

_PDF_NOISE_PATTERNS = [
    re.compile(r"^Page\s+\d+\s+of\s+\d+\s*\|\s*Allcargo\s+Logistics\s*[—\-]+\s*Internal\s+Reference$", re.IGNORECASE),
    re.compile(r"^Allcargo\s+Logistics\s*[—\-]+\s*Internal\s+Reference$", re.IGNORECASE),
    re.compile(r"^[^|]{3,80}\|\s*Page\s+\d+$", re.IGNORECASE),
    re.compile(r"^Page\s+\d+(?:\s+of\s+\d+)?$", re.IGNORECASE),
]
_SECTION_HEADING_RE = re.compile(
    r"^(?:(?:\d{1,2}\.\s+[A-Z][^\n]{2,90})|(?:Table\s+\d+\s*[—\-:]\s*[^\n]{2,90})|(?:Example\s+[A-Z]\s*[—\-:]\s*[^\n]{2,90}))$"
)

PDF_CATALOG_MAP: Dict[str, Tuple[str, str, str]] = {
    "customer support tracking booking reference.pdf": (
        "PDF-CUST-SUPPORT",
        "Customer Support, Tracking & Booking Reference",
        "customer_support",
    ),
    "export import documentation customs reference guide.pdf": (
        "PDF-EXIM-CUSTOMS",
        "Export-Import Documentation & Customs Reference Guide",
        "customs_documentation",
    ),
    "incoterms international trade terms guide.pdf": (
        "PDF-INCOTERMS",
        "Incoterms & International Trade Terms Guide",
        "incoterms_trade",
    ),
    "shipment delay causes route risk reference.pdf": (
        "PDF-DELAY-RISK",
        "Shipment Delay Causes & Route Risk Reference",
        "delay_route_risk",
    ),
    "warehousing contract logistics reference.pdf": (
        "PDF-WAREHOUSING",
        "Warehousing & Contract Logistics Reference",
        "warehousing_logistics",
    ),
}


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


def _clean_pdf_lines(raw_text: str) -> str:
    """Clean extracted PDF page text while preserving headings, tables, and logical paragraphs."""
    normalized = re.sub(r"\r\n|\r", "\n", raw_text or "")
    cleaned_lines: List[str] = []
    for raw_ln in normalized.split("\n"):
        ln = re.sub(r"[ \t]+", " ", raw_ln).strip()
        if not ln:
            cleaned_lines.append("")
            continue
        if any(pat.match(ln) for pat in _PDF_NOISE_PATTERNS):
            continue
        # Ensure headings / table headers stand as distinct blocks
        if _SECTION_HEADING_RE.match(ln):
            cleaned_lines.append("")
            cleaned_lines.append(ln)
            cleaned_lines.append("")
        else:
            cleaned_lines.append(ln)

    # Reflow soft-wrapped prose lines inside blocks while keeping headings, bullets, and short table cells intact
    blocks: List[str] = []
    buf: List[str] = []
    for ln in cleaned_lines:
        if ln == "":
            if buf:
                blocks.append(" ".join(buf))
                buf = []
            continue
        is_bullet = ln.startswith(("•", "-", "*")) or re.match(r"^\d+\.\s", ln)
        if is_bullet and buf:
            blocks.append(" ".join(buf))
            buf = [ln]
        elif len(ln) <= 35 and buf and not buf[-1].endswith((".", ":", "?", "!")):
            # Likely tabular cell column or short subhead — separate by newline cleanly
            buf.append("\n" + ln)
        else:
            buf.append(ln)
    if buf:
        blocks.append(" ".join(buf))

    text = "\n\n".join(b.strip() for b in blocks if b.strip())
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_pages_structured(content: bytes) -> List[Dict[str, Any]]:
    """Extract per-page cleaned text and section headings from PDF bytes using pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        pages: List[Dict[str, Any]] = []
        active_section = "Overview"

        for idx, page in enumerate(reader.pages, start=1):
            try:
                raw_txt = page.extract_text() or ""
            except Exception as page_exc:
                logger.warning("PDF page %d extraction error: %s", idx, page_exc)
                continue

            cleaned = _clean_pdf_lines(raw_txt)
            if not cleaned:
                logger.debug("Skipping empty PDF page %d", idx)
                continue

            headings = [
                blk.strip()
                for blk in cleaned.split("\n\n")
                if _SECTION_HEADING_RE.match(blk.strip())
            ]
            page_section = headings[0] if headings else active_section
            if headings:
                active_section = headings[-1]

            pages.append({
                "page_number": idx,
                "text": cleaned,
                "headings": headings,
                "section_name": page_section,
            })

        if not pages:
            raise ValueError("PDF file contains no extractable text (it may be scanned/image-only).")
        return pages
    except ImportError:
        raise ValueError("PDF parsing library (pypdf) is not installed on the system.")
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"Failed to parse PDF document: {exc}") from exc


def extract_text_from_pdf(content: bytes) -> str:
    """Extract cleaned multi-page text from PDF file bytes using pypdf."""
    pages = extract_pdf_pages_structured(content)
    return "\n\n".join(p["text"] for p in pages).strip()


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


def _infer_chunk_section(page_text: str, chunk_text: str, default_section: str) -> str:
    """Identify the active numbered heading or table title for a PDF chunk."""
    lines_in_chunk = [ln.strip() for ln in chunk_text.splitlines() if _SECTION_HEADING_RE.match(ln.strip())]
    if lines_in_chunk:
        return lines_in_chunk[0]
    probe = chunk_text[:120].strip()
    pos = page_text.find(probe)
    if pos > 0:
        preceding = page_text[:pos]
        prior_headings = [ln.strip() for ln in preceding.splitlines() if _SECTION_HEADING_RE.match(ln.strip())]
        if prior_headings:
            return prior_headings[-1]
    return default_section


def process_pdf_document(
    filename: str,
    content: bytes,
    category: Optional[str] = None,
    document_id: Optional[str] = None,
    document_name: Optional[str] = None,
    chunk_size: int = PDF_CHUNK_SIZE,
    overlap: int = PDF_CHUNK_OVERLAP,
) -> Tuple[List[Dict[str, Any]], str]:
    """Extract, clean, chunk, deduplicate, and attach rich page/section metadata for PDF documents."""
    if not content or len(content) == 0:
        raise ValueError("The uploaded document is empty.")

    pages = extract_pdf_pages_structured(content)
    full_text = "\n\n".join(p["text"] for p in pages)
    catalog_hit = PDF_CATALOG_MAP.get(Path(filename).name.lower())
    if catalog_hit:
        cat_doc_id, cat_doc_name, cat_domain = catalog_hit
        doc_id = document_id or cat_doc_id
        doc_name = document_name or cat_doc_name
        doc_cat = category or cat_domain
    else:
        doc_id = document_id or f"DOC-{compute_hash(full_text)[:12].upper()}"
        doc_name = document_name or Path(filename).stem
        doc_cat = category or "uploaded_document"

    timestamp = datetime.now(timezone.utc).isoformat()
    seen_chunk_hashes: set[str] = set()
    processed_chunks: List[Dict[str, Any]] = []
    global_idx = 0

    for page_info in pages:
        page_num = page_info["page_number"]
        page_text = page_info["text"]
        default_sec = page_info["section_name"]
        page_chunks = split_text_into_chunks(page_text, chunk_size=chunk_size, overlap=overlap)
        if not page_chunks:
            page_chunks = [page_text]

        for p_idx, chunk_text in enumerate(page_chunks, start=1):
            c_hash = compute_hash(re.sub(r"\s+", " ", chunk_text.strip()))
            if c_hash in seen_chunk_hashes:
                continue
            seen_chunk_hashes.add(c_hash)
            global_idx += 1

            section_name = _infer_chunk_section(page_text, chunk_text, default_sec)
            chunk_id = f"{doc_id}-P{page_num:02d}-C{p_idx:03d}"
            title_display = f"{doc_name} | p.{page_num}: {section_name}"

            metadata = {
                # Phase 3 standardized PDF metadata keys
                "document_id": doc_id,
                "document_name": doc_name,
                "source_file": Path(filename).name,
                "page_number": page_num,
                "section_name": section_name,
                "document_category": doc_cat,
                "upload_timestamp": timestamp,
                "chunk_id": chunk_id,
                # Legacy ChromaDB / search compatibility keys
                "doc_id": doc_id,
                "filename": Path(filename).name,
                "chunk_index": global_idx,
                "source": Path(filename).name,
                "file_format": "pdf",
                "doc_type": "pdf_reference" if catalog_hit else "uploaded_document",
                "category": doc_cat,
                "title": title_display,
                "section_title": title_display,
                "character_count": len(chunk_text),
                "word_count": len(chunk_text.split()),
                "content_hash": c_hash[:16],
                "timestamp": timestamp[:10],
                "language": "en",
                "status": "active",
            }
            processed_chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "metadata": metadata,
            })

    total = len(processed_chunks)
    for item in processed_chunks:
        item["metadata"]["total_chunks"] = total

    return processed_chunks, doc_id


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

    if ext == ".pdf" and isinstance(content, (bytes, bytearray)):
        return process_pdf_document(filename, bytes(content))

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
