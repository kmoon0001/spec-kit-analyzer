from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from src.database import schemas, crud, models, get_db
from src.api.routers.auth import get_current_active_user

router = APIRouter()

@router.get("/summary", response_model=schemas.DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Provides a summary of compliance data for the dashboard.
    """
    total_reports = len(crud.get_reports(db, limit=1000)) # A simple count for now

    # This is a placeholder for a more complex calculation
    average_score = 75

    # Get the most common findings
    common_findings = crud.get_findings_summary(db, limit=5)

    return {
        "total_reports_analyzed": total_reports,
        "average_compliance_score": average_score,
        "most_common_findings": common_findings
    }

@router.get("/trend", response_model=List[schemas.ComplianceTrendPoint])
def get_compliance_trend(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Provides data points for the compliance score trend chart.
    """
    reports = crud.get_reports(db, limit=30) # Get last 30 reports for the trend

    trend_data = [
        {
            "date": report.analysis_date.strftime("%Y-%m-%d"),
            "score": report.compliance_score
        }
        for report in reversed(reports) # Reverse to show oldest to newest
    ]

    return trend_data