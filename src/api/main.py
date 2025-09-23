from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
import shutil
import os
import uuid
from src.core.analysis_service import AnalysisService

app = FastAPI()
analysis_service = AnalysisService()
tasks = {}


@app.get("/")
def read_root():
    return {"message": "Backend for Therapy Compliance Analyzer"}


def run_analysis(file_path: str, task_id: str):
    try:
        report_html = analysis_service.analyze_document(file_path)
        tasks[task_id] = {"status": "completed", "result": report_html}
    except Exception as e:
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        # Clean up the temporary file
        os.remove(file_path)

@app.post("/analyze")
async def analyze_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    task_id = str(uuid.uuid4())
    temp_file_path = f"temp_{task_id}_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(run_analysis, temp_file_path, task_id)
    tasks[task_id] = {"status": "processing"}

    return JSONResponse(status_code=202, content={"task_id": task_id, "status": "processing"})

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        return JSONResponse(status_code=404, content={"error": "Task not found"})

    if task["status"] == "completed":
        return HTMLResponse(content=task["result"])
    else:
        return JSONResponse(content=task)
