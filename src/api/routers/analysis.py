from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.responses import HTMLResponse
import shutil
import os
import uuid
import logging
import pickle

from ... import schemas, models, crud
from ...auth import get_current_active_user
from ...core.analysis_service import AnalysisService
from ...database import SessionLocal
from ..dependencies import get_analysis_service

router = APIRouter()
logger = logging.getLogger(__name__)

tasks: dict = {}

def run_analysis_and_save(
    file_path: str,
    task_id: str,
    doc_name: str,
    discipline: str | None,
    analysis_mode: str,
    analysis_service_instance: AnalysisService,
):
    """Runs the analysis, saves the data, and generates the report."""
    db = SessionLocal()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            document_text = f.read()

        embedding_bytes = analysis_service_instance.get_document_embedding(document_text)
        new_embedding = pickle.loads(embedding_bytes)

        cached_report = crud.find_similar_report(db, new_embedding)

        if cached_report:
            logger.info(f"Semantic cache hit for document: {doc_name}.")
            analysis_result = cached_report.analysis_result
        else:
            logger.info(f"Semantic cache miss for document: {doc_name}. Performing full analysis.")
            analysis_result = analysis_service_instance.analyzer.analyze_document(
                document_text=document_text,
                discipline=str(discipline),
                doc_type="Unknown",
            )
            report_data = {
                "document_name": doc_name,
                "compliance_score": analysis_service_instance.report_generator.risk_scoring_service.calculate_compliance_score(
                    analysis_result.get("findings", [])
                ),
                "analysis_result": analysis_result,
                "document_embedding": embedding_bytes,
            }
            crud.create_report_and_findings(db, report_data, analysis_result.get("findings", []))

        report_html = analysis_service_instance.report_generator.generate_html_report(
            analysis_result=analysis_result,
            doc_name=doc_name,
            analysis_mode=analysis_mode,
        )
        tasks[task_id] = {"status": "completed", "result": report_html}

    except Exception as e:
        logger.error(f"Error in analysis background task: {e}", exc_info=True)
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        db.close()
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/analyze", response_model=schemas.AnalysisResult, status_code=202)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    discipline: str = Form("All"),
    analysis_mode: str = Form("rubric"),
    current_user: models.User = Depends(get_current_active_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    task_id = str(uuid.uuid4())
    doc_name = file.filename if file.filename else "uploaded_file.tmp"
    temp_file_path = f"temp_{task_id}_{doc_name}"

    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Convert the file to text before passing to the background task
    with open(temp_file_path, "r", encoding="utf-8", errors="ignore") as f:
        text_content = f.read()

    with open(temp_file_path, "w", encoding="utf-8") as f:
        f.write(text_content)

    background_tasks.add_task(
        run_analysis_and_save,
        temp_file_path,
        task_id,
        doc_name,
        discipline,
        analysis_mode,
        analysis_service,
    )
    tasks[task_id] = {"status": "processing"}
    return {"task_id": task_id, "status": "processing"}

@router.get("/tasks/{task_id}", response_model=schemas.TaskStatus, responses={200: {"content": {"text/html": {}}}})
async def get_task_status(
    task_id: str, current_user: models.User = Depends(get_current_active_user)
):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] == "completed":
        return HTMLResponse(content=task["result"])
    return task