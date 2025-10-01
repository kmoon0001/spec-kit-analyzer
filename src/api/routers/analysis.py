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
    current_user=Depends(get_current_active_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> Dict[str, str]:
    if analysis_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analysis service is not ready yet.",
        )

    settings = get_settings()
    temp_dir = Path(settings.paths.temp_upload_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    task_id = uuid.uuid4().hex
    destination = temp_dir / f"{task_id}_{file.filename}"

    content = await file.read()
    destination.write_bytes(content)

    tasks[task_id] = {"status": "processing", "filename": file.filename}

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
    task_id: str, current_user=Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Retrieves the status of a background analysis task.
    """
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] == "completed":
        # Pop the result once it's retrieved to avoid memory bloat
        return tasks.pop(task_id)

    return task
