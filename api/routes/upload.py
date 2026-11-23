"""Document upload route controller for indexing new text knowledge into ChromaDB."""
from __future__ import annotations

import logging
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from api.schemas.request_models import DocUploadData, DocUploadResponse, ErrorResponse
from rag.document_processor import SUPPORTED_EXTENSIONS, process_document, process_txt_document
from rag.search import index_document_chunks

logger = logging.getLogger("logistics_chatbot.api.upload")
router = APIRouter(tags=["upload"])

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 Megabytes


@router.post(
    "/upload-doc",
    response_model=DocUploadResponse,
    responses={
        200: {"model": DocUploadResponse, "description": "Document processed and indexed into ChromaDB"},
        400: {"model": ErrorResponse, "description": "Invalid file format, empty file, or encoding error"},
        413: {"model": ErrorResponse, "description": "File exceeds 5MB size limit"},
        500: {"model": ErrorResponse, "description": "Indexing or embedding generation error"},
    },
    summary="Upload and index a knowledge document (.txt, .pdf, .docx)",
    description="Accepts a .txt, .pdf, or .docx document via multipart/form-data, splits it into semantic chunks, generates embeddings, and indexes them into ChromaDB for immediate RAG retrieval.",
)
async def upload_document_endpoint(
    file: UploadFile = File(..., description="Knowledge base document (.txt, .pdf, .docx)")
) -> JSONResponse:
    # 1. Validate filename and extension
    filename = file.filename or ""
    if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
        logger.warning("Rejected unsupported upload: %s", filename)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": f"Unsupported file type for '{filename}'. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}",
                "data": None,
            },
        )

    # 2. Read file content
    try:
        content_bytes = await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file %s: %s", filename, exc)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": f"Failed to read file contents: {exc}",
                "data": None,
            },
        )

    # 3. Validate file size limit (5MB)
    if len(content_bytes) > MAX_FILE_SIZE_BYTES:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "success": False,
                "message": f"File size ({len(content_bytes):,} bytes) exceeds maximum allowed limit of 5MB.",
                "data": None,
            },
        )

    # 4. Process, decode/extract, and chunk text
    try:
        chunks, doc_id = process_document(filename=filename, content=content_bytes)
    except ValueError as exc:
        logger.warning("Validation failure for file %s: %s", filename, exc)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": str(exc),
                "data": None,
            },
        )
    except Exception as exc:
        logger.exception("Unexpected error processing document %s: %s", filename, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"Failed to process document content: {exc}",
                "data": None,
            },
        )

    # 5. Index chunks and generate embeddings into ChromaDB
    try:
        indexed_count = index_document_chunks(chunks)
        logger.info(
            "Document '%s' successfully indexed: %d chunks created and stored in ChromaDB (Doc ID: %s)",
            filename,
            indexed_count,
            doc_id,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Document uploaded successfully",
                "data": {
                    "filename": filename,
                    "chunks_created": indexed_count,
                    "status": "Indexed Successfully",
                },
            },
        )
    except Exception as exc:
        logger.exception("ChromaDB indexing failure for document %s: %s", filename, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"Vector indexing failed: {exc}",
                "data": None,
            },
        )
