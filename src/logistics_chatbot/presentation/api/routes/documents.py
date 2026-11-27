"""Document and CSV upload ingestion HTTP routes."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from logistics_chatbot.application.services import document_service
from logistics_chatbot.core import config
from logistics_chatbot.domain.exceptions import (
    ChatbotError,
    DocumentProcessingError,
    InvalidFileFormatError,
)
from logistics_chatbot.presentation.api.schemas.responses import (
    DocUploadData,
    DocUploadResponse,
    ErrorResponse,
)

logger = logging.getLogger("logistics_chatbot.api.documents")
router = APIRouter(tags=["upload"])


@router.post(
    "/upload-doc",
    response_model=DocUploadResponse,
    responses={
        200: {"model": DocUploadResponse, "description": "Document or CSV processed and integrated"},
        400: {"model": ErrorResponse, "description": "Invalid file format, empty file, or validation error"},
        413: {"model": ErrorResponse, "description": "File exceeds size limit"},
        500: {"model": ErrorResponse, "description": "Processing or database integration error"},
    },
    summary="Upload and ingest a document or structured dataset (.txt, .pdf, .docx, .csv)",
    description="Accepts .txt, .pdf, .docx, or .csv. CSV files are analyzed, validated, integrated into the relational database, and indexed into ChromaDB. Documents are chunked and indexed into ChromaDB.",
)
async def upload_document_endpoint(
    file: UploadFile = File(
        ...,
        description="Knowledge base document or dataset (.txt, .pdf, .docx, .csv)",
    )
):
    """Ingest uploaded documents or datasets into ChromaDB and SQLite."""
    filename = file.filename or ""
    if not filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a valid filename.")

    ext = Path(filename).suffix.lower()
    if ext not in document_service.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported extensions: {', '.join(sorted(document_service.SUPPORTED_EXTENSIONS))}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail=f"Uploaded file '{filename}' is empty.")

    if len(content) > config.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file '{filename}' exceeds maximum allowed size of {config.MAX_UPLOAD_SIZE_BYTES} bytes.",
        )

    try:
        result = document_service.ingest_uploaded_file(filename=filename, content_bytes=content)
    except InvalidFileFormatError as exc:
        raise HTTPException(status_code=400, detail=exc.user_message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except DocumentProcessingError as exc:
        logger.error("Document processing failed for '%s': %s", filename, exc.detail or exc)
        raise HTTPException(status_code=500, detail=exc.user_message)
    except ChatbotError as exc:
        logger.error("Upload chatbot error for '%s': %s", filename, exc.detail or exc)
        raise HTTPException(status_code=exc.status_code, detail=exc.user_message)
    except Exception as exc:
        logger.exception("Failed to process uploaded file '%s': %s", filename, exc)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the uploaded file.")

    if result["kind"] == "csv":
        payload = result["payload"]
        inner = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        return DocUploadResponse(
            success=True,
            message=payload.get("message", f"CSV dataset '{filename}' processed successfully"),
            data=DocUploadData(
                filename=inner.get("filename", filename),
                chunks_created=inner.get("chunks_created", payload.get("chunks_indexed", 0)),
                status=inner.get("status", "Imported and Indexed Successfully"),
                total_records=inner.get("total_records"),
                imported=inner.get("imported"),
                skipped=inner.get("skipped"),
                failed=inner.get("failed"),
                category=inner.get("category"),
                summary=payload.get("summary"),
            ),
            summary=payload.get("summary"),
        )

    chunks_created = result.get("chunks_created", 0)
    return DocUploadResponse(
        success=True,
        message="Document uploaded successfully",
        data=DocUploadData(
            filename=filename,
            chunks_created=chunks_created,
            status="Indexed Successfully",
        ),
    )
