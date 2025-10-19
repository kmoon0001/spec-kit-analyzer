"""Analysis API router for document compliance analysis.

Provides endpoints for uploading documents, running compliance analysis,
and retrieving analysis results.
"""

import asyncio
import datetime
import sqlite3
import uuid
from typing import Any

import sqlalchemy
import sqlalchemy.exc
import structlog
from pydantic import BaseModel

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import get_current_active_user
from ...core.analysis_service import AnalysisService
from ...core.security_validator import SecurityValidator
from ...core.file_upload_validator import validate_uploaded_file, sanitize_filename
from ...core.file_encryption import get_secure_storage
from ...database import crud, models, schemas
from ...database.database import get_async_db
from ..task_registry import analysis_task_registry
from ..dependencies import get_analysis_service
from ..deps.request_tracking import RequestId, log_with_request_id

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])

tasks = analysis_task_registry.metadata

# Secure document storage (replaces in-memory storage)
secure_storage = get_secure_storage()
legacy_router = APIRouter(tags=["analysis-legacy"])


class LegacyAnalysisRequest(BaseModel):
    document_id: str
    rubric_id: str
    analysis_type: str = "comprehensive"
    discipline: str | None = None


async def run_analysis_and_save(
    file_content: bytes,
    task_id: str,
    original_filename: str,
    discipline: str,
    analysis_mode: str,
    strictness: str,
    analysis_service: AnalysisService,
    user_id: int,
) -> None:
    """Background task coordinator that schedules the async analysis workflow."""

    def _update_progress(percentage: int, message: str | None) -> None:
        state = tasks.setdefault(task_id, {})
        state["progress"] = percentage
        state["status_message"] = message
        if percentage >= 100:
            state["status"] = "completed"
        elif percentage >= 60:
            state["status"] = "analyzing"
        else:
            state["status"] = "processing"
        logger.info("Task %s progress: %d%% - %s", task_id, percentage, message)

    async def _async_analysis() -> None:
        try:
            logger.info("Starting analysis for task %s", task_id)
            _update_progress(0, "Analysis started.")
            result = await analysis_service.analyze_document(
                file_content=file_content,
                original_filename=original_filename,
                discipline=discipline,
                analysis_mode=analysis_mode,
                strictness=strictness,
                progress_callback=_update_progress,
            )
            # The result from analyze_document has nested structure: {analysis: {...}, report_html: ...}
            analysis_payload = result if isinstance(result, dict) else {}

            # Extract the analysis data (may be nested under "analysis" key)
            analysis_data = analysis_payload.get("analysis", analysis_payload)

            # Extract findings and other data
            findings = analysis_data.get("findings", [])
            compliance_score = analysis_data.get("compliance_score") or analysis_payload.get("compliance_score")
            document_type = analysis_data.get("document_type") or analysis_payload.get("document_type")
            report_html = analysis_payload.get("report_html")

            logger.info("Analysis result structure: %s", list(analysis_payload.keys()) if isinstance(analysis_payload, dict) else "Not a dict")
            logger.info("Found %d findings, compliance score: %s", len(findings), compliance_score)

            task_entry = tasks[task_id]
            task_entry["status"] = "analyzing"
            task_entry["status_message"] = "Finalizing analysis results..."
            task_entry["progress"] = max(task_entry.get("progress", 90), 95)
            task_entry["user_id"] = user_id  # Track user ownership
            await asyncio.sleep(0.2)
            task_entry.update(
                {
                    "status": "completed",
                    "result": result,
                    "filename": original_filename,
                    "timestamp": datetime.datetime.now(datetime.UTC),
                    "progress": 100,
                    "status_message": "Analysis complete.",
                    "analysis": analysis_payload,
                    "findings": findings,
                    "overall_score": compliance_score,
                    "document_type": document_type,
                    "report_html": report_html,
                    "strictness": strictness,
                }
            )
            logger.info("Analysis completed for task %s", task_id)
        except Exception as exc:
            logger.exception("Analysis task failed", task_id=task_id, error=str(exc))
            tasks[task_id] = {
                "status": "failed",
                "error": str(exc),
                "filename": original_filename,
                "timestamp": datetime.datetime.now(datetime.UTC),
                "progress": 0,
                "status_message": f"Analysis failed: {exc}",
                "strictness": strictness,
                "findings": [],
                "overall_score": 0.0,
                "document_type": "Unknown",
                "report_html": None,
            }
            # Task failure is already handled by the task registry cleanup

    await analysis_task_registry.start(task_id, _async_analysis())


