import logging
import uuid
import shutil
import os
import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse

from ... import schemas, models
from ...auth import get_current_active_user
from ...core.analysis_service import AnalysisService
from ...database import get_async_db
from ..dependencies import get_analysis_service
from ... import crud

router = APIRouter()
logger = logging.getLogger(__name__)

tasks = {}

async def run_analysis_and_save_async(
    file_path: str,
    task_id: str,
    doc_name: str,
    discipline: str | None,
    analysis_mode: str,
    analysis_service: AnalysisService,
):
    """Async version of the analysis task."""
    async for db in get_async_db():
        try:
            analysis_result = analysis_service.analyze_document(
                file_path=file_path,
                discipline=discipline
            )

            with open(file_path, "r", encoding="utf-8") as f:
                document_text = f.read()

            embedding_bytes = analysis_service.get_document_embedding(document_text)

            report_html = analysis_service.report_generator.generate_html_report(analysis_result, doc_name, analysis_mode)

            report_data = {
                "document_name": doc_name,
                "compliance_score": "N/A",
                "analysis_result": analysis_result,
                "document_embedding": embedding_bytes
            }
            await crud.create_report_and_findings(db, report_data, analysis_result.get("findings", []))

            tasks[task_id] = {"status": "completed", "result": report_html}

        except Exception as e:
            logger.error(f"Error during analysis for task {task_id}: {e}", exc_info=True)
            tasks[task_id] = {"status": "failed", "error": str(e)}
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

def analysis_task_wrapper(*args, **kwargs):
    """Sync wrapper to run the async analysis task in a background thread."""
    asyncio.run(run_analysis_and_save_async(*args, **kwargs))

@router.post("/analyze", status_code=202)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    discipline: str = Form("All"),
    analysis_mode: str = Form("rubric"),
    current_user: models.User = Depends(get_current_active_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    task_id = str(uuid.uuid4())
    upload_dir = "tmp/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    temp_file_path = os.path.join(upload_dir, f"temp_{task_id}_{file.filename}")
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(
        analysis_task_wrapper, temp_file_path, task_id, file.filename, discipline, analysis_mode, analysis_service
    )
    tasks[task_id] = {"status": "processing"}

    return {"task_id": task_id, "status": "processing"}

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] == "completed":
        return HTMLResponse(content=task["result"])
    
    return task