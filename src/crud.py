from sqlalchemy.ext.asyncio import AsyncSession
<<<<<<< HEAD
from sqlalchemy import select, delete
from . import models
||||||| 604b275
from sqlalchemy import select
from . import models
=======
from sqlalchemy import select, delete
from . import models, schemas
>>>>>>> origin/main
import datetime
import pickle
<<<<<<< HEAD
from typing import List, Dict, Optional
||||||| 604b275
=======
from typing import Dict, List, Optional
>>>>>>> origin/main
import numpy as np
from scipy.spatial.distance import cosine

# Define a threshold for semantic similarity. 1.0 is identical.
SIMILARITY_THRESHOLD = 0.98

<<<<<<< HEAD
async def get_user_by_username(db: AsyncSession, username: str) -> Optional[models.User]:
||||||| 604b275
async def get_user_by_username(db: AsyncSession, username: str):
=======
# --- User CRUD ---
async def get_user_by_username(db: AsyncSession, username: str) -> Optional[models.User]:
>>>>>>> origin/main
    result = await db.execute(select(models.User).filter(models.User.username == username))
    return result.scalars().first()

<<<<<<< HEAD
async def create_report_and_findings(db: AsyncSession, report_data: dict, findings_data: list) -> models.Report:
||||||| 604b275
def create_report_and_findings(db: Session, report_data: dict, findings_data: list):
=======
async def change_user_password(db: AsyncSession, user: models.User, new_hashed_password: str) -> models.User:
    user.hashed_password = new_hashed_password
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# --- Report & Analysis CRUD ---
async def create_report_and_findings(db: AsyncSession, report_data: dict, findings_data: list) -> models.Report:
>>>>>>> origin/main
    db_report = models.Report(
        document_name=report_data['document_name'],
        compliance_score=report_data['compliance_score'],
        analysis_result=report_data['analysis_result'],
        document_embedding=report_data.get('document_embedding')
    )
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)
    return db_report

async def find_similar_report(db: AsyncSession, new_embedding: np.ndarray) -> Optional[models.Report]:
    stmt = select(models.Report).filter(models.Report.document_embedding.isnot(None))
    result = await db.execute(stmt)
    cached_reports = result.scalars().all()
    
    if not cached_reports:
<<<<<<< HEAD
        return None

    best_match = None
    highest_similarity = 0.0

    for report in cached_reports:
        cached_embedding = pickle.loads(report.document_embedding)
        similarity = 1 - cosine(new_embedding.flatten(), cached_embedding.flatten())

        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = report

    if highest_similarity >= SIMILARITY_THRESHOLD:
        return best_match
    return None

async def get_reports(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.Report]:
    stmt = select(models.Report).order_by(models.Report.analysis_date.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_report(db: AsyncSession, report_id: int) -> Optional[models.Report]:
    stmt = select(models.Report).filter(models.Report.id == report_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def change_user_password(db: AsyncSession, user: models.User, new_hashed_password: str) -> models.User:
    user.hashed_password = new_hashed_password
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_findings_summary(db: AsyncSession, limit: int = 5) -> List[Dict]:
    stmt = select(models.Report)
    result = await db.execute(stmt)
    reports = result.scalars().all()
    summary = {}
    for report in reports:
        if report.analysis_result and 'findings' in report.analysis_result:
            for finding in report.analysis_result['findings']:
                rule_id = finding.get('rule_id', 'Unknown')
                summary[rule_id] = summary.get(rule_id, 0) + 1

    sorted_summary = sorted(summary.items(), key=lambda item: item[1], reverse=True)
    return [{"rule_id": rule_id, "count": count} for rule_id, count in sorted_summary[:limit]]

async def delete_reports_older_than(db: AsyncSession, days: int) -> int:
    if days <= 0:
        return 0
    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    stmt = delete(models.Report).where(models.Report.analysis_date < cutoff_date)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount

async def get_rubrics(db: AsyncSession, limit: int = 1000) -> list[models.Rubric]:
    """Asynchronously retrieves all rubrics from the database."""
    result = await db.execute(select(models.Rubric).limit(limit))
    return result.scalars().all()
||||||| 604b275
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

async def delete_reports_older_than(db: AsyncSession, days: int) -> int:
    if days <= 0:
        return 0
    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    # First, select the reports to be deleted
    result = await db.execute(
        select(models.Report).filter(models.Report.analysis_date < cutoff_date)
    )
    reports_to_delete = result.scalars().all()

    num_deleted = len(reports_to_delete)
    if num_deleted > 0:
        for report in reports_to_delete:
            await db.delete(report)
        await db.commit()

    return num_deleted

async def get_rubrics(db: AsyncSession, limit: int = 1000) -> list[models.Rubric]:
    """Asynchronously retrieves all rubrics from the database."""
    result = await db.execute(select(models.Rubric).limit(limit))
    return result.scalars().all()
=======
        return None
>>>>>>> origin/main