@legacy_router.post("/upload-document")
async def legacy_upload_document(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Legacy-friendly endpoint to upload documents with secure encryption."""
    try:
        safe_filename = SecurityValidator.validate_and_sanitize_filename(file.filename or "")
    except ValueError as exc:  # pragma: no cover - defensive sanitization
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    content = await file.read()
    is_valid_size, error = SecurityValidator.validate_file_size(len(content))
    if not is_valid_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error or "Invalid file size")

    # Store document securely with encryption
    document_id = secure_storage.store_document(
        content=content,
        filename=safe_filename,
        user_id=current_user.id,
        metadata={
            "upload_type": "legacy",
            "original_filename": file.filename,
            "content_type": file.content_type
        }
    )

    logger.info("Legacy upload stored securely", document_id=document_id, filename=safe_filename, user_id=current_user.id)
    return {"status": "success", "document_id": document_id, "filename": safe_filename}


@legacy_router.get("/documents/{document_id}")
async def legacy_get_document(
    document_id: str, current_user: models.User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """Retrieve document metadata (content not included for security)."""
    # Get document metadata from secure storage
    user_docs = secure_storage.list_user_documents(current_user.id)
    document_metadata = None

    for doc in user_docs:
        if doc["doc_id"] == document_id:
            document_metadata = doc
            break

    if not document_metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    return {
        "id": document_id,
        "filename": document_metadata["filename"],
        "file_size": document_metadata["file_size"],
        "uploaded_at": document_metadata["stored_at"],
        "metadata": document_metadata["metadata"]
    }


@legacy_router.post("/analyze")
async def legacy_start_analysis(
    request: LegacyAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_active_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> dict[str, str]:
    """Kick off an analysis job using a previously uploaded document."""
    if analysis_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analysis service is not ready yet.",
        )

    # Retrieve document content from secure storage
    document_content = secure_storage.retrieve_document(request.document_id, current_user.id)
    if not document_content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Get document metadata
    user_docs = secure_storage.list_user_documents(current_user.id)
    document_metadata = None
    for doc in user_docs:
        if doc["doc_id"] == request.document_id:
            document_metadata = doc
            break

    if not document_metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document metadata not found.")

    discipline = (request.discipline or "pt").lower()
    is_valid, error = SecurityValidator.validate_discipline(discipline)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error or "Invalid discipline")

    analysis_mode = request.analysis_type.lower()
    if analysis_mode == "comprehensive":
        analysis_mode = "rubric"
    is_valid_mode, mode_error = SecurityValidator.validate_analysis_mode(analysis_mode)
    if not is_valid_mode:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=mode_error or "Invalid analysis mode")

    task_id = uuid.uuid4().hex
    tasks[task_id] = {
        "status": "processing",
        "filename": document_metadata["filename"],
        "timestamp": datetime.datetime.now(datetime.UTC),
        "strictness": "standard",
        "user_id": current_user.id,  # Track user ownership
    }

    background_tasks.add_task(
        run_analysis_and_save,
        document_content,
        task_id,
        document_metadata["filename"],
        discipline,
        analysis_mode,
        "standard",
        analysis_service,
        current_user.id,  # Pass user ID
    )

    logger.info("Legacy analysis started", document_id=request.document_id, task_id=task_id)
    return {"status": "started", "task_id": task_id}


@legacy_router.get("/analysis-status/{task_id}")
async def legacy_get_analysis_status(
    task_id: str, current_user: models.User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """Expose task status without the /analysis prefix for older clients."""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check authorization - user must own the task or be admin
    if task.get("user_id") != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this task")

    current_status = task.get("status", "processing")
    if current_status == "completed":
        if not task.get("_reported_completion"):
            task["_reported_completion"] = True
            transient = dict(task)
            transient["status"] = "analyzing"
            return transient
        return dict(task)

    # Ensure progress and status_message are always returned, even if not explicitly set yet
    task.setdefault("progress", 0)
    task.setdefault("status_message", "Initializing...")
    return task


@legacy_router.post("/export-pdf/{task_id}")
async def legacy_export_report(
    task_id: str, current_user: models.User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """Export analysis report to PDF for legacy clients."""
    return await export_report_to_pdf(task_id, current_user)


@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    discipline: str = Form("pt"),
    analysis_mode: str = Form("rubric"),
    strictness: str = Form("standard"),
    _current_user: models.User = Depends(get_current_active_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
    request_id: str = RequestId,
) -> dict[str, str]:
    """Upload and analyze a clinical document for compliance from in-memory content with request tracking."""
    log_with_request_id(
        f"Analysis request started by user {_current_user.username}",
        level="info",
        user_id=_current_user.id,
        filename=file.filename,
        discipline=discipline,
        analysis_mode=analysis_mode,
        strictness=strictness
    )
    if analysis_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Analysis service is not ready yet."
        )

    try:
        # Read file content first for comprehensive validation
        content = await file.read()

        # Enhanced file validation with magic number detection
        is_valid, error_msg = validate_uploaded_file(
            content,
            file.filename or "unknown",
            file.content_type
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File validation failed: {error_msg}"
            )

        # Sanitize filename
        safe_filename = sanitize_filename(file.filename or "unknown")

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    discipline_valid, discipline_error = SecurityValidator.validate_discipline(discipline)
    if not discipline_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=discipline_error)

    mode_valid, mode_error = SecurityValidator.validate_analysis_mode(analysis_mode)
    if not mode_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=mode_error)

    strictness_valid, strictness_error = SecurityValidator.validate_strictness(strictness)
    if not strictness_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=strictness_error)
    strictness = (strictness or "standard").lower()

    # Content already read above for validation
    size_valid, size_error = SecurityValidator.validate_file_size(len(content))
    if not size_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=size_error)

    task_id = uuid.uuid4().hex
    tasks[task_id] = {
        "status": "processing",
        "filename": safe_filename,
        "timestamp": datetime.datetime.now(datetime.UTC),
        "strictness": strictness,
        "user_id": _current_user.id,  # Track user ownership
    }

    background_tasks.add_task(
        run_analysis_and_save,
        content,
        task_id,
        safe_filename,
        discipline,
        analysis_mode,
        strictness,
        analysis_service,
        _current_user.id,  # Pass user ID
    )

    return {"task_id": task_id, "status": "processing"}


# REMOVED: /submit endpoint - redundant with /analyze endpoint
# The submit endpoint was just an alias for analyze_document and has been removed
# to reduce API surface area and improve maintainability.
# Use /analyze endpoint instead.


@router.get("/status/{task_id}")
async def get_analysis_status(
    task_id: str,
    current_user: models.User = Depends(get_current_active_user),
    request_id: str = RequestId,
) -> dict[str, Any]:
    """Retrieves the status of a background analysis task (user must own the task) with request tracking."""
    log_with_request_id(
        f"Status request for task {task_id} by user {current_user.username}",
        level="info",
        user_id=current_user.id,
        task_id=task_id
    )
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check authorization - user must own the task or be admin
    if task.get("user_id") != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this task")

    current_status = task.get("status", "processing")
    if current_status == "completed":
        if not task.get("_reported_completion"):
            task["_reported_completion"] = True
            transient = dict(task)
            transient["status"] = "analyzing"
            return transient
        return dict(task)

    # Ensure progress and status_message are always returned, even if not explicitly set yet
    task.setdefault("progress", 0)
    task.setdefault("status_message", "Initializing...")
    return task


@router.get("/all-tasks")
async def get_all_tasks(_current_user: models.User = Depends(get_current_active_user)) -> dict[str, dict[str, Any]]:
    """Retrieves all current analysis tasks."""
    return tasks


@router.post("/export-pdf/{task_id}")
async def export_report_to_pdf(
    task_id: str, _current_user: models.User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """Export analysis report to PDF format."""
    from ...core.pdf_export_service import PDFExportService
    from ...core.report_generator import ReportGenerator

    task = tasks.get(task_id)
    if not task or task["status"] != "completed":
        raise HTTPException(status_code=404, detail="Completed task not found")

    # Check authorization - user must own the task or be admin
    if task.get("user_id") != _current_user.id and not _current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to export this task")

    try:
        analysis_result = task.get("result", {})
        document_name = task.get("filename", "document")

        report_html = task.get("report_html") if isinstance(task.get("report_html"), str) else None
        analysis_section = task.get("analysis") if isinstance(task.get("analysis"), dict) else None
        findings = task.get("findings") if isinstance(task.get("findings"), list) else None
        overall_score = task.get("overall_score")
        document_type = task.get("document_type")
        generated_at = task.get("generated_at")

        if report_html is None or analysis_section is None:
            report_gen = ReportGenerator()
            generated_payload = report_gen.generate_report(analysis_result=analysis_result, document_name=document_name)
            report_html = generated_payload.get("report_html")
            analysis_section = generated_payload.get("analysis")
            findings = generated_payload.get("findings", findings) or []
            overall_score = (analysis_section or {}).get("compliance_score", overall_score)
            document_type = (analysis_section or {}).get("document_type", document_type)
            generated_at = generated_payload.get("generated_at", generated_at)

            tasks[task_id]["analysis"] = analysis_section
            tasks[task_id]["findings"] = findings
            tasks[task_id]["overall_score"] = overall_score
            tasks[task_id]["document_type"] = document_type
            if report_html:
                tasks[task_id]["report_html"] = report_html
            if generated_at:
                tasks[task_id]["generated_at"] = generated_at
        else:
            findings = findings or analysis_section.get("findings", [])
            tasks[task_id]["findings"] = findings
            overall_score = overall_score if overall_score is not None else analysis_section.get("compliance_score")
            tasks[task_id]["overall_score"] = overall_score
            document_type = document_type or analysis_section.get("document_type")
            tasks[task_id]["document_type"] = document_type
            if generated_at is None:
                generated_at = datetime.datetime.now(datetime.UTC).isoformat()
                tasks[task_id]["generated_at"] = generated_at

        if not isinstance(report_html, str):
            raise ValueError("Report HTML is not available for this task.")

        pdf_service = PDFExportService()
        pdf_result = pdf_service.export_to_pdf(
            html_content=report_html,
            document_name=document_name,
            metadata={
                "Document": document_name,
                "Analysis Date": generated_at or datetime.datetime.now(datetime.UTC).isoformat(),
                "Compliance Score": overall_score if overall_score is not None else "N/A",
                "Total Findings": len(findings or []),
                "Document Type": document_type or "Unknown",
                "Discipline": (analysis_section or {}).get("discipline", "Unknown"),
            },
        )

        if not pdf_result.get("success"):
            error_message = pdf_result.get("error", "Unknown error")
            logger.error(
                "PDF export failed; returning HTML fallback",
                task_id=task_id,
                error=error_message,
            )
            return {
                "success": False,
                "task_id": task_id,
                "message": "PDF export failed. Returning HTML report instead.",
                "pdf_info": pdf_result,
                "fallback": "html",
                "report_html": report_html,
                "error": error_message,
            }

        return {
            "success": True,
            "task_id": task_id,
            "pdf_info": pdf_result,
            "message": "PDF exported successfully",
        }

    except (ImportError, ModuleNotFoundError, ValueError) as e:
        logger.exception("PDF export failed", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"PDF export failed: {e!s}") from e


@router.post("/feedback", response_model=schemas.FeedbackAnnotation, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback: schemas.FeedbackAnnotationCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Endpoint to receive and store user feedback on AI findings."""
    try:
        return await crud.create_feedback_annotation(db=db, feedback=feedback, user_id=current_user.id)
    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        logger.exception("Failed to save feedback", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save feedback: {e}"
        ) from e
