from . import models, schemas
import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, desc


# -------------------------------
# User operations
# -------------------------------

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[models.User]:
    """Fetch a user by unique username."""
    result = await db.execute(select(models.User).filter(models.User.username == username))
    return result.scalars().first()


async def get_user(db: AsyncSession, user_id: int) -> Optional[models.User]:
    """Fetch a user by primary key ID."""
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    return result.scalars().first()


async def create_user(db: AsyncSession, user: schemas.UserCreate, hashed_password: str) -> models.User:
    """Create a new user with a pre-hashed password."""
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def delete_user(db: AsyncSession, user_id: int) -> None:
    await db.execute(delete(models.User).where(models.User.id == user_id))
    await db.commit()


async def change_user_password(
    db: AsyncSession, user: models.User, new_hashed_password: str
) -> models.User:
    user.hashed_password = new_hashed_password
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_rubric(
    db: AsyncSession, rubric: schemas.RubricCreate
) -> models.Rubric:
    db_rubric = models.Rubric(**rubric.model_dump())
    db.add(db_rubric)
    await db.commit()
    await db.refresh(db_rubric)
    return db_rubric


async def get_rubric(db: AsyncSession, rubric_id: int) -> Optional[models.Rubric]:
    """Fetch a rubric by ID."""
    result = await db.execute(select(models.Rubric).filter(models.Rubric.id == rubric_id))
    return result.scalars().first()


async def get_rubrics(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.Rubric]:
    """List rubrics with pagination."""
    result = await db.execute(select(models.Rubric).offset(skip).limit(limit))
    return result.scalars().all()


async def update_rubric(db: AsyncSession, rubric_id: int, rubric: schemas.RubricCreate) -> Optional[models.Rubric]:
    """Update an existing rubric, returning the updated record or None."""
    db_rubric = await get_rubric(db, rubric_id)
    if db_rubric:
        for key, value in rubric.model_dump().items():
            setattr(db_rubric, key, value)
        await db.commit()
        await db.refresh(db_rubric)
    return db_rubric


async def delete_rubric(db: AsyncSession, rubric_id: int) -> None:
    """Delete a rubric by ID."""
    await db.execute(delete(models.Rubric).where(models.Rubric.id == rubric_id))
    await db.commit()


# -------------------------------
# Report and findings operations
# -------------------------------

async def create_report(db: AsyncSession, report: schemas.ReportCreate) -> models.Report:
    """Create a report record from the provided schema."""
    db_report = models.Report(**report.model_dump())
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)
    return db_report


async def get_report(db: AsyncSession, report_id: int) -> Optional[models.Report]:
    """Fetch a report by ID."""
    result = await db.execute(select(models.Report).filter(models.Report.id == report_id))
    return result.scalars().first()


async def get_reports(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.Report]:
    """List reports with pagination."""
    result = await db.execute(select(models.Report).offset(skip).limit(limit))
    return result.scalars().all()


async def delete_report(db: AsyncSession, report_id: int) -> None:
    """Delete a report and its dependent findings by report ID."""
    await db.execute(delete(models.Finding).where(models.Finding.report_id == report_id))
    await db.execute(delete(models.Report).where(models.Report.id == report_id))
    await db.commit()


async def delete_reports_older_than(db: AsyncSession, days: int) -> int:
    """Delete reports and related findings older than a given number of days.

    Returns the number of deleted report rows.
    """
    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    # Identify report IDs to delete
    reports_to_delete_query = select(models.Report.id).filter(models.Report.analysis_date < cutoff_date)
    reports_to_delete_result = await db.execute(reports_to_delete_query)
    report_ids_to_delete = reports_to_delete_result.scalars().all()

    if report_ids_to_delete:
        # Delete associated findings first due to FK constraints
        await db.execute(delete(models.Finding).where(models.Finding.report_id.in_(report_ids_to_delete)))
        # Then delete the reports
        result = await db.execute(delete(models.Report).filter(models.Report.analysis_date < cutoff_date))
        await db.commit()
        return int(result.rowcount or 0)
    return 0


async def find_similar_report(db: AsyncSession, embedding: bytes, threshold: float = 0.9) -> Optional[models.Report]:
    """Placeholder for a similarity search.

    In a real implementation, a vector database or specialized similarity search
    mechanism would be used to find a similar report by embedding.
    """
    return None


