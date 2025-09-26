from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from . import models, schemas
import datetime
import pickle
from typing import Dict, List, Optional
import numpy as np
from scipy.spatial.distance import cosine

# Define a threshold for semantic similarity. 1.0 is identical.
SIMILARITY_THRESHOLD = 0.98

# --- User CRUD ---
async def get_user_by_username(db: AsyncSession, username: str) -> Optional[models.User]:
    result = await db.execute(select(models.User).filter(models.User.username == username))
    return result.scalars().first()

async def change_user_password(db: AsyncSession, user: models.User, new_hashed_password: str) -> models.User:
    user.hashed_password = new_hashed_password
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# --- Report & Analysis CRUD ---
async def create_report_and_findings(db: AsyncSession, report_data: dict, findings_data: list) -> models.Report:
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

async def get_findings_summary(db: AsyncSession, limit: int = 5) -> List[Dict[str, Any]]:
    stmt = select(models.Report)
    result = await db.execute(stmt)
    reports = result.scalars().all()
    
    summary: Dict[str, int] = {}
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

# --- Rubric CRUD Functions (Async) ---
async def get_rubric_by_name(db: AsyncSession, name: str) -> Optional[models.Rubric]:
    stmt = select(models.Rubric).filter(models.Rubric.name == name)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_rubric(db: AsyncSession, rubric_id: int) -> Optional[models.Rubric]:
    stmt = select(models.Rubric).filter(models.Rubric.id == rubric_id)
    result = await db.execute(stmt)
    return result.scalars().first()

<<<<<<< HEAD
async def get_rubrics(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.Rubric]:
    stmt = select(models.Rubric).order_by(models.Rubric.name).offset(skip).limit(limit)
    result = await db.execute(stmt)
||||||| 4db3b6b
    return num_deleted

async def get_rubrics(db: AsyncSession, limit: int = 1000) -> list[models.Rubric]:
    """
    Asynchronously retrieves all rubrics from the database.
    """
    result = await db.execute(select(models.Rubric).limit(limit))
=======
    return num_deleted

async def get_rubrics(db: AsyncSession, limit: int = 1000) -> list[models.Rubric]:
    """Asynchronously retrieves all rubrics from the database."""
    result = await db.execute(select(models.Rubric).limit(limit))
>>>>>>> origin/main
    return result.scalars().all()

async def create_rubric(db: AsyncSession, rubric: schemas.RubricCreate) -> models.Rubric:
    db_rubric = models.Rubric(name=rubric.name, content=rubric.content)
    db.add(db_rubric)
    await db.commit()
    await db.refresh(db_rubric)
    return db_rubric

async def update_rubric(db: AsyncSession, rubric_id: int, rubric_update: schemas.RubricCreate) -> Optional[models.Rubric]:
    db_rubric = await get_rubric(db, rubric_id)
    if db_rubric:
        db_rubric.name = rubric_update.name
        db_rubric.content = rubric_update.content
        db.add(db_rubric)
        await db.commit()
        await db.refresh(db_rubric)
    return db_rubric

async def delete_rubric(db: AsyncSession, rubric_id: int) -> Optional[models.Rubric]:
    db_rubric = await get_rubric(db, rubric_id)
    if db_rubric:
        await db.delete(db_rubric)
        await db.commit()
    return db_rubric