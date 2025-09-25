from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import shutil
import os
import uuid
from src.compliance_analyzer import ComplianceAnalyzer
from src.utils import load_config, save_config
from typing import List
from src.guideline_service import GuidelineService
from src.core.hybrid_retriever import HybridRetriever
from src.parsing import parse_document_content


# Add metadata for the API
app = FastAPI(
    title="Clinical Compliance Analyzer API",
    description="API for analyzing clinical documents for compliance.",
    version="1.0.0",
)

config = load_config()
guideline_service = GuidelineService(sources=config.get('guideline_sources', []))
retriever = HybridRetriever(config['models']['retriever'])
analyzer = ComplianceAnalyzer(config, guideline_service, retriever)
tasks = {}

class TaskStatus(BaseModel):
    task_id: str
    status: str
    error: str | None = None

class AnalysisResult(BaseModel):
    task_id: str
    status: str

class Settings(BaseModel):
    quantization: str
    performance_profile: str
    reviewer_difficulty: str

def process_document(file_path: str, task_id: str, discipline: str, doc_type: str):
    try:
        document_text = " ".join([chunk[0] for chunk in parse_document_content(file_path)])
        analysis_result = analyzer.analyze_document(document_text, discipline, doc_type)
        report_html = generate_report(analysis_result, os.path.basename(file_path))
        tasks[task_id] = {"status": "completed", "result": report_html}
    except Exception as e:
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

def process_folder(folder_path: str, task_id: str, discipline: str, doc_type: str):
    try:
        reports = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                document_text = " ".join([chunk[0] for chunk in parse_document_content(file_path)])
                analysis_result = analyzer.analyze_document(document_text, discipline, doc_type)
                report_html = generate_report(analysis_result, filename)
                reports.append(report_html)

        tasks[task_id] = {"status": "completed", "result": reports}
    except Exception as e:
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        # Clean up the temporary folder
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

@app.post("/analyze", response_model=AnalysisResult, status_code=202)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    discipline: str = Form(...),
    doc_type: str = Form(...),
):
    """
    Starts an asynchronous analysis of the uploaded document.

    - **file**: The clinical document to analyze.
    - **discipline**: The discipline to analyze for (e.g., 'PT', 'OT').
    - **doc_type**: The document type (e.g., 'evaluation', 'progress_note').
    - Returns a task ID to check the analysis status.
    """
    task_id = str(uuid.uuid4())
    temp_file_path = f"temp_{task_id}_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_document, temp_file_path, task_id, discipline, doc_type)
    tasks[task_id] = {"status": "processing"}

    return {"task_id": task_id, "status": "processing"}

@app.post("/analyze_folder", response_model=AnalysisResult, status_code=202)
async def analyze_folder(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    discipline: str = Form(...),
    doc_type: str = Form(...),
):
    """
    Starts an asynchronous analysis of the uploaded folder of documents.

    - **files**: The clinical documents to analyze.
    - **discipline**: The discipline to analyze for (e.g., 'PT', 'OT').
    - **doc_type**: The document type (e.g., 'evaluation', 'progress_note').
    - Returns a task ID to check the analysis status.
    """
    task_id = str(uuid.uuid4())
    temp_folder_path = f"temp_{task_id}"
    os.makedirs(temp_folder_path)
    for file in files:
        temp_file_path = os.path.join(temp_folder_path, file.filename)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_folder, temp_folder_path, task_id, discipline, doc_type)
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
        if isinstance(task["result"], list):
            return JSONResponse(content=task["result"])
        else:
            return HTMLResponse(content=task["result"])
    else:
        return task

@app.get("/settings", response_model=Settings)
async def get_settings():
    """
    Retrieves the current settings.
    """
    return {
        "quantization": config.get('quantization', 'none'),
        "performance_profile": config.get('performance_profile', 'medium'),
        "reviewer_difficulty": config.get('reviewer_difficulty', 'moderate'),
    }

@app.put("/settings", response_model=Settings)
async def update_settings(settings: Settings):
    """
    Updates the settings.
    """
    global analyzer
    config['quantization'] = settings.quantization
    config['performance_profile'] = settings.performance_profile
    config['reviewer_difficulty'] = settings.reviewer_difficulty
    save_config(config)
    analyzer = ComplianceAnalyzer(config, guideline_service, retriever)
    return settings

def generate_report(analysis_result: dict, doc_name: str) -> str:
    """
    Generates an HTML report from the analysis result.
    """
    with open(os.path.join("src", "resources", "report_template.html"), "r") as f:
        template_str = f.read()

    # Populate summary
    report_html = template_str.replace("<!-- Placeholder for document name -->", doc_name)
    report_html = report_html.replace("<!-- Placeholder for analysis date -->", str(uuid.uuid4()))

    findings = analysis_result.get("findings", [])
    compliance_score = max(0, 100 - (len(findings) * 10))  # Simple scoring
    report_html = report_html.replace("<!-- Placeholder for compliance score -->", str(compliance_score))
    report_html = report_html.replace("<!-- Placeholder for total findings -->", str(len(findings)))

    # Populate findings table
    findings_rows_html = ""
    if findings:
        for finding in findings:
            findings_rows_html += f"""
            <tr>
                <td>{finding.get('rule_id', 'N/A')}</td>
                <td>{finding.get('risk', 'N/A')}</td>
                <td>{finding.get('suggestion', 'N/A')}</td>
                <td>{finding.get('text', 'N/A')}</td>
            </tr>
            """
    else:
        findings_rows_html = "<tr><td colspan='4'>No findings.</td></tr>"
    report_html = report_html.replace("<!-- Placeholder for findings rows -->", findings_rows_html)

    # Populate Medicare guidelines (This might need to be adjusted based on the new analysis_result format)
    guidelines_html = "<p>No relevant Medicare guidelines found.</p>"
    report_html = report_html.replace("<!-- Placeholder for Medicare guidelines -->", guidelines_html)

    # Populate footer
    report_html = report_html.replace("<!-- Placeholder for generation date -->", str(uuid.uuid4()))

    return report_html