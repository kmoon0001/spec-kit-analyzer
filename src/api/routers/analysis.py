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
from ...database import crud, models, schemas
from ...database.database import get_async_db
from ..dependencies import get_analysis_service

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])

tasks: dict[str, dict[str, Any]] = {}

uploaded_documents: dict[str, dict[str, Any]] = {}
legacy_router = APIRouter(tags=['analysis-legacy'])


class LegacyAnalysisRequest(BaseModel):
    document_id: str
    rubric_id: str
    analysis_type: str = 'comprehensive'
    discipline: str | None = None



def run_analysis_and_save(
    file_content: bytes,
    task_id: str,
    original_filename: str,
    discipline: str,
    analysis_mode: str,
    analysis_service: AnalysisService,
) -> None:
    """Background task to run document analysis on in-memory content and save results."""

    def _update_progress(percentage: int, message: str) -> None:
        tasks[task_id]["progress"] = percentage
        tasks[task_id]["status_message"] = message
        if percentage >= 100:
            tasks[task_id]["status"] = "completed"
        elif percentage >= 60:
            tasks[task_id]["status"] = "analyzing"
        else:
            tasks[task_id]["status"] = "processing"
        logger.info("Task %s progress: %d%% - %s", task_id, percentage, message)

    async def _async_analysis():
        try:
            logger.info("Starting analysis for task %s", task_id)
            _update_progress(0, "Analysis started.")
            result = await analysis_service.analyze_document(
                file_content=file_content,
                original_filename=original_filename,
                discipline=discipline,
                analysis_mode=analysis_mode,
                progress_callback=_update_progress,
            )
            analysis_payload = result if isinstance(result, dict) else {}
            analysis_details = {}
            if isinstance(analysis_payload, dict):
                candidate = analysis_payload.get("analysis")
                if isinstance(candidate, dict):
                    analysis_details = candidate

            findings = analysis_details.get("findings", []) if isinstance(analysis_details, dict) else []
            compliance_score = analysis_details.get("compliance_score") if isinstance(analysis_details, dict) else None
            document_type = analysis_details.get("document_type") if isinstance(analysis_details, dict) else None
            report_html = analysis_payload.get("report_html") if isinstance(analysis_payload, dict) else None

            task_entry = tasks[task_id]
            task_entry["status"] = "analyzing"
            task_entry["status_message"] = "Finalizing analysis results..."
            task_entry["progress"] = max(task_entry.get("progress", 90), 95)
            await asyncio.sleep(0.2)
            task_entry.update({
                "status": "completed",
                "result": result,
                "filename": original_filename,
                "timestamp": datetime.datetime.now(datetime.UTC),
                "progress": 100,
                "status_message": "Analysis complete.",
                "analysis": analysis_details,
                "findings": findings,
                "overall_score": compliance_score,
                "document_type": document_type,
                "report_html": report_html,
            })
            logger.info("Analysis completed for task %s", task_id)
        except (FileNotFoundError, PermissionError, OSError) as exc:
            logger.exception("Analysis task failed", task_id=task_id, error=str(exc))
            tasks[task_id] = {
                "status": "failed",
                "error": str(exc),
                "filename": original_filename,
                "timestamp": datetime.datetime.now(datetime.UTC),
                "progress": 0,
                "status_message": f"Analysis failed: {exc}",
            }

    # Run the async function in a new event loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_async_analysis())
    finally:
        loop.close()


@legacy_router.post("/upload-document")
async def legacy_upload_document(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Legacy-friendly endpoint to upload documents prior to analysis."""
    try:
        safe_filename = SecurityValidator.validate_and_sanitize_filename(file.filename or "")
    except ValueError as exc:  # pragma: no cover - defensive sanitization
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    content = await file.read()
    is_valid_size, error = SecurityValidator.validate_file_size(len(content))
    if not is_valid_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error or "Invalid file size")

    document_id = uuid.uuid4().hex
    uploaded_documents[document_id] = {
        "filename": safe_filename,
        "content_bytes": content,
        "content_text": content.decode("utf-8", errors="ignore"),
        "uploaded_at": datetime.datetime.now(datetime.UTC),
        "owner_id": current_user.id,
    }

    logger.info("Legacy upload stored", document_id=document_id, filename=safe_filename)
    return {"status": "success", "document_id": document_id, "filename": safe_filename}


@legacy_router.get("/documents/{document_id}")
async def legacy_get_document(
    document_id: str, current_user: models.User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """Retrieve an uploaded document for compatibility clients."""
    document = uploaded_documents.get(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if document["owner_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this document.")

    return {
        "id": document_id,
        "filename": document["filename"],
        "content": document["content_text"],
        "uploaded_at": document["uploaded_at"].isoformat(),
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

    document = uploaded_documents.get(request.document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if document["owner_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to analyze this document."
        )

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
        "filename": document["filename"],
        "timestamp": datetime.datetime.now(datetime.UTC),
    }

    background_tasks.add_task(
        run_analysis_and_save,
        document["content_bytes"],
        task_id,
        document["filename"],
        discipline,
        analysis_mode,
        analysis_service,
    )

    logger.info("Legacy analysis started", document_id=request.document_id, task_id=task_id)
    return {"status": "started", "task_id": task_id}


@legacy_router.get("/analysis-status/{task_id}")
async def legacy_get_analysis_status(
    task_id: str, current_user: models.User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """Expose task status without the /analysis prefix for older clients."""
    return await get_analysis_status(task_id, current_user)


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
    _current_user: models.User = Depends(get_current_active_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> dict[str, str]:
    """Upload and analyze a clinical document for compliance from in-memory content."""
    if analysis_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Analysis service is not ready yet."
        )

    safe_filename = SecurityValidator.validate_and_sanitize_filename(file.filename or "")
    SecurityValidator.validate_discipline(discipline)
    SecurityValidator.validate_analysis_mode(analysis_mode)

    content = await file.read()
    SecurityValidator.validate_file_size(len(content))

    task_id = uuid.uuid4().hex
    tasks[task_id] = {
        "status": "processing",
        "filename": safe_filename,
        "timestamp": datetime.datetime.now(datetime.UTC),
    }

    background_tasks.add_task(
        run_analysis_and_save, content, task_id, safe_filename, discipline, analysis_mode, analysis_service
    )

    return {"task_id": task_id, "status": "processing"}


@router.post("/submit", status_code=status.HTTP_202_ACCEPTED)
async def submit_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    discipline: str = Form("pt"),
    analysis_mode: str = Form("rubric"),
    _current_user: models.User = Depends(get_current_active_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> dict[str, str]:
    """Submit document for compliance analysis (alias for analyze_document for GUI compatibility)."""
    return await analyze_document(background_tasks, file, discipline, analysis_mode, _current_user, analysis_service)


@router.get("/status/{task_id}")
async def get_analysis_status(
    task_id: str, _current_user: models.User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """Retrieves the status of a background analysis task."""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

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


