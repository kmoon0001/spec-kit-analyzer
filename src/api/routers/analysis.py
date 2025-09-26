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
from ...database import AsyncSessionLocal
from ..dependencies import get_analysis_service

router = APIRouter()
logger = logging.getLogger(__name__)

tasks = {}

async def run_analysis_and_save(
    file_path: str,
    task_id: str,
    doc_name: str,
    discipline: str | None,
    analysis_mode: str,
    analysis_service: AnalysisService,
):
    """Runs the analysis with semantic caching, saves the data, and generates the report."""
    db = AsyncSessionLocal()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            document_text = f.read()

        # NOTE: The get_document_embedding method seems to be missing from AnalysisService.
        # This will likely cause an error, but fixing the DB access first.
        embedding_bytes = analysis_service.get_document_embedding(document_text)
        new_embedding = pickle.loads(embedding_bytes)

        # 2. Check for a semantically similar report in the cache (database)
        cached_report = await crud.find_similar_report(db, new_embedding)

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

            # Save the new analysis result and its embedding to the database
            report_data = {
                "document_name": doc_name,
                "compliance_score": "N/A", # Scoring service was removed
                "analysis_result": analysis_result,
                "document_embedding": embedding_bytes
            }
            await crud.create_report_and_findings(db, report_data, analysis_result.get("findings", []))

        # 3. Generate the HTML report (either from cached or new data)
        report_html = analysis_service.report_generator.generate_html_report(
            analysis_result=analysis_result,
            doc_name=doc_name,
            analysis_mode=analysis_mode
        )

        tasks[task_id] = {"status": "completed", "result": report_html}

    except Exception as e:
        logger.error(f"Error in analysis background task: {e}", exc_info=True)
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        await db.close()
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

@router.get("/tasks/{task_id}", response_model=schemas.TaskStatus, responses={200: {"content": {"text/html": {}}}})
async def get_task_status(task_id: str, current_user: models.User = Depends(get_current_active_user)):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] == "completed":
        return HTMLResponse(content=task["result"])
    return task