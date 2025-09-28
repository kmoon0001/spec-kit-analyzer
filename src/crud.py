from sqlalchemy.orm import Session
from . import models


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_report_and_findings(db: Session, report_data: dict, findings_data: list):
    """
    Creates a new Report and its associated Findings in the database.
    """
    db_report = models.Report(**report_data)
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    for finding in findings_data:
        db_finding = models.Finding(
            report_id=db_report.id,
            rule_id=finding.get("rule_id", "N/A"),
            risk=finding.get("risk", "N/A"),
            personalized_tip=finding.get("personalized_tip", ""),
            problematic_text=finding.get("text", ""),
        )
        db.add(db_finding)

    db.commit()
    return db_report


def get_reports(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieves a list of all reports from the database.
    """
    return (
        db.query(models.Report)
        .order_by(models.Report.analysis_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
