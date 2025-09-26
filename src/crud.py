from sqlalchemy.orm import Session
from . import models, schemas
import datetime
import pickle
from typing import Dict
import numpy as np
from scipy.spatial.distance import cosine

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(username=user.username, hashed_password=fake_hashed_password, is_admin=False)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_rubric(db: Session, rubric: schemas.RubricCreate):
    db_rubric = models.Rubric(**rubric.dict())
    db.add(db_rubric)
    db.commit()
    db.refresh(db_rubric)
    return db_rubric

def get_rubrics(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Rubric).offset(skip).limit(limit).all()

def create_report(db: Session, report_data: dict, report_html: str):
    db_report = models.Report(
        document_name=report_data["document_name"],
        compliance_score=report_data["compliance_score"],
        analysis_result=report_data["analysis_result"],
        report_html=report_html,
        document_embedding=report_data["document_embedding"]
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_report(db: Session, report_id: int):
    return db.query(models.Report).filter(models.Report.id == report_id).first()

def change_user_password(db: Session, user: models.User, new_hashed_password: str):
    user.hashed_password = new_hashed_password  # type: ignore[assignment]
    db.commit()
    db.refresh(user)
    return user

def get_findings_summary(db: Session, limit: int = 5):
    reports = db.query(models.Report).all()
    summary: Dict[str, int] = {}
    for report in reports:
        if report.analysis_result and 'findings' in report.analysis_result:  # type: ignore[operator]
            for finding in report.analysis_result['findings']:  # type: ignore[attr-defined]
                rule_id = finding.get('rule_id', 'Unknown')
                summary[rule_id] = summary.get(rule_id, 0) + 1

    sorted_summary = sorted(summary.items(), key=lambda item: item[1], reverse=True)
    return dict(sorted_summary[:limit])

def delete_reports_older_than(db: Session, days: int) -> int:
    """Deletes all reports from the database older than a specified number of days."""
    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    reports_to_delete = db.query(models.Report).filter(models.Report.created_at < cutoff_date)
    num_deleted = reports_to_delete.count()
    if num_deleted > 0:
        reports_to_delete.delete(synchronize_session=False)
        db.commit()
    return num_deleted