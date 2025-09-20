"""
FastAPI application for the LLM Orchestration Framework.

This module defines the RESTful API endpoints to interact with the clinical
analysis workflows. It uses FastAPI to create a robust and well-documented API
that allows other services to consume the AI capabilities of this framework.

The API provides endpoints for:
- Submitting text for analysis (`/analyze`).
- Asking questions against the knowledge base (`/ask`).
- Checking the status and retrieving the results of a task (`/tasks/{task_id}`).
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult
from typing import Dict

from .celery_app import run_workflow_task

# Initialize the FastAPI application
app = FastAPI(
    title="Clinical LLM Orchestration Framework",
    description="An API for orchestrating clinical NLP workflows.",
    version="1.0.0"
)

# --- Pydantic Models for Request and Response Bodies ---

class AnalysisRequest(BaseModel):
    text: str

class AskRequest(BaseModel):
    question: str

class TaskResponse(BaseModel):
    task_id: str
    status: str

class TaskResultResponse(BaseModel):
    task_id: str
    status: str
    result: Dict

# --- API Endpoints ---

@app.post("/analyze", response_model=TaskResponse, status_code=202)
def analyze_text(request: AnalysisRequest):
    """
    Accepts clinical text for analysis.

    This endpoint dispatches a 'clinical_analysis' task to the Celery worker
    and returns a task ID for tracking.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    task = run_workflow_task.delay("clinical_analysis", {"text": request.text})
    return {"task_id": task.id, "status": "Processing"}

@app.post("/ask", response_model=TaskResponse, status_code=202)
def ask_question(request: AskRequest):
    """
    Accepts a question to be answered using the RAG pipeline.

    This endpoint dispatches a 'question_answering' task to the Celery worker
    and returns a task ID.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    task = run_workflow_task.delay("question_answering", {"text": request.question})
    return {"task_id": task.id, "status": "Processing"}

@app.get("/tasks/{task_id}", response_model=TaskResultResponse)
def get_task_status(task_id: str):
    """
    Retrieves the status and result of a Celery task.
    """
    task_result = AsyncResult(task_id)

    if task_result.state == 'PENDING':
        # Task is waiting to be processed or the ID is invalid
        raise HTTPException(status_code=404, detail="Task not found or not yet started.")

    result_data = task_result.result if task_result.ready() else None

    return {
        "task_id": task_id,
        "status": task_result.state,
        "result": result_data
    }

@app.get("/", summary="Health Check")
def read_root():
    """
    A simple health check endpoint to confirm the API is running.
    """
    return {"status": "ok", "message": "Welcome to the Clinical LLM Orchestration Framework API"}