async def create_report_and_findings(
    db: AsyncSession,
    report_data: schemas.ReportCreate,
    findings_data: List[schemas.FindingCreate],
) -> models.Report:
    """Create a report with associated findings in a single transaction."""
    db_report = models.Report(
        document_name=report_data.document_name,
        compliance_score=report_data.compliance_score,
        analysis_result=report_data.analysis_result,
        document_embedding=report_data.document_embedding,
    )
    db.add(db_report)
    await db.flush()  # Obtain report ID before creating dependent findings

    for finding_data in findings_data:
        db_finding = models.Finding(
            report_id=db_report.id,
            rule_id=finding_data.rule_id,
            risk=finding_data.risk,
            personalized_tip=finding_data.personalized_tip,
            problematic_text=finding_data.problematic_text,
            clinician_name=finding_data.clinician_name,
            habit_name=finding_data.habit_name,
        )
        db.add(db_finding)

    await db.commit()
    await db.refresh(db_report)
    return db_report


# -------------------------------
# Analytics queries (dashboard)
# -------------------------------

async def get_total_findings_count(
    db: AsyncSession,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
    discipline: Optional[str] = None,
) -> int:
    """Return total number of findings within an optional date range and discipline filter."""
    query = select(func.count(models.Finding.id)).join(models.Report)
    if start_date:
        query = query.filter(models.Report.analysis_date >= start_date)
    if end_date:
        query = query.filter(models.Report.analysis_date <= end_date)
    if discipline:
        query = query.filter(models.Report.analysis_result["discipline"].astext == discipline)
    result = await db.execute(query)
    return result.scalar_one_or_none() or 0


async def get_team_habit_summary(
    db: AsyncSession,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
    discipline: Optional[str] = None,
) -> List[schemas.TeamHabitAnalytics]:
    """Return a summary of findings per habit for the team within an optional date range."""
    query = (
        select(
            models.Finding.habit_name,
            func.count(models.Finding.id).label("count"),
        )
        .join(models.Report)
        .group_by(models.Finding.habit_name)
        .order_by(desc("count"))
        .filter(models.Finding.habit_name.isnot(None))
    )
    if start_date:
        query = query.filter(models.Report.analysis_date >= start_date)
    if end_date:
        query = query.filter(models.Report.analysis_date <= end_date)
    if discipline:
        query = query.filter(models.Report.analysis_result["discipline"].astext == discipline)
    result = await db.execute(query)
    return [
        schemas.TeamHabitAnalytics(habit_name=row.habit_name, count=row.count)
        for row in result.all()
    ]


async def get_clinician_habit_breakdown(
    db: AsyncSession,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
    discipline: Optional[str] = None,
) -> List[schemas.ClinicianHabitAnalytics]:
    """Return a detailed breakdown of findings per habit for each clinician within an optional date range."""
    query = (
        select(
            models.Finding.clinician_name,
            models.Finding.habit_name,
            func.count(models.Finding.id).label("count"),
        )
        .join(models.Report)
        .group_by(models.Finding.clinician_name, models.Finding.habit_name)
        .order_by(models.Finding.clinician_name, desc("count"))
        .filter(models.Finding.clinician_name.isnot(None))
        .filter(models.Finding.habit_name.isnot(None))
    )
    if start_date:
        query = query.filter(models.Report.analysis_date >= start_date)
    if end_date:
        query = query.filter(models.Report.analysis_date <= end_date)
    if discipline:
        query = query.filter(models.Report.analysis_result["discipline"].astext == discipline)
    result = await db.execute(query)
    return [
        schemas.ClinicianHabitAnalytics(
            clinician_name=row.clinician_name,
            habit_name=row.habit_name,
            count=row.count,
        )
        for row in result.all()
    ]


async def get_habit_trend_data(
    db: AsyncSession,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
) -> List[schemas.HabitTrendPoint]:
    """Return data points for habit trends over time."""
    query = (
        select(
            func.date(models.Report.analysis_date).label("date"),
            models.Finding.habit_name,
            func.count(models.Finding.id).label("count"),
        )
        .join(models.Report)
        .group_by("date", models.Finding.habit_name)
        .order_by("date")
        .filter(models.Finding.habit_name.isnot(None))
    )
    if start_date:
        query = query.filter(models.Report.analysis_date >= start_date)
    if end_date:
        query = query.filter(models.Report.analysis_date <= end_date)

    result = await db.execute(query)
    return [
        schemas.HabitTrendPoint(date=row.date, habit_name=row.habit_name, count=row.count)
        for row in result.all()
    ]
