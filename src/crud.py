from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_report_and_findings(db: Session, report_data: dict, findings_data: list):
    """
    Creates a new Report and its associated Findings in the database.
    """
    # Note: We are now storing the raw analysis JSON in the report.
    db_report = models.Report(
        document_name=report_data['document_name'],
        compliance_score=report_data['compliance_score'],
        analysis_result=report_data['analysis_result']
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    # The individual findings are now part of the JSON and don't need to be saved separately.
    # If you still wanted to save them for easier querying, the logic would remain here.
    
    return db_report

def get_reports(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieves a list of all reports from the database.
    """
    return db.query(models.Report).order_by(models.Report.analysis_date.desc()).offset(skip).limit(limit).all()

def get_report(db: Session, report_id: int):
    """
    Retrieves a single report by its ID.
    """
    return db.query(models.Report).filter(models.Report.id == report_id).first()

def change_user_password(db: Session, user: models.User, new_hashed_password: str):
    """
    Updates a user's password in the database.
    """
    user.hashed_password = new_hashed_password
    db.commit()
    db.refresh(user)
    return user

def get_findings_summary(db: Session, limit: int = 5):
    """
    Retrieves a summary of the most common findings by rule_id from the stored JSON.
    """
    # This query is more complex as it needs to process the JSON data.
    # For simplicity, we will implement this logic in the application layer for now.
    # A more advanced implementation might use database-specific JSON functions.
    reports = db.query(models.Report).all()
    summary = {}
    for report in reports:
        if report.analysis_result and 'findings' in report.analysis_result:
            for finding in report.analysis_result['findings']:
                rule_id = finding.get('rule_id', 'Unknown')
                summary[rule_id] = summary.get(rule_id, 0) + 1
    
    # Sort and limit the results
    sorted_summary = sorted(summary.items(), key=lambda item: item[1], reverse=True)
    return [{"rule_id": rule_id, "count": count} for rule_id, count in sorted_summary[:limit]]
