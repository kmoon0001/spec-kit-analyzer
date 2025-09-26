from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List

from ... import crud, schemas, models
from ...database import get_db
from ...auth import get_current_active_user
from ...core.report_generator import ReportGenerator # Import the generator

router = APIRouter()

# Instantiate the report generator once to reuse it
report_generator = ReportGenerator()

@router.get("/reports", response_model=List[schemas.Report])
def read_reports(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retrieves a list of historical analysis reports for the dashboard."""
    reports = crud.get_reports(db, skip=skip, limit=limit)
    return reports

@router.get("/reports/{report_id}", response_class=HTMLResponse)
def read_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retrieves a single report by ID and generates its HTML view on the fly."""
    db_report = crud.get_report(db, report_id=report_id)
    if db_report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Generate the HTML report from the stored JSON data
    report_html = report_generator.generate_html_report(
        analysis_result=db_report.analysis_result,
        doc_name=db_report.document_name,
        analysis_mode="rubric" # The mode doesn't affect our current template
    )
    return HTMLResponse(content=report_html)

@router.get("/findings-summary", response_model=List[schemas.FindingSummary])
def read_findings_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retrieves a summary of the most common compliance findings."""
    summary = crud.get_findings_summary(db)
    return summary
