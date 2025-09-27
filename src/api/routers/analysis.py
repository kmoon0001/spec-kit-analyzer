`python
import asyncio
import logging
import os
import shutil
import uuid
from typing import Dict, Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import HTMLResponse

from ... import crud, models, schemas
from ...auth import get_current_active_user
from ...core.analysis_service import AnalysisService
from ...database import get_async_db

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory store for task statuses. In a production scenario, this would be a more persistent store like Redis.
tasks = {}


# Dependency to get a singleton instance of the analysis service
def get_analysis_service():
    return AnalysisService()


def _calculate_compliance_score(analysis_result: Dict[str, Any]) -> str:
    """Calculates a numeric compliance score from analysis findings."""
    base_score = 100
    if "findings" not in analysis_result or not analysis_result["findings"]:
        return str(base_score)

    score_deductions = {"High": 10, "Medium": 5, "Low": 2}
    current_score = base_score
    for finding in analysis_result["findings"]:
        risk = finding.get("risk", "Low")
        current_score -= score_deductions.get(risk, 0)
    return str(max(0, current_score))


async def run_analysis_and_save(
        file_path: str,
        task_id: str,
        doc_name: str,
        user_id: int,
        analysis_service: AnalysisService,
):
    """
    A background task that runs the analysis, saves the report, and cleans up.
    """
    db_session_gen = get_async_db()
    db = await anext(db_session_gen)
    try:
        logger.info(f"Starting analysis for task {task_id} on file {doc_name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            document_text = f.read()

        # Perform the analysis
        analysis_result = analysis_service.analyzer.analyze_document(
            document_text=document_text,
            discipline="PT",  # Placeholder, consider passing from request
            doc_type="Unknown",  # Placeholder, to be replaced by classifier
        )

        # Generate report and score
        report_html = analysis_service.report_generator.generate_html_report(
            analysis_result, doc_name, "rubric"
        )
        compliance_score = _calculate_compliance_score(analysis_result)

        # Get document embedding for semantic caching
        embedding_bytes = analysis_service.get_document_embedding(document_text)

        # Create report record in the database
        report_data = schemas.ReportCreate(
            document_name=doc_name,
            compliance_score=compliance_score,
            analysis_result=analysis_result,
            document_embedding=embedding_bytes,
            owner_id=user_id,
        )
        await crud.create_report_and_findings(
            db=db,
            report_data=report_data,
            findings_data=analysis_result.get("findings", []),
        )

        logger.info(f"Analysis for task {task_id} completed successfully.")
        tasks[task_id] = {
            "status": "completed",
            "result": report_html,
            "compliance_score": compliance_score,
        }

    except Exception as e:
        logger.error(f"Error during analysis for task {task_id}: {e}", exc_info=True)
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
        # Close the database session
        await db.close()


@router.post("/analyze", status_code=202, response_model=schemas.TaskStatus)
async def analyze_document(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        discipline: str = Form("All"),
        analysis_mode: str = Form("rubric"),
        current_user: models.User = Depends(get_current_active_user),
        analysis_service: AnalysisService = Depends(get_analysis_service),
):
    """
    Accepts a document, saves it temporarily, and starts a background task for analysis.
    """
    task_id = str(uuid.uuid4())
    upload_dir = "temp_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    temp_file_path = os.path.join(upload_dir, f"temp_{task_id}_{file.filename}")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to process uploaded file.")

    background_tasks.add_task(
        run_analysis_and_save,
        file_path=temp_file_path,
        task_id=task_id,
        doc_name=file.filename,
        user_id=current_user.id,
        analysis_service=analysis_service,
    )

    tasks[task_id] = {"status": "processing"}
    return {"task_id": task_id, "status": "processing"}


@router.get("/tasks/{task_id}", response_model=schemas.TaskStatus)
async def get_task_status(task_id: str):
    """
    Retrieves the status of an analysis task.
    """
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/reports/{task_id}", response_class=HTMLResponse)
async def get_report(task_id: str):
    """
    Retrieves the HTML report for a completed task.
    """
    task = tasks.get(task_id)
    if not task or task.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Report not found or not ready.")
    return HTMLResponse(content=task["result"])


# Helper for async generator dependency
from typing import AsyncGenerator


async def anext(gen: AsyncGenerator):
    return await gen.__anext__()


`