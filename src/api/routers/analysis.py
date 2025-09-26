from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import logging
import traceback

from src.database import schemas, crud, models
from src.database.database import get_db
from src.core.document_analysis_service import DocumentAnalysisService
from src.api.routers.auth import get_current_active_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize the analysis service
# This service holds the AI models and can be reused across requests
analysis_service = DocumentAnalysisService()


def analyze_and_save_task(db: Session, doc_content: str, doc_name: str):
    """
    A background task to run the analysis and save the report.
    This prevents the API from timing out on long analyses.
    """
    try:
        logger.info(f"Starting background analysis for document: {doc_name}")
        # 1. Run the full analysis pipeline
        report_data, findings_data = analysis_service.analyze_document(doc_content, doc_name)

        # 2. Save the report and findings to the database
        crud.create_report_and_findings(db, report_data=report_data, findings_data=findings_data)
        logger.info(f"Successfully saved analysis report for: {doc_name}")

    except Exception as e:
        # Log the full error traceback for debugging
        tb_str = traceback.format_exc()
        logger.error(f"Error during background analysis for {doc_name}: {e}\n{tb_str}")


@router.post("/analyze/text", status_code=202)
def analyze_text(
    background_tasks: BackgroundTasks,
    text_input: schemas.TextInput,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Accepts plain text, runs analysis in the background,
    and returns immediately with a confirmation.
    """
    doc_name = f"text_input_{text_input.title[:20]}.txt"
    # Add the analysis task to be run in the background
    background_tasks.add_task(analyze_and_save_task, db, text_input.content, doc_name)

    return {"message": "Analysis has been started in the background."}


@router.post("/analyze/file", status_code=202)
async def analyze_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Accepts a file upload, runs analysis in the background,
    and returns immediately.
    """
    try:
        content = await file.read()
        doc_name = file.filename
        # Add the analysis task to be run in the background
        background_tasks.add_task(analyze_and_save_task, db, content.decode('utf-8', errors='ignore'), doc_name)

        return {"message": "File analysis has been started in the background."}

    except Exception as e:
        logger.error(f"Error processing file upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")


@router.get("/reports", response_model=List[schemas.Report])
def get_reports(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieves a list of the most recent analysis reports.
    """
    reports = crud.get_reports(db, skip=skip, limit=limit)
    return reports


@router.get("/reports/{report_id}", response_model=schemas.Report)
def get_report_details(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieves the full details of a specific analysis report.
    """
    report = crud.get_report(db, report_id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report