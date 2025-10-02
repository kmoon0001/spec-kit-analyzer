"""
Analysis API router for document compliance analysis.

Provides endpoints for uploading documents, running compliance analysis,
and retrieving analysis results.
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from ...auth import get_current_active_user
from ...config import get_settings
from ...core.analysis_service import AnalysisService
from ...core.security_validator import SecurityValidator
from ..dependencies import get_analysis_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])

tasks: Dict[str, Dict[str, Any]] = {}


def run_analysis_and_save(
    file_path: str,
    task_id: str,
    original_filename: str,
    discipline: str,
    analysis_mode: str,
    analysis_service: AnalysisService,
) -> None:
    """
    Background task to run document analysis and save results.

    Args:
        file_path: Path to uploaded document
        task_id: Unique task identifier
        original_filename: Original filename from upload
        discipline: Therapy discipline
        analysis_mode: Analysis mode to use
        analysis_service: Analysis service instance
    """
    async def _job() -> None:
        try:
            result = await analysis_service.analyze_document(
                file_path=file_path,
                discipline=discipline,
                analysis_mode=analysis_mode,
            )
            tasks[task_id] = {
                "status": "completed",
                "result": result,
                "filename": original_filename,
            }
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Analysis task %s failed", task_id)
            tasks[task_id] = {
                "status": "failed",
                "error": str(exc),
                "filename": original_filename,
            }
        finally:
            Path(file_path).unlink(missing_ok=True)

    asyncio.run(_job())


@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    discipline: str = Form("pt"),
    analysis_mode: str = Form("rubric"),
    _current_user=Depends(get_current_active_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> Dict[str, str]:
    """
    Upload and analyze a clinical document for compliance.

    Args:
        background_tasks: FastAPI background tasks manager
        file: Uploaded document file
        discipline: Therapy discipline (pt, ot, slp)
        analysis_mode: Analysis mode (rubric, checklist, hybrid)
        _current_user: Authenticated user (for authorization)
        analysis_service: Analysis service dependency

    Returns:
        Dict with task_id and status

    Raises:
        HTTPException: For validation errors or service unavailability
    """
    if analysis_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analysis service is not ready yet.",
        )

    # Security: Validate filename
    is_valid, error_msg = SecurityValidator.validate_filename(file.filename or "")
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    settings = get_settings()
    temp_dir = Path(settings.paths.temp_upload_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    task_id = uuid.uuid4().hex
    # Security: Sanitize filename to prevent path traversal
    safe_filename = SecurityValidator.sanitize_filename(file.filename or "")
    destination = temp_dir / f"{task_id}_{safe_filename}"

    content = await file.read()
    
    # Security: Validate file size
    is_valid, error_msg = SecurityValidator.validate_file_size(len(content))
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=error_msg,
        )
    
    destination.write_bytes(content)

    # Security: Validate discipline parameter
    is_valid, error_msg = SecurityValidator.validate_discipline(discipline)
    if not is_valid:
        destination.unlink(missing_ok=True)  # Clean up uploaded file
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )
    
    # Security: Validate analysis_mode parameter
    is_valid, error_msg = SecurityValidator.validate_analysis_mode(analysis_mode)
    if not is_valid:
        destination.unlink(missing_ok=True)  # Clean up uploaded file
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    tasks[task_id] = {"status": "processing", "filename": safe_filename}

    background_tasks.add_task(
        run_analysis_and_save,
        str(destination),
        task_id,
        file.filename,
        discipline,
        analysis_mode,
        analysis_service,
    )

    return {"task_id": task_id, "status": "processing"}


@router.get("/status/{task_id}")
async def get_analysis_status(
    task_id: str, _current_user=Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Retrieves the status of a background analysis task.

    Args:
        task_id: Unique task identifier
        _current_user: Authenticated user (for authorization)

    Returns:
        Dict with task status and results

    Raises:
        HTTPException: If task not found
    """
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] == "completed":
        # Pop the result once it's retrieved to avoid memory bloat
        return tasks.pop(task_id)

    return task
