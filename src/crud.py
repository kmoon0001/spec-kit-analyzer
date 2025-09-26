from sqlalchemy.orm import Session
<<<<<<< HEAD
from . import models, schemas
||||||| c46cdd8
from . import models
=======
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from . import models
>>>>>>> origin/main
import datetime
import pickle
from typing import Dict
import numpy as np
from scipy.spatial.distance import cosine

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(models.User).filter(models.User.username == username))
    return result.scalars().first()

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

<<<<<<< HEAD
||||||| c46cdd8
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

=======
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
    return None

def get_reports(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Report).order_by(models.Report.analysis_date.desc()).offset(skip).limit(limit).all()

>>>>>>> origin/main
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

<<<<<<< HEAD
def delete_reports_older_than(db: Session, days: int) -> int:
    """Deletes all reports from the database older than a specified number of days."""
||||||| c46cdd8
def delete_reports_older_than(db: Session, days: int) -> int:
    if days <= 0:
        return 0
=======
async def delete_reports_older_than(db: AsyncSession, days: int) -> int:
    if days <= 0:
        return 0
>>>>>>> origin/main
    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
<<<<<<< HEAD
    reports_to_delete = db.query(models.Report).filter(models.Report.created_at < cutoff_date)
    num_deleted = reports_to_delete.count()
||||||| c46cdd8
    reports_to_delete = db.query(models.Report).filter(models.Report.analysis_date < cutoff_date)
    num_deleted = reports_to_delete.count()
=======

    # First, select the reports to be deleted
    result = await db.execute(
        select(models.Report).filter(models.Report.analysis_date < cutoff_date)
    )
    reports_to_delete = result.scalars().all()

    num_deleted = len(reports_to_delete)
>>>>>>> origin/main
    if num_deleted > 0:
<<<<<<< HEAD
        reports_to_delete.delete(synchronize_session=False)
        db.commit()
    return num_deleted
||||||| c46cdd8
        reports_to_delete.delete(synchronize_session=False)
        db.commit()
    return num_deleted

def get_rubrics(db: Session, limit: int = 1000):
    """
    Mock function to get rubrics. Returns an empty list.
    """
    return []
=======
        for report in reports_to_delete:
            await db.delete(report)
        await db.commit()

    return num_deleted

async def get_rubrics(db: AsyncSession, limit: int = 1000) -> list[models.Rubric]:
    """Asynchronously retrieves all rubrics from the database."""
    result = await db.execute(select(models.Rubric).limit(limit))
    return result.scalars().all()
>>>>>>> origin/main
