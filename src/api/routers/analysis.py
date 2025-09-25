from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.responses import HTMLResponse
import shutil
import os
import uuid

from ... import schemas, models, crud
from ...auth import get_current_active_user
from ...core.analysis_service import AnalysisService
from ...database import SessionLocal

router = APIRouter()

analysis_service = AnalysisService()
tasks = {}

def run_analysis_and_save(
    file_path: str, 
    task_id: str, 
    doc_name: str,
    rubric_id: int | None, 
    discipline: str | None, 
    analysis_mode: str
):
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

        # Save the report and findings to the database
        report_data = {
            "document_name": doc_name,
            "compliance_score": analysis_service.report_generator.risk_scoring_service.calculate_compliance_score(analysis_result.get("findings", []))
        }
        crud.create_report_and_findings(db, report_data, analysis_result.get("findings", []))

        tasks[task_id] = {"status": "completed", "result": report_html}

    except Exception as e:
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        db.close()
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/analyze", response_model=schemas.AnalysisResult, status_code=202)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    discipline: str = Form("All"),
    rubric_id: int = Form(None),
    analysis_mode: str = Form("rubric"),
    current_user: models.User = Depends(get_current_active_user),
):
    task_id = str(uuid.uuid4())
    temp_file_path = f"temp_{task_id}_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(
        run_analysis_and_save, temp_file_path, task_id, file.filename, rubric_id, discipline, analysis_mode
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
    else:
        return task
