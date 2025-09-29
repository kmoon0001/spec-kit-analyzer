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
from ...database import crud, schemas
from ...database.database import get_async_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])

tasks: Dict[str, Dict[str, Any]] = {}


async def run_analysis_and_save(
    file_path: str,
    task_id: str,
    original_filename: str,
    discipline: str,
    analysis_mode: str,
    analysis_service: AnalysisService,
    user_id: int,
) -> None:
    """
    This function runs in the background. It performs the analysis and then
    saves the resulting report to the database.
    """
    db_session_generator = get_async_db()
    db = await db_session_generator.__anext__()
    try:
        result = await analysis_service.analyze_document(
            file_path=file_path,
            discipline=discipline,
            analysis_mode=analysis_mode,
        )

        # Save the report to the database
        report_create = schemas.ReportCreate(
            document_name=original_filename,
            # Extract score from analysis, default to 0 if not found
            compliance_score=result.get("analysis", {}).get("overall_confidence", 0.0) * 100,
            analysis_result=result.get("analysis", {}),
        )
        db_report = await crud.create_report(db=db, report=report_create)
        logger.info(f"Saved analysis report with ID: {db_report.id}")

        tasks[task_id] = {
            "status": "completed",
            "result": {**result, "report_id": db_report.id}, # Add report_id to the result
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
        await db.close()
        Path(file_path).unlink(missing_ok=True)


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
    temp_dir = Path(settings.temp_upload_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    task_id = uuid.uuid4().hex
    destination = temp_dir / f"{task_id}_{file.filename}"

    content = await file.read()
    destination.write_bytes(content)

    tasks[task_id] = {"status": "processing", "filename": file.filename}

    background_tasks.add_task(
        run_analysis_and_save,
        file_path=str(destination),
        task_id=task_id,
        original_filename=file.filename,
        discipline=discipline,
        analysis_mode=analysis_mode,
        analysis_service=analysis_service,
        user_id=current_user.id,
    )

    return {"task_id": task_id, "status": "processing"}
