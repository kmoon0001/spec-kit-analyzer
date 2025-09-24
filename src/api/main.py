import shutil
import os
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from src.core.analysis_service import AnalysisService

# Configure logging
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    On startup, it initializes the AnalysisService and stores it in the app state.
    """
    logger.info("Application startup...")
    # Initialize the AnalysisService. This will trigger model loading and index building.
    # This happens in the background after the server has started.
    app.state.analysis_service = AnalysisService()
    app.state.tasks = {}
    logger.info("AnalysisService initialized and ready.")
    yield
    # Cleanup on shutdown (if any)
    logger.info("Application shutdown.")

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "Backend for Therapy Compliance Analyzer"}

def run_analysis(file_path: str, task_id: str, analysis_service: AnalysisService, tasks: dict):
    """
    The actual analysis function that runs in a background thread.
    """
    try:
        report_html = analysis_service.analyze_document(file_path)
        tasks[task_id] = {"status": "completed", "result": report_html}
    except Exception as e:
        logger.error(f"Analysis for task {task_id} failed: {e}", exc_info=True)
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/analyze")
async def analyze_document(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    task_id = str(uuid.uuid4())

    # Use a temporary directory to avoid filename conflicts
    temp_dir = "temp_files"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"{task_id}_{file.filename}")

    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Get the services from the application state
    analysis_service = request.app.state.analysis_service
    tasks = request.app.state.tasks

    # Add the analysis to the background
    background_tasks.add_task(run_analysis, temp_file_path, task_id, analysis_service, tasks)
    tasks[task_id] = {"status": "processing"}

    return JSONResponse(status_code=202, content={"task_id": task_id, "status": "processing"})

@app.get("/tasks/{task_id}")
async def get_task_status(request: Request, task_id: str):
    tasks = request.app.state.tasks
    task = tasks.get(task_id)

    if not task:
        return JSONResponse(status_code=404, content={"error": "Task not found"})

    if task["status"] == "completed":
        return HTMLResponse(content=task["result"])
    else:
        return JSONResponse(content=task)
