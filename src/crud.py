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