"""Document upload route controller for indexing new text knowledge into ChromaDB."""
from __future__ import annotations

import logging
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from api.schemas.request_models import DocUploadData, DocUploadResponse, ErrorResponse
from logistics_chatbot.document_ingestion.csv_processor import process_csv_upload
from rag.document_processor import SUPPORTED_EXTENSIONS, process_document, process_txt_document
from rag.search import index_document_chunks

logger = logging.getLogger("logistics_chatbot.api.upload")
router = APIRouter(tags=["upload"])

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 Megabytes


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
    file: UploadFile = File(..., description="Knowledge base document or dataset (.txt, .pdf, .docx, .csv)")
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

    # 3. Validate file size limit
    if len(content_bytes) > MAX_FILE_SIZE_BYTES:
        return JSONResponse(
            status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
            content={
                "success": False,
                "message": f"File size ({len(content_bytes):,} bytes) exceeds maximum allowed limit of 10MB.",
                "data": None,
            },
        )

    # 4. Check for Empty File Content
    if not content_bytes or not content_bytes.strip():
        logger.warning("Validation failure for file %s: The uploaded document is empty.", filename)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": "The uploaded document is empty.",
                "data": None,
            },
        )

    # 5. Specialized CSV Ingestion Workflow
    if filename.lower().endswith(".csv"):
        try:
            csv_result = process_csv_upload(filename=filename, content_bytes=content_bytes)
            logger.info("CSV '%s' processed successfully: %s", filename, csv_result["data"])
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": csv_result["message"],
                    "summary": csv_result["summary"],
                    "data": csv_result["data"],
                },
            )
        except ValueError as exc:
            logger.warning("CSV validation failure for file %s: %s", filename, exc)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": str(exc),
                    "data": None,
                },
            )
        except Exception as exc:
            logger.exception("Unexpected error during CSV ingestion for %s: %s", filename, exc)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "message": f"Failed to process CSV file: {exc}",
                    "data": None,
                },
            )

    # 6. Unstructured Document Processing (.txt, .pdf, .docx)
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

    # 7. Index chunks and generate embeddings into ChromaDB
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
                "summary": f"Document `{filename}` successfully indexed into ChromaDB ({indexed_count} semantic chunks).",
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
