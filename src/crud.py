from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
import datetime
from src import models, schemas


async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    return result.scalars().first()


async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(
        select(models.User).filter(models.User.username == username)
    )
    return result.scalars().first()


async def change_user_password(
    db: AsyncSession, user: models.User, new_hashed_password: str
):
    user.hashed_password = new_hashed_password
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_user(db: AsyncSession, user: schemas.UserCreate, hashed_password: str):
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_total_findings_count(
    db: AsyncSession,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    discipline: Optional[str] = None,
) -> int:
    """Retrieve the total count of findings, optionally filtered by date and discipline."""
    # Placeholder for actual database query
    return 0


async def get_reports(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.AnalysisReport).offset(skip).limit(limit))
    return result.scalars().all()


async def get_report(db: AsyncSession, report_id: int):
    result = await db.execute(
        select(models.AnalysisReport).filter(models.AnalysisReport.id == report_id)
    )
    return result.scalars().first()


async def get_findings_summary(db: AsyncSession):
    # This is a placeholder implementation. A real implementation would involve
    # more complex aggregation queries.
    result = await db.execute(select(models.AnalysisReport))
    reports = result.scalars().all()
    summary = {}
    for report in reports:
        if report.findings:
            for finding in report.findings:
                title = finding.get("issue_title", "Unknown Issue")
                summary[title] = summary.get(title, 0) + 1
    return [{"issue_title": title, "count": count} for title, count in summary.items()]


async def get_all_rubrics(db: AsyncSession):
    """Retrieve all compliance rubrics from the database."""
    result = await db.execute(select(models.ComplianceRubric))
    return result.scalars().all()
