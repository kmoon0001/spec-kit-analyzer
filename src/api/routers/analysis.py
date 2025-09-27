from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.responses import HTMLResponse
import logging
import uuid
import shutil
import os
import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
import uuid

from ... import models
from ... import schemas, models, crud
from ...auth import get_current_active_user
from ...core.analysis_service import AnalysisService
from ...database import get_async_db
from ... import crud
from ...config import settings # Import settings
from ...database import SessionLocal

router = APIRouter()
logger = logging.getLogger(__name__)

analysis_service = AnalysisService()
tasks = {}

def run_analysis_and_save(
    file_path: str,
    task_id: str, 
def _calculate_compliance_score(analysis_result: Dict[str, Any]) -> str:
    base_score = 100
    if "findings" not in analysis_result or not analysis_result["findings"]:
        return str(base_score)

    score_deductions = {
        "High": 10,
        "Medium": 5,
        "Low": 2
    }

    current_score = base_score
    for finding in analysis_result["findings"]:
        risk = finding.get("risk", "Low") # Default to Low if not specified
        current_score -= score_deductions.get(risk, 0)

        if finding.get("is_disputed", False):
            current_score -= 3
        if finding.get("is_low_confidence", False):
            current_score -= 1

    return str(max(0, current_score))


async def run_analysis_and_save(
    file_path: str,
    task_id: str,
    doc_name: str,
    rubric_id: int | None,
    discipline: str | None,
    analysis_mode: str
    discipline: str | None,
    analysis_mode: str,
    analysis_service: AnalysisService,
):
    """Runs the analysis with semantic caching, saves the data, and generates the report."""
    async for db in get_async_db():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                document_text = f.read()

            # 1. Generate embedding for the new document
            embedding_bytes = analysis_service.get_document_embedding(document_text)

            # 2. Check for a semantically similar report in the cache (database)
            cached_report = await crud.find_similar_report(db, embedding_bytes)

            if cached_report:
                # --- CACHE HIT ---
                logger.info(f"Semantic cache hit for document: {doc_name}. Using cached report ID: {cached_report.id}")
                analysis_result = cached_report.analysis_result
            else:
                # --- CACHE MISS ---
                logger.info(f"Semantic cache miss for document: {doc_name}. Performing full analysis.")
                # Perform the full analysis to get the structured data
                analysis_result = analysis_service.analyzer.analyze_document(
                    document_text=document_text,
                    discipline=discipline,
                    doc_type="Unknown" # This will be replaced by the classifier
                )
    """Runs the analysis and saves the report and findings to the database."""
    db = SessionLocal()
    try:
        # Perform the analysis
        analysis_result = analysis_service.analyzer.analyze_document(
            document=open(file_path, 'r', encoding='utf-8').read(),
            discipline=discipline,
            doc_type="Unknown"
        )

        # Generate the HTML report
        report_html = analysis_service.report_generator.generate_html_report(
            analysis_result=analysis_result,
            doc_name=doc_name,
            analysis_mode=analysis_mode
        )
                report_html = analysis_service.report_generator.generate_html_report(analysis_result, doc_name, analysis_mode)

                compliance_score = _calculate_compliance_score(analysis_result)
                report_data = {
                    "document_name": doc_name,
                    "compliance_score": compliance_score,
                    "analysis_result": analysis_result,
                    "document_embedding": embedding_bytes
                }
                await crud.create_report_and_findings(db, report_data, analysis_result.get("findings", []))
        # Save the report and findings to the database
        report_data = {
            "document_name": doc_name,
            "compliance_score": analysis_service.report_generator.risk_scoring_service.calculate_compliance_score(analysis_result.get("findings", []))
        }
        crud.create_report_and_findings(db, report_data, analysis_result.get("findings", []))

        tasks[task_id] = {"status": "completed", "result": report_html}
                tasks[task_id] = {"status": "completed", "result": report_html, "compliance_score": compliance_score}

        except Exception as e:
            logger.error(f"Error during analysis for task {task_id}: {e}", exc_info=True)
            tasks[task_id] = {"status": "failed", "error": str(e)}
        finally:
            await db.close()
            db.close()
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

def analysis_task_wrapper(*args, **kwargs):
    """Sync wrapper to run the async analysis task in a background thread."""
    asyncio.run(run_analysis_and_save(*args, **kwargs))

@router.post("/analyze", status_code=202)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    discipline: str = Form("All"),
    rubric_id: int = Form(None),
    analysis_mode: str = Form("rubric"),
    current_user: models.User = Depends(get_current_active_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    task_id = str(uuid.uuid4())
    temp_file_path = f"temp_{task_id}_{file.filename}"
    upload_dir = settings.temp_upload_dir # Use settings.temp_upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    temp_file_path = os.path.join(upload_dir, f"temp_{task_id}_{file.filename}")
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(
        run_analysis_and_save, temp_file_path, task_id, file.filename, rubric_id, discipline, analysis_mode
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
        return {"status": "completed", "compliance_score": task.get("compliance_score", "N/A"), "report_url": f"/reports/{task_id}"}

    return task
        return HTMLResponse(content=task["result"])
    else:
        return task
