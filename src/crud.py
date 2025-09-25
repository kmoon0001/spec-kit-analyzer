from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
import datetime
import pickle
import numpy as np
from scipy.spatial.distance import cosine

# Define a threshold for semantic similarity. 1.0 is identical.
SIMILARITY_THRESHOLD = 0.98

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_report_and_findings(db: Session, report_data: dict, findings_data: list):
    db_report = models.Report(
        document_name=report_data['document_name'],
        compliance_score=report_data['compliance_score'],
        analysis_result=report_data['analysis_result'],
        document_embedding=report_data.get('document_embedding')
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def find_similar_report(db: Session, new_embedding: np.ndarray) -> models.Report | None:
    """
    Finds a report in the database with a semantically similar document embedding.

    Args:
        db: The SQLAlchemy database session.
        new_embedding: The numpy array of the new document's embedding.

    Returns:
        The most similar Report object if it meets the threshold, otherwise None.
    """
    # Fetch all existing reports that have an embedding
    cached_reports = db.query(models.Report).filter(models.Report.document_embedding.isnot(None)).all()
    if not cached_reports:
        return None

    best_match = None
    highest_similarity = 0.0

    for report in cached_reports:
        # Deserialize the stored embedding
        cached_embedding = pickle.loads(report.document_embedding)
        
        # Calculate cosine similarity (1 - cosine distance)
        similarity = 1 - cosine(new_embedding, cached_embedding)
        
        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = report

    if highest_similarity >= SIMILARITY_THRESHOLD:
        return best_match
    else:
        return None

def get_reports(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Report).order_by(models.Report.analysis_date.desc()).offset(skip).limit(limit).all()

def get_report(db: Session, report_id: int):
    return db.query(models.Report).filter(models.Report.id == report_id).first()

def change_user_password(db: Session, user: models.User, new_hashed_password: str):
    user.hashed_password = new_hashed_password
    db.commit()
    db.refresh(user)
    return user

def get_findings_summary(db: Session, limit: int = 5):
    reports = db.query(models.Report).all()
    summary = {}
    for report in reports:
        if report.analysis_result and 'findings' in report.analysis_result:
            for finding in report.analysis_result['findings']:
                rule_id = finding.get('rule_id', 'Unknown')
                summary[rule_id] = summary.get(rule_id, 0) + 1
    
    sorted_summary = sorted(summary.items(), key=lambda item: item[1], reverse=True)
    return [{"rule_id": rule_id, "count": count} for rule_id, count in sorted_summary[:limit]]

def delete_reports_older_than(db: Session, days: int) -> int:
    if days <= 0:
        return 0
    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    reports_to_delete = db.query(models.Report).filter(models.Report.analysis_date < cutoff_date)
    num_deleted = reports_to_delete.count()
    if num_deleted > 0:
        reports_to_delete.delete(synchronize_session=False)
        db.commit()
    return num_deleted
