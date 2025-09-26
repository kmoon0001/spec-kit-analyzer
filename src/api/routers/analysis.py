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
<<<<<<< HEAD
from ...database import get_async_db
||||||| 278fb88
from ...database import SessionLocal
=======
from ...database import AsyncSessionLocal
>>>>>>> origin/main
from ..dependencies import get_analysis_service
from ... import crud

router = APIRouter()
logger = logging.getLogger(__name__)

tasks = {}

<<<<<<< HEAD
async def run_analysis_and_save_async(
||||||| 278fb88
def run_analysis_and_save(
=======
async def run_analysis_and_save(
>>>>>>> origin/main
    file_path: str,
    task_id: str,
    doc_name: str,
    discipline: str | None,
    analysis_mode: str,
    analysis_service: AnalysisService,
):
<<<<<<< HEAD
    """Async version of the analysis task."""
    async for db in get_async_db():
        try:
            analysis_result = analysis_service.analyze_document(
                file_path=file_path,
                discipline=discipline
||||||| 278fb88
    """Runs the analysis with semantic caching, saves the data, and generates the report."""
    db = SessionLocal()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            document_text = f.read()

        # 1. Generate embedding for the new document
        embedding_bytes = analysis_service.get_document_embedding(document_text)
        new_embedding = pickle.loads(embedding_bytes)

        # 2. Check for a semantically similar report in the cache (database)
        cached_report = crud.find_similar_report(db, new_embedding)

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
=======
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
>>>>>>> origin/main
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

<<<<<<< HEAD
def analysis_task_wrapper(*args, **kwargs):
    """Sync wrapper to run the async analysis task in a background thread."""
    asyncio.run(run_analysis_and_save_async(*args, **kwargs))
||||||| 278fb88
    except Exception as e:
        logger.error(f"Error in analysis background task: {e}", exc_info=True)
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        db.close()
        if os.path.exists(file_path):
            os.remove(file_path)
=======
    except Exception as e:
        logger.error(f"Error in analysis background task: {e}", exc_info=True)
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        await db.close()
        if os.path.exists(file_path):
            os.remove(file_path)
>>>>>>> origin/main

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
<<<<<<< HEAD
    
    return task
||||||| 278fb88
    return task
=======
    return task
>>>>>>> origin/main
