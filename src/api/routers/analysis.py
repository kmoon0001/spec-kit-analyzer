import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from ...auth import get_current_active_user
from ...config import get_settings
from ...core.services import AnalysisService
from ..dependencies import get_analysis_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])

tasks: Dict[str, Dict[str, Any]] = {}


def run_analysis_and_save(
    file_path: str,
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

    asyncio.create_task(_job())

@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_document(
    file: UploadFile = File(...),
    discipline: str = Form("pt"),
    analysis_mode: str = Form("rubric"),
    current_user=Depends(get_current_active_user),
    analysis_service=Depends(get_analysis_service),
) -> Dict[str, str]:
    """
    Accepts a document for analysis, creates a task, and starts it in the background.
    """
    if not analysis_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "service_unavailable", "message": "Analysis service is not available."},
        )

    settings = get_settings()
    temp_dir = Path(settings.temp_upload_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    task_id = uuid.uuid4().hex
    destination = temp_dir / f"{task_id}_{file.filename}"
    content = await file.read()
    destination.write_bytes(content)

    task = await task_manager.create_task(task_id=task_id, filename=file.filename)

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


@router.websocket("/ws/tasks/{task_id}")
async def websocket_task_status(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint to provide real-time status updates for an analysis task.
    """
    await websocket.accept()
    task = await task_manager.get_task(task_id)

    if not task:
        await websocket.send_json({"status": "failed", "error": "Task not found."})
        await websocket.close()
        return

    # If the task is already finished, send the final state and close.
    if task.status in ["completed", "failed"]:
        final_state = {"status": task.status}
        if task.result:
            final_state["result"] = task.result
        if task.error:
            final_state["error"] = task.error
        await websocket.send_json(final_state)
        await websocket.close()
        return

    # Subscribe to updates for the ongoing task
    queue = task.subscribe()
    try:
        while True:
            update = await queue.get()
            if update is None:  # Sentinel value indicating task completion
                break
            await websocket.send_json(update)
        await websocket.close()
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for task %s", task_id)
    finally:
        task.unsubscribe(queue)
        # Optionally, clean up the task from the manager once all subscribers are gone
        # or after a certain period. For now, we leave it for potential result retrieval.