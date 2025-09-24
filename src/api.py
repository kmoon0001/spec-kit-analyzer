from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import shutil
import os
import uuid
from src.core.analysis_service import AnalysisService

# Add metadata for the API
app = FastAPI(
    title="Clinical Compliance Analyzer API",
    description="API for analyzing clinical documents for compliance.",
    version="1.0.0",
)

analysis_service = AnalysisService()
tasks = {}

class TaskStatus(BaseModel):
    task_id: str
    status: str
    error: str | None = None

class AnalysisResult(BaseModel):
    task_id: str
    status: str

def run_analysis(file_path: str, task_id: str, rubric_id: int | None, discipline: str | None):
    try:
        report_html = analysis_service.analyze_document(file_path, rubric_id=rubric_id, discipline=discipline)
        tasks[task_id] = {"status": "completed", "result": report_html}
    except Exception as e:
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/analyze", response_model=AnalysisResult, status_code=202)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    discipline: str = Form("All"),
    rubric_id: int = Form(None),
):
    """
    Starts an asynchronous analysis of the uploaded document.

    - **file**: The clinical document to analyze.
    - **discipline**: The discipline to analyze for (e.g., 'PT', 'OT').
    - **rubric_id**: The ID of the rubric to use for analysis.
    - Returns a task ID to check the analysis status.
    """
    task_id = str(uuid.uuid4())
    temp_file_path = f"temp_{task_id}_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(run_analysis, temp_file_path, task_id, rubric_id, discipline)
    tasks[task_id] = {"status": "processing"}

    return {"task_id": task_id, "status": "processing"}

@app.get("/tasks/{task_id}", response_model=TaskStatus, responses={200: {"content": {"text/html": {}}}})
async def get_task_status(task_id: str):
    """
    Retrieves the status or result of an analysis task.

    - **task_id**: The ID of the task to check.
    - If the task is **completed**, it returns the HTML compliance report.
    - If the task is **processing** or **failed**, it returns the status.
    """
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] == "completed":
        return HTMLResponse(content=task["result"])
    else:
        return task
