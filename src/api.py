from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import shutil
import os
import uuid
from src.core.analysis_service import AnalysisService
from src.config import settings
from src.auth import create_access_token, get_current_user, Token

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

def run_analysis(file_path: str, task_id: str, rubric_id: int | None, discipline: str | None, analysis_mode: str):
    try:
        report_html = analysis_service.analyze_document(file_path, rubric_id=rubric_id, discipline=discipline, analysis_mode=analysis_mode)
        tasks[task_id] = {"status": "completed", "result": report_html}
    except Exception as e:
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # In a real application, you would validate the username and password against a database
    if form_data.username == "testuser" and form_data.password == "testpassword":
        access_token = create_access_token(data={"sub": form_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Incorrect username or password")

@app.post("/analyze", response_model=AnalysisResult, status_code=202)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    discipline: str = Form("All"),
    rubric_id: int = Form(None),
    analysis_mode: str = Form("rubric"),
    current_user: str = Depends(get_current_user),
):
    """
    Starts an asynchronous analysis of the uploaded document.

    - **file**: The clinical document to analyze.
    - **discipline**: The discipline to analyze for (e.g., 'PT', 'OT').
    - **rubric_id**: The ID of the rubric to use for analysis.
    - **analysis_mode**: The analysis mode ('rubric', 'llm_only', or 'hybrid').
    - Returns a task ID to check the analysis status.
    """
    task_id = str(uuid.uuid4())

    # Sanitize the filename to prevent directory traversal attacks
    sanitized_filename = os.path.basename(file.filename)
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    temp_file_path = os.path.join(temp_dir, f"{task_id}_{sanitized_filename}")

    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(run_analysis, temp_file_path, task_id, rubric_id, discipline, analysis_mode)
    tasks[task_id] = {"status": "processing"}

    return {"task_id": task_id, "status": "processing"}

@app.get("/tasks/{task_id}", response_model=TaskStatus, responses={200: {"content": {"text/html": {}}}})
async def get_task_status(task_id: str, current_user: str = Depends(get_current_user)):
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
