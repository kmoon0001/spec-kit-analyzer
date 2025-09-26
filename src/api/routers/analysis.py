import logging
import uuid
import shutil
import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from ... import schemas, models, crud
from ...auth import get_current_active_user
from ...core.analysis_service import AnalysisService
from ...database import SessionLocal
from ..dependencies import get_analysis_service

router = APIRouter()
logger = logging.getLogger(__name__)

tasks = {}

def run_analysis_and_save(
    file_path: str,
    task_id: str,
    doc_name: str,
    discipline: str | None,
    analysis_mode: str,
    analysis_service: AnalysisService,
):
    """Runs the analysis, saves the data, and generates the report."""
    db = SessionLocal()
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
            "compliance_score": "N/A", # Scoring service was removed
            "analysis_result": analysis_result,
            "document_embedding": embedding_bytes
        }
        crud.create_report(db, report_data, report_html)

        tasks[task_id] = {"status": "complete", "result": report_html}

    except Exception as e:
        logger.error(f"Error during analysis for task {task_id}: {e}", exc_info=True)
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        # Correctly remove the temporary file.
        if os.path.exists(file_path):
            os.remove(file_path)
        db.close()

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
    os.makedirs(upload_dir, exist_ok=True)  # Ensure the directory exists
    temp_file_path = os.path.join(upload_dir, f"temp_{task_id}_{file.filename}")
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(
        run_analysis_and_save, temp_file_path, task_id, file.filename, discipline, analysis_mode, analysis_service
    )
    tasks[task_id] = {"status": "processing"}

    return {"task_id": task_id, "status": "processing"}


@router.get("/results/{task_id}", response_model=schemas.AnalysisResult)
def get_analysis_results(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task