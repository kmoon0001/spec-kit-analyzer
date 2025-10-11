# MODIFIED: Added timezone and timedelta imports.
"""Database CRUD operations for the Therapy Compliance Analyzer.

Provides async database operations for users, rubrics, reports, and findings.
"""

import datetime
import logging
import math
import sqlite3
from collections import Counter
from datetime import date, timedelta
from typing import Any

import numpy as np
import sqlalchemy
import sqlalchemy.exc
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.vector_store import get_vector_store
from . import models, schemas

logger = logging.getLogger(__name__)


async def get_user(db: AsyncSession, user_id: int) -> models.User | None:
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    return result.scalars().first()


default_admin_flag = False


async def get_user_by_username(db: AsyncSession, username: str) -> models.User | None:
    """Get user by username with input validation.

    Args:
        db: Database session
        username: Username to search for

    Returns:
        models.User | None: User if found, None otherwise

    Raises:
        ValueError: If username is invalid
    """
    if not username or not username.strip():
        raise ValueError("Username cannot be empty")

    # Sanitize username - remove extra whitespace and convert to lowercase
    clean_username = username.strip().lower()

    try:
        result = await db.execute(select(models.User).where(models.User.username == clean_username))
        return result.scalars().first()
    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        logger.error("Failed to get user by username %s: %s", clean_username, e)
        raise


async def create_user(
    db: AsyncSession,
    user: schemas.UserCreate,
    hashed_password: str,
    *,
    is_admin: bool | None = None,
) -> models.User:
    """Create a new user with proper transaction handling.

    Args:
        db: Database session
        user: User creation data
        hashed_password: Pre-hashed password
        is_admin: Optional admin flag override

    Returns:
        models.User: The created user

    Raises:
        sqlalchemy.exc.IntegrityError: If username already exists
        sqlalchemy.exc.SQLAlchemyError: For other database errors
    """
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=is_admin if is_admin is not None else getattr(user, "is_admin", False),
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
        logger.info("Created user: %s", user.username)
        return db_user
    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        await db.rollback()
        logger.error("Failed to create user %s: %s", user.username, e)
        raise


async def change_user_password(db: AsyncSession, user: models.User, new_hashed_password: str) -> models.User:
    user.hashed_password = new_hashed_password  # type: ignore[attr-defined]
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Rubric management
# ---------------------------------------------------------------------------


async def create_rubric(db: AsyncSession, rubric: schemas.RubricCreate) -> models.ComplianceRubric:
    """Create a new compliance rubric."""
    db_rubric = models.ComplianceRubric(**rubric.model_dump())
    db.add(db_rubric)
    try:
        await db.commit()
    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        await db.rollback()
        raise
    await db.refresh(db_rubric)
    return db_rubric


async def get_rubrics(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    discipline: str | None = None,
    category: str | None = None,
) -> list[models.ComplianceRubric]:
    """Return a page of rubrics with optional filtering.

    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        discipline: Optional discipline filter (PT, OT, SLP)
        category: Optional category filter

    Returns:
        list[models.ComplianceRubric]: List of rubrics

    Raises:
        ValueError: If pagination parameters are invalid
    """
    # Validate pagination parameters
    if skip < 0:
        raise ValueError("Skip parameter must be non-negative")
    if limit < 1 or limit > 1000:
        raise ValueError("Limit must be between 1 and 1000")

    query = select(models.ComplianceRubric)

    # Apply filters
    if discipline:
        query = query.where(models.ComplianceRubric.discipline == discipline.upper())
    if category:
        query = query.where(models.ComplianceRubric.category == category)

    # Apply ordering and pagination
    query = query.order_by(models.ComplianceRubric.discipline, models.ComplianceRubric.name).offset(skip).limit(limit)

    try:
        result = await db.execute(query)
        rubrics = list(result.scalars().all())
        logger.debug("Retrieved %d rubrics (skip=%d, limit=%d)", len(rubrics), skip, limit)
        return rubrics
    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        logger.error("Failed to get rubrics: %s", e)
        raise


async def get_rubric(db: AsyncSession, rubric_id: int) -> models.ComplianceRubric | None:
    """Return a single rubric by identifier."""
    query = select(models.ComplianceRubric).where(models.ComplianceRubric.id == rubric_id)
    result = await db.execute(query)
    return result.scalars().first()


async def update_rubric(
    db: AsyncSession, rubric_id: int, rubric: schemas.RubricCreate
) -> models.ComplianceRubric | None:
    """Update an existing rubric."""
    db_rubric = await get_rubric(db, rubric_id)
    if db_rubric is None:
        return None

    for field, value in rubric.model_dump().items():
        setattr(db_rubric, field, value)
    db_rubric.updated_at = datetime.datetime.utcnow()

    try:
        await db.commit()
    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        await db.rollback()
        raise
    await db.refresh(db_rubric)
    return db_rubric


async def delete_rubric(db: AsyncSession, rubric_id: int) -> bool:
    """Delete a rubric if it exists.

    Args:
        db: Database session
        rubric_id: ID of the rubric to delete

    Returns:
        bool: True if rubric was deleted, False if not found

    Raises:
        sqlalchemy.exc.SQLAlchemyError: For database errors
    """
    if rubric_id <= 0:
        raise ValueError("Rubric ID must be positive")

    try:
        db_rubric = await get_rubric(db, rubric_id)
        if db_rubric is None:
            logger.warning("Attempted to delete non-existent rubric: %d", rubric_id)
            return False

        await db.delete(db_rubric)
        await db.commit()
        logger.info("Deleted rubric: %s (ID: %d)", db_rubric.name, rubric_id)
        return True

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        await db.rollback()
        logger.error("Failed to delete rubric %d: %s", rubric_id, e)
        raise


async def get_dashboard_statistics(db: AsyncSession) -> dict[str, Any]:
    """Computes and returns key statistics for the main dashboard.

    Args:
        db: Database session

    Returns:
        dict[str, Any]: Dashboard statistics including document counts and scores

    Raises:
        sqlalchemy.exc.SQLAlchemyError: For database errors
    """
    try:
        # Get total documents analyzed
        total_docs_query = select(func.count(models.AnalysisReport.id))
        total_docs_result = await db.execute(total_docs_query)
        total_documents_analyzed = total_docs_result.scalar_one_or_none() or 0

        # Get overall compliance score
        avg_score_query = select(func.avg(models.AnalysisReport.compliance_score)).where(
            models.AnalysisReport.compliance_score.is_not(None)
        )
        avg_score_result = await db.execute(avg_score_query)
        overall_compliance_score = float(avg_score_result.scalar_one_or_none() or 0.0)

        # Get compliance by category
        category_query = (
            select(
                models.AnalysisReport.document_type,
                func.avg(models.AnalysisReport.compliance_score).label("average_score"),
                func.count(models.AnalysisReport.id).label("document_count"),
            )
            .where(
                models.AnalysisReport.document_type.is_not(None),
                models.AnalysisReport.compliance_score.is_not(None),
            )
            .group_by(models.AnalysisReport.document_type)
            .order_by(models.AnalysisReport.document_type)
        )
        category_result = await db.execute(category_query)

        compliance_by_category = {}
        for row in category_result.all():
            if row.document_type:
                compliance_by_category[row.document_type] = {
                    "average_score": float(row.average_score or 0.0),
                    "document_count": int(row.document_count or 0),
                }

        statistics = {
            "total_documents_analyzed": total_documents_analyzed,
            "overall_compliance_score": round(overall_compliance_score, 2),
            "compliance_by_category": compliance_by_category,
            "last_updated": datetime.datetime.now(datetime.UTC).isoformat(),
        }

        logger.debug("Generated dashboard statistics: %d documents analyzed", total_documents_analyzed)
        return statistics

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        logger.error("Failed to get dashboard statistics: %s", e)
        # Return default statistics on error
        return {
            "total_documents_analyzed": 0,
            "overall_compliance_score": 0.0,
            "compliance_by_category": {},
            "last_updated": datetime.datetime.now(datetime.UTC).isoformat(),
            "error": "Failed to load statistics",
        }


async def get_organizational_metrics(db: AsyncSession, days_back: int) -> dict[str, Any]:
    """Computes high-level organizational metrics."""
    cutoff_date = datetime.datetime.now(datetime.UTC) - timedelta(days=days_back)

    report_query = select(models.AnalysisReport).filter(models.AnalysisReport.analysis_date >= cutoff_date)
    reports = list(
        (await db.execute(report_query.options(selectinload(models.AnalysisReport.findings)))).scalars().unique().all()
    )

    total_analyses = len(reports)
    total_findings = sum(len(r.findings) for r in reports)
    avg_score = np.mean([r.compliance_score for r in reports]) if reports else 0

    user_query = select(func.count(models.User.id))
    total_users = (await db.execute(user_query)).scalar_one_or_none() or 0

    return {
        "total_users": total_users,
        "avg_compliance_score": avg_score,
        "total_findings": total_findings,
        "total_analyses": total_analyses,
    }


async def get_discipline_breakdown(db: AsyncSession, days_back: int) -> dict[str, dict[str, Any]]:
    """Computes compliance metrics broken down by discipline, querying the JSON field."""
    cutoff_date = datetime.datetime.now(datetime.UTC) - timedelta(days=days_back)

    query = (
        select(
            models.AnalysisReport.analysis_result["discipline"].as_string().label("discipline"),
            func.avg(models.AnalysisReport.compliance_score).label("avg_score"),
            func.count(models.AnalysisReport.id).label("user_count"),
        )
        .filter(models.AnalysisReport.analysis_date >= cutoff_date)
        .group_by(models.AnalysisReport.analysis_result["discipline"].as_string())
    )
    result = await db.execute(query)
    return {
        row.discipline: {"avg_compliance_score": row.avg_score, "user_count": row.user_count} for row in result.all()
    }


async def get_team_habit_breakdown(db: AsyncSession, days_back: int) -> dict[str, dict[str, Any]]:
    """Computes the distribution of findings related to habits."""
    # This is a simplified example. A real implementation would join with a habits table.
    return {
        "habit_1": {"habit_number": 1, "habit_name": "Be Proactive", "percentage": 25.0},
        "habit_2": {"habit_number": 2, "habit_name": "Begin with the End in Mind", "percentage": 15.0},
        "habit_3": {"habit_number": 3, "habit_name": "Put First Things First", "percentage": 20.0},
    }


async def get_training_needs(db: AsyncSession, days_back: int) -> list[dict[str, Any]]:
    """Identifies potential training needs based on finding frequency."""
    # This is a simplified example.
    return [
        {
            "habit_name": "Put First Things First",
            "percentage_of_findings": 20.0,
            "priority": "high",
            "affected_users": 10,
            "training_focus": "Time management and prioritization",
        },
        {
            "habit_name": "Be Proactive",
            "percentage_of_findings": 25.0,
            "priority": "medium",
            "affected_users": 15,
            "training_focus": "Identifying and addressing potential issues",
        },
    ]


async def get_team_performance_trends(db: AsyncSession, days_back: int) -> list[dict[str, Any]]:
    """Computes team performance trends grouped by week."""
    if days_back <= 0:
        return []

    now = datetime.datetime.now(datetime.UTC)
    num_weeks = max(1, math.ceil(days_back / 7))
    cutoff_date = now - datetime.timedelta(days=days_back)

    query = (
        select(models.AnalysisReport)
        .options(selectinload(models.AnalysisReport.findings))
        .where(models.AnalysisReport.analysis_date >= cutoff_date)
    )
    result = await db.execute(query)
    reports = list(result.scalars().unique().all())

    def _as_aware(dt: datetime.datetime) -> datetime.datetime:
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.replace(tzinfo=datetime.UTC)
        return dt.astimezone(datetime.UTC)

    trends: list[dict[str, Any]] = []
    for index in range(num_weeks):
        week_end = now - datetime.timedelta(days=index * 7)
        week_start = week_end - datetime.timedelta(days=7)

        week_reports = [report for report in reports if week_start <= _as_aware(report.analysis_date) < week_end]

        if week_reports:
            avg_score = float(np.mean([report.compliance_score for report in week_reports]))
            total_findings = sum(len(report.findings) for report in week_reports)
        else:
            avg_score = 0.0
            total_findings = 0

        trends.append(
            {
                "week": index + 1,
                "avg_compliance_score": avg_score,
                "total_findings": total_findings,
            }
        )

    return trends


async def get_benchmark_data(
    db: AsyncSession,
    days_back: int = 365,
    min_analyses: int = 10,
) -> dict[str, Any]:
    """Get benchmark data for compliance score percentiles.

    Args:
        db: Database session
        days_back: Number of days to look back for data
        min_analyses: Minimum number of analyses required for meaningful benchmarks

    Returns:
        dict[str, Any]: Benchmark data with percentiles and metadata
    """
    try:
        # Calculate cutoff date
        cutoff_date = datetime.datetime.now(datetime.UTC) - timedelta(days=days_back)

        # Query compliance scores within the time window
        result = await db.execute(
            select(models.AnalysisReport.compliance_score)
            .where(
                models.AnalysisReport.compliance_score.is_not(None),
                models.AnalysisReport.analysis_date >= cutoff_date,
            )
            .order_by(models.AnalysisReport.compliance_score)
        )
        scores = [float(row[0]) for row in result.fetchall()]

        # Default benchmarks for insufficient data
        default_benchmarks = {
            "compliance_score_percentiles": {
                "p10": 65.0,
                "p25": 70.0,
                "p50": 80.0,
                "p75": 90.0,
                "p90": 95.0,
            },
            "total_analyses": 0,
            "data_quality": "insufficient",
            "days_analyzed": days_back,
            "last_updated": datetime.datetime.now(datetime.UTC).isoformat(),
        }

        if len(scores) < min_analyses:
            logger.warning("Insufficient data for benchmarks: %d analyses (minimum: %d)", len(scores), min_analyses)
            return {
                **default_benchmarks,
                "total_analyses": len(scores),
            }

        # Calculate percentiles using numpy
        percentiles = {
            "p10": float(np.percentile(scores, 10)),
            "p25": float(np.percentile(scores, 25)),
            "p50": float(np.percentile(scores, 50)),
            "p75": float(np.percentile(scores, 75)),
            "p90": float(np.percentile(scores, 90)),
        }

        # Calculate additional statistics
        mean_score = float(np.mean(scores))
        std_score = float(np.std(scores))

        benchmark_data = {
            "compliance_score_percentiles": percentiles,
            "total_analyses": len(scores),
            "mean_score": round(mean_score, 2),
            "std_deviation": round(std_score, 2),
            "data_quality": "good" if len(scores) >= min_analyses * 2 else "adequate",
            "days_analyzed": days_back,
            "score_range": {
                "min": float(min(scores)),
                "max": float(max(scores)),
            },
            "last_updated": datetime.datetime.now(datetime.UTC).isoformat(),
        }

        logger.debug("Generated benchmark data from %d analyses", len(scores))
        return benchmark_data

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error, ValueError) as e:
        logger.error("Error getting benchmark data: %s", e)
        return {
            **default_benchmarks,
            "error": str(e),
        }


async def get_all_reports_with_embeddings(db: AsyncSession) -> list[models.AnalysisReport]:
    """Return all analysis reports that have an embedding stored."""
    query = (
        select(models.AnalysisReport)
        .options(selectinload(models.AnalysisReport.findings))
        .where(models.AnalysisReport.document_embedding.isnot(None))
    )
    try:
        result = await db.execute(query)
    except OperationalError as exc:
        logger.warning("Unable to load existing embeddings: %s", exc)
        return []
    return list(result.scalars().unique().all())


async def get_report(db: AsyncSession, report_id: int) -> models.AnalysisReport | None:
    """Fetches a single analysis report with its findings eagerly loaded.

    Args:
        db: Database session
        report_id: ID of the report to fetch

    Returns:
        models.AnalysisReport | None: Report if found, None otherwise

    Raises:
        ValueError: If report_id is invalid
        sqlalchemy.exc.SQLAlchemyError: For database errors
    """
    if report_id <= 0:
        raise ValueError("Report ID must be positive")

    try:
        query = (
            select(models.AnalysisReport)
            .options(selectinload(models.AnalysisReport.findings))
            .where(models.AnalysisReport.id == report_id)
        )
        result = await db.execute(query)
        report = result.scalars().first()

        if report:
            logger.debug("Retrieved report: %s (ID: %d)", report.document_name, report_id)
        else:
            logger.warning("Report not found: %d", report_id)

        return report

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        logger.error("Failed to get report %d: %s", report_id, e)
        raise


async def create_analysis_report(
    db: AsyncSession,
    report_data: schemas.ReportCreate,
    findings_data: list[schemas.FindingCreate] | None = None,
) -> models.AnalysisReport:
    """Create a new analysis report with optional findings.

    Args:
        db: Database session
        report_data: Report creation data
        findings_data: Optional list of findings to create with the report

    Returns:
        models.AnalysisReport: The created report with findings

    Raises:
        ValueError: If report data is invalid
        sqlalchemy.exc.SQLAlchemyError: For database errors
    """
    # Validate report data
    if not report_data.document_name or not report_data.document_name.strip():
        raise ValueError("Document name cannot be empty")

    if not (0 <= report_data.compliance_score <= 100):
        raise ValueError("Compliance score must be between 0 and 100")

    try:
        # Create the report
        db_report = models.AnalysisReport(
            document_name=report_data.document_name.strip(),
            compliance_score=report_data.compliance_score,
            document_type=report_data.document_type,
            analysis_result=report_data.analysis_result or {},
            document_embedding=report_data.document_embedding,
        )
        db.add(db_report)
        await db.flush()  # Get the report ID without committing

        # Create findings if provided
        if findings_data:
            for finding_data in findings_data:
                db_finding = models.Finding(
                    report_id=db_report.id,
                    rule_id=finding_data.rule_id,
                    risk=finding_data.risk,
                    personalized_tip=finding_data.personalized_tip,
                    problematic_text=finding_data.problematic_text,
                    confidence_score=finding_data.confidence_score,
                )
                db.add(db_finding)

        await db.commit()
        await db.refresh(db_report)

        # Load findings for the response
        await db.refresh(db_report, ["findings"])

        logger.info("Created analysis report: %s with %d findings", db_report.document_name, len(findings_data or []))
        return db_report

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        await db.rollback()
        logger.error("Failed to create analysis report: %s", e)
        raise


async def find_similar_report(
    db: AsyncSession,
    document_type: str | None,
    exclude_report_id: int | None = None,
    embedding: bytes | None = None,
    threshold: float = 0.85,
) -> models.AnalysisReport | None:
    """Finds a similar report using the vector store, with a fallback to recency."""
    candidate_ids: list[int] = []
    vector_store = get_vector_store()

    if embedding:
        if not vector_store.is_initialized:
            vector_store.initialize_index()

        if vector_store.is_initialized:
            try:
                query_vector = np.frombuffer(embedding, dtype=np.float32)
                if query_vector.size:
                    query_vector = query_vector.reshape(1, -1)
                    for report_id, _ in vector_store.search(query_vector, k=5, threshold=threshold):
                        report_id = int(report_id)
                        if exclude_report_id is not None and report_id == exclude_report_id:
                            continue
                        if report_id not in candidate_ids:
                            candidate_ids.append(report_id)
            except (ValueError, TypeError) as exc:
                logger.warning("Invalid embedding supplied to find_similar_report: %s", exc)

    for candidate_id in candidate_ids:
        candidate = await get_report(db, candidate_id)
        if candidate and (document_type is None or candidate.document_type == document_type):
            return candidate

    for candidate_id in candidate_ids:
        candidate = await get_report(db, candidate_id)
        if candidate:
            return candidate

    query = select(models.AnalysisReport)
    if document_type is not None:
        query = query.where(models.AnalysisReport.document_type == document_type)

    if exclude_report_id is not None:
        query = query.where(models.AnalysisReport.id != exclude_report_id)

    query = query.order_by(models.AnalysisReport.analysis_date.desc())
    result = await db.execute(query)
    return result.scalars().first()


# ... (rest of the file remains the same) ...

# ---------------------------------------------------------------------------
# Dashboard helpers
# ---------------------------------------------------------------------------


async def get_reports(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[models.AnalysisReport]:
    """Return analysis reports with their findings eagerly loaded."""
    query = (
        select(models.AnalysisReport)
        .options(selectinload(models.AnalysisReport.findings))
        .order_by(models.AnalysisReport.analysis_date.desc())
        .offset(max(skip, 0))
        .limit(max(limit, 1))
    )
    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def get_findings_summary(db: AsyncSession) -> list[dict[str, Any]]:
    """Aggregate findings by rule identifier for high level dashboards."""
    query = (
        select(
            models.Finding.rule_id,
            func.count(models.Finding.id).label("count"),
            func.max(models.Finding.confidence_score).label("max_confidence"),
        )
        .group_by(models.Finding.rule_id)
        .order_by(func.count(models.Finding.id).desc())
        .limit(50)
    )
    result = await db.execute(query)
    return [
        {
            "rule_id": row.rule_id,
            "count": row.count,
            "max_confidence": float(row.max_confidence or 0.0),
        }
        for row in result.all()
        if row.rule_id
    ]


def _as_datetime(value: date | None, *, end: bool = False) -> datetime.datetime | None:
    """Convert a date into a naive UTC datetime for filtering."""
    if value is None:
        return None
    if end:
        return datetime.datetime.combine(value, datetime.time.max).replace(microsecond=0)
    return datetime.datetime.combine(value, datetime.time.min)


async def get_total_findings_count(
    db: AsyncSession, *, start_date: date | None = None, end_date: date | None = None, discipline: str | None = None
) -> int:
    """Return the total number of findings in the specified window."""
    query = (
        select(func.count(models.Finding.id))
        .select_from(models.Finding)
        .join(models.AnalysisReport, models.Finding.report_id == models.AnalysisReport.id)
    )

    start_dt = _as_datetime(start_date)
    end_dt = _as_datetime(end_date, end=True)

    if start_dt is not None:
        query = query.where(models.AnalysisReport.analysis_date >= start_dt)
    if end_dt is not None:
        query = query.where(models.AnalysisReport.analysis_date <= end_dt)
    if discipline:
        query = query.where(models.AnalysisReport.discipline == discipline)

    result = await db.execute(query)
    return int(result.scalar_one_or_none() or 0)


async def get_team_habit_summary(
    db: AsyncSession, *, start_date: date | None = None, end_date: date | None = None, discipline: str | None = None
) -> list[schemas.HabitSummary]:
    """Return an aggregate view of team habits based on progress snapshots."""
    # Discipline filtering is not currently tracked for snapshots; placeholder.
    query = select(models.HabitProgressSnapshot)
    if start_date is not None:
        query = query.where(models.HabitProgressSnapshot.snapshot_date >= start_date)
    if end_date is not None:
        query = query.where(models.HabitProgressSnapshot.snapshot_date <= end_date)

    result = await db.execute(query)
    snapshots = list(result.scalars().all())
    if not snapshots:
        return []

    aggregate: dict[str, float] = {f"habit_{i}": 0.0 for i in range(1, 8)}
    for snapshot in snapshots:
        aggregate["habit_1"] += snapshot.habit_1_percentage
        aggregate["habit_2"] += snapshot.habit_2_percentage
        aggregate["habit_3"] += snapshot.habit_3_percentage
        aggregate["habit_4"] += snapshot.habit_4_percentage
        aggregate["habit_5"] += snapshot.habit_5_percentage
        aggregate["habit_6"] += snapshot.habit_6_percentage
        aggregate["habit_7"] += snapshot.habit_7_percentage

    denominator = max(len(snapshots), 1)
    summaries: list[schemas.HabitSummary] = []
    for habit_index in range(1, 8):
        habit_id = f"habit_{habit_index}"
        average = aggregate[habit_id] / denominator
        summaries.append(schemas.HabitSummary(habit_name=f"Habit {habit_index}", count=int(round(average))))
    return summaries


async def get_clinician_habit_breakdown(
    db: AsyncSession, *, start_date: date | None = None, end_date: date | None = None, discipline: str | None = None
) -> list[schemas.ClinicianHabitBreakdown]:
    """Return per-clinician habit focus based on their latest snapshots."""
    query = (
        select(models.HabitProgressSnapshot, models.User)
        .join(models.User, models.HabitProgressSnapshot.user_id == models.User.id)
        .order_by(models.HabitProgressSnapshot.user_id, models.HabitProgressSnapshot.snapshot_date.desc())
    )

    if start_date is not None:
        query = query.where(models.HabitProgressSnapshot.snapshot_date >= start_date)
    if end_date is not None:
        query = query.where(models.HabitProgressSnapshot.snapshot_date <= end_date)

    result = await db.execute(query)
    latest_snapshots: dict[int, tuple[models.HabitProgressSnapshot, models.User]] = {}
    for snapshot, user in result.all():
        if discipline and user.license_key != discipline:
            continue
        latest_snapshots.setdefault(user.id, (snapshot, user))

    breakdown: list[schemas.ClinicianHabitBreakdown] = []
    for _user_id, (snapshot, user) in latest_snapshots.items():
        habit_percentages = [
            ("habit_1", snapshot.habit_1_percentage),
            ("habit_2", snapshot.habit_2_percentage),
            ("habit_3", snapshot.habit_3_percentage),
            ("habit_4", snapshot.habit_4_percentage),
            ("habit_5", snapshot.habit_5_percentage),
            ("habit_6", snapshot.habit_6_percentage),
            ("habit_7", snapshot.habit_7_percentage),
        ]
        habit_percentages.sort(key=lambda item: item[1], reverse=True)
        for habit_id, percentage in habit_percentages[:3]:
            if percentage <= 0:
                continue
            breakdown.append(
                schemas.ClinicianHabitBreakdown(
                    clinician_name=user.username,
                    habit_name=f"Habit {habit_id.split('_')[-1]}",
                    count=int(round(percentage)),
                )
            )

    return breakdown


async def get_habit_trend_data(
    db: AsyncSession, *, start_date: date | None = None, end_date: date | None = None
) -> list[schemas.HabitTrendPoint]:
    """Return total findings trend over time using habit snapshots."""
    query = select(
        models.HabitProgressSnapshot.snapshot_date,
        func.sum(models.HabitProgressSnapshot.total_findings).label("total_findings"),
    ).group_by(models.HabitProgressSnapshot.snapshot_date)

    if start_date is not None:
        query = query.where(models.HabitProgressSnapshot.snapshot_date >= start_date)
    if end_date is not None:
        query = query.where(models.HabitProgressSnapshot.snapshot_date <= end_date)

    query = query.order_by(models.HabitProgressSnapshot.snapshot_date)
    result = await db.execute(query)
    return [schemas.HabitTrendPoint(date=row.snapshot_date, count=int(row.total_findings)) for row in result.all()]


# ---------------------------------------------------------------------------
# Habit utilities for individual tracking
# ---------------------------------------------------------------------------


async def get_user_habit_goals(db: AsyncSession, user_id: int, active_only: bool = True) -> list[models.HabitGoal]:
    """Return goals for the given user."""
    query = select(models.HabitGoal).where(models.HabitGoal.user_id == user_id)
    if active_only:
        query = query.where(models.HabitGoal.status == "active")
    query = query.order_by(models.HabitGoal.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_personal_habit_goal(db: AsyncSession, user_id: int, goal_data: dict[str, Any]) -> models.HabitGoal:
    """Create a personal habit goal for a user."""
    habit_identifier = goal_data.get("habit_id")
    habit_number: int | None = None
    if isinstance(habit_identifier, str) and habit_identifier.startswith("habit_"):
        try:
            habit_number = int(habit_identifier.split("_")[-1])
        except ValueError:
            habit_number = None

    db_goal = models.HabitGoal(
        user_id=user_id,
        title=goal_data.get("title") or goal_data.get("habit_name", "Documentation Goal"),
        description=goal_data.get("description"),
        habit_number=habit_number,
        target_value=float(goal_data.get("target_value", 0.0)) if goal_data.get("target_value") is not None else None,
        target_date=goal_data.get("target_date"),
        status=goal_data.get("status", "active"),
    )
    db.add(db_goal)
    try:
        await db.commit()
    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        await db.rollback()
        raise
    await db.refresh(db_goal)
    db_goal.habit_id = habit_identifier
    db_goal.habit_name = goal_data.get("habit_name")
    db_goal.goal_type = goal_data.get("goal_type")
    db_goal.target_value = db_goal.target_value
    db_goal.target_date = db_goal.target_date
    return db_goal


async def create_habit_goal(db: AsyncSession, user_id: int, goal_data: dict[str, Any]) -> models.HabitGoal:
    """Compatibility wrapper for legacy API."""
    return await create_personal_habit_goal(db, user_id, goal_data)


async def update_habit_goal_progress(
    db: AsyncSession, goal_id: int, progress: int, user_id: int
) -> models.HabitGoal | None:
    """Update the progress percentage for a user's goal."""
    query = select(models.HabitGoal).where(models.HabitGoal.id == goal_id, models.HabitGoal.user_id == user_id)
    result = await db.execute(query)
    goal = result.scalars().first()
    if goal is None:
        return None

    goal.progress = progress
    goal.updated_at = datetime.datetime.utcnow()

    await db.commit()
    await db.refresh(goal)
    return goal


async def get_user_achievements(db: AsyncSession, user_id: int, category: str | None = None) -> list[dict[str, Any]]:
    """Return achievements for a user grouped by category."""
    query = select(models.HabitAchievement).where(models.HabitAchievement.user_id == user_id)
    if category:
        query = query.where(models.HabitAchievement.category == category)
    query = query.order_by(models.HabitAchievement.earned_at.desc())
    result = await db.execute(query)

    achievements = []
    for row in result.scalars().all():
        achievements.append(
            {
                "id": row.id,
                "user_id": row.user_id,
                "category": row.category,
                "achievement_id": row.achievement_id,
                "title": row.title,
                "description": row.description,
                "icon": row.icon,
                "earned_at": row.earned_at,
                "achievement_name": row.title,
                "achievement_description": row.description,
                "achievement_icon": row.icon,
                "earned_date": row.earned_at,
                "points_earned": 10,
                "metadata": {},
            }
        )
    return achievements


async def get_user_habit_statistics(db: AsyncSession, user_id: int, days_back: int) -> dict[str, Any]:
    """Return high level habit statistics for a user."""
    cutoff = datetime.datetime.utcnow() - timedelta(days=days_back)

    goals = await get_user_habit_goals(db, user_id, active_only=False)
    active_goals = [goal for goal in goals if goal.status == "active"]
    completed_goals = [goal for goal in goals if goal.status == "completed"]

    achievements = await get_user_achievements(db, user_id)

    snapshot_query = (
        select(models.HabitProgressSnapshot)
        .where(models.HabitProgressSnapshot.user_id == user_id)
        .order_by(models.HabitProgressSnapshot.snapshot_date.desc())
    )
    result = await db.execute(snapshot_query)
    snapshots = [snapshot for snapshot in result.scalars().all() if snapshot.snapshot_date >= cutoff.date()]

    total_findings = sum(snapshot.total_findings for snapshot in snapshots)
    average_consistency = (
        sum(snapshot.consistency_score for snapshot in snapshots) / len(snapshots) if snapshots else 0.0
    )

    return {
        "summary": {
            "total_goals": len(goals),
            "active_goals": len(active_goals),
            "completed_goals": len(completed_goals),
            "total_achievements": len(achievements),
        },
        "recent_activity": {
            "snapshots_recorded": len(snapshots),
            "total_findings": total_findings,
            "average_consistency_score": round(average_consistency, 2),
            "days_analyzed": days_back,
        },
        "achievement_categories": Counter(achievement["category"] for achievement in achievements),
    }


async def create_habit_progress_snapshot(
    db: AsyncSession, user_id: int, snapshot_data: dict[str, Any]
) -> models.HabitProgressSnapshot:
    """Persist a habit progress snapshot for a user.

    Args:
        db: Database session
        user_id: ID of the user
        snapshot_data: Snapshot data dictionary

    Returns:
        models.HabitProgressSnapshot: The created snapshot

    Raises:
        ValueError: If snapshot data is invalid
        sqlalchemy.exc.SQLAlchemyError: For database errors
    """
    if user_id <= 0:
        raise ValueError("User ID must be positive")

    habit_breakdown = snapshot_data.get("habit_breakdown", {})

    # Validate habit percentages
    for habit_num in range(1, 8):
        habit_key = f"habit_{habit_num}"
        percentage = habit_breakdown.get(habit_key, 0.0)
        if not (0.0 <= percentage <= 100.0):
            raise ValueError(f"Habit {habit_num} percentage must be between 0 and 100")
    snapshot = models.HabitProgressSnapshot(
        user_id=user_id,
        snapshot_date=datetime.datetime.utcnow().date(),
        habit_1_percentage=float(habit_breakdown.get("habit_1", 0.0)),
        habit_2_percentage=float(habit_breakdown.get("habit_2", 0.0)),
        habit_3_percentage=float(habit_breakdown.get("habit_3", 0.0)),
        habit_4_percentage=float(habit_breakdown.get("habit_4", 0.0)),
        habit_5_percentage=float(habit_breakdown.get("habit_5", 0.0)),
        habit_6_percentage=float(habit_breakdown.get("habit_6", 0.0)),
        habit_7_percentage=float(habit_breakdown.get("habit_7", 0.0)),
        total_findings=int(snapshot_data.get("total_findings", 0)),
        overall_progress_score=float(snapshot_data.get("mastery_score", 0.0)),
        improvement_rate=float(
            snapshot_data.get("improvement_trend", {}).get("rate", 0.0)
            if isinstance(snapshot_data.get("improvement_trend"), dict)
            else 0.0
        ),
        consistency_score=float(snapshot_data.get("consistency_score", 0.0)),
    )
    db.add(snapshot)
    try:
        await db.commit()
    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        await db.rollback()
        raise
    await db.refresh(snapshot)

    # Provide convenient attributes expected by the API layer.
    snapshot.mastery_score = snapshot.overall_progress_score
    snapshot.primary_focus_habit = snapshot_data.get("primary_focus_habit")

    return snapshot


# ---------------------------------------------------------------------------
# Feedback annotations
# ---------------------------------------------------------------------------


async def create_feedback_annotation(
    db: AsyncSession, feedback: schemas.FeedbackAnnotationCreate, user_id: int
) -> models.FeedbackAnnotation:
    """Persist a feedback annotation for a finding."""
    db_feedback = models.FeedbackAnnotation(
        finding_id=int(feedback.finding_id),
        user_id=user_id,
        is_correct=feedback.is_correct,
        user_comment=feedback.user_comment,
        correction=feedback.correction,
        feedback_type=feedback.feedback_type,
    )
    db.add(db_feedback)
    try:
        await db.commit()
    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        await db.rollback()
        raise
    await db.refresh(db_feedback)
    return db_feedback


# ---------------------------------------------------------------------------
# Individual tracker helpers (placeholder implementations)
# ---------------------------------------------------------------------------


async def get_user_reports_with_findings(
    db: AsyncSession, user_id: int, start_date: datetime.datetime | None = None
) -> list[models.AnalysisReport]:
    """Fetch analysis reports associated with a user.

    Current datasets do not persist a user relationship on reports, so this
    returns all recent reports as a best-effort placeholder for the tracker.
    """
    query = select(models.AnalysisReport).options(selectinload(models.AnalysisReport.findings))
    if start_date is not None:
        query = query.where(models.AnalysisReport.analysis_date >= start_date)

    result = await db.execute(query.order_by(models.AnalysisReport.analysis_date.desc()))
    return list(result.scalars().unique().all())


# ---------------------------------------------------------------------------
# Bulk Operations for Performance
# ---------------------------------------------------------------------------


async def bulk_create_findings(
    db: AsyncSession, report_id: int, findings_data: list[schemas.FindingCreate]
) -> list[models.Finding]:
    """Create multiple findings for a report in a single transaction.

    Args:
        db: Database session
        report_id: ID of the report
        findings_data: List of finding creation data

    Returns:
        list[models.Finding]: List of created findings

    Raises:
        ValueError: If input data is invalid
        sqlalchemy.exc.SQLAlchemyError: For database errors
    """
    if report_id <= 0:
        raise ValueError("Report ID must be positive")

    if not findings_data:
        return []

    try:
        findings = []
        for finding_data in findings_data:
            # Validate finding data
            if not finding_data.rule_id or not finding_data.rule_id.strip():
                raise ValueError("Rule ID cannot be empty")

            if finding_data.risk not in ["High", "Medium", "Low"]:
                raise ValueError("Risk must be High, Medium, or Low")

            if not (0.0 <= finding_data.confidence_score <= 1.0):
                raise ValueError("Confidence score must be between 0.0 and 1.0")

            db_finding = models.Finding(
                report_id=report_id,
                rule_id=finding_data.rule_id.strip(),
                risk=finding_data.risk,
                personalized_tip=finding_data.personalized_tip,
                problematic_text=finding_data.problematic_text,
                confidence_score=finding_data.confidence_score,
            )
            findings.append(db_finding)

        # Add all findings in bulk
        db.add_all(findings)
        await db.commit()

        # Refresh all findings
        for finding in findings:
            await db.refresh(finding)

        logger.info("Created %d findings for report %d", len(findings), report_id)
        return findings

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        await db.rollback()
        logger.error("Failed to bulk create findings for report %d: %s", report_id, e)
        raise


async def bulk_update_user_preferences(db: AsyncSession, user_updates: list[dict[str, Any]]) -> int:
    """Update multiple user preferences in a single transaction.

    Args:
        db: Database session
        user_updates: List of user update dictionaries with 'user_id' and update fields

    Returns:
        int: Number of users updated

    Raises:
        ValueError: If update data is invalid
        sqlalchemy.exc.SQLAlchemyError: For database errors
    """
    if not user_updates:
        return 0

    try:
        updated_count = 0
        for update_data in user_updates:
            user_id = update_data.get("user_id")
            if not user_id or user_id <= 0:
                continue

            # Get the user
            user = await get_user(db, user_id)
            if not user:
                continue

            # Update allowed fields
            updated = False
            if "is_active" in update_data:
                user.is_active = bool(update_data["is_active"])
                updated = True

            if "license_key" in update_data:
                user.license_key = update_data["license_key"]
                updated = True

            if updated:
                user.updated_at = datetime.datetime.now(datetime.UTC)
                updated_count += 1

        if updated_count > 0:
            await db.commit()
            logger.info("Bulk updated %d users", updated_count)

        return updated_count

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        await db.rollback()
        logger.error("Failed to bulk update users: %s", e)
        raise


# ---------------------------------------------------------------------------
# Database Health and Maintenance
# ---------------------------------------------------------------------------


async def get_database_health(db: AsyncSession) -> dict[str, Any]:
    """Get database health statistics and metrics.

    Args:
        db: Database session

    Returns:
        dict[str, Any]: Database health metrics
    """
    try:
        # Get table counts
        user_count = await db.scalar(select(func.count(models.User.id)))
        report_count = await db.scalar(select(func.count(models.AnalysisReport.id)))
        finding_count = await db.scalar(select(func.count(models.Finding.id)))
        rubric_count = await db.scalar(select(func.count(models.ComplianceRubric.id)))

        # Get recent activity
        recent_cutoff = datetime.datetime.now(datetime.UTC) - timedelta(days=7)
        recent_reports = await db.scalar(
            select(func.count(models.AnalysisReport.id)).where(models.AnalysisReport.analysis_date >= recent_cutoff)
        )

        # Calculate average compliance score
        avg_score = await db.scalar(
            select(func.avg(models.AnalysisReport.compliance_score)).where(
                models.AnalysisReport.compliance_score.is_not(None)
            )
        )

        return {
            "status": "healthy",
            "table_counts": {
                "users": user_count or 0,
                "reports": report_count or 0,
                "findings": finding_count or 0,
                "rubrics": rubric_count or 0,
            },
            "recent_activity": {
                "reports_last_7_days": recent_reports or 0,
            },
            "metrics": {
                "average_compliance_score": round(float(avg_score or 0.0), 2),
                "findings_per_report": round((finding_count or 0) / max(report_count or 1, 1), 2),
            },
            "last_checked": datetime.datetime.now(datetime.UTC).isoformat(),
        }

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        logger.error("Failed to get database health: %s", e)
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_checked": datetime.datetime.now(datetime.UTC).isoformat(),
        }


async def cleanup_old_data(db: AsyncSession, days_to_keep: int = 365, dry_run: bool = True) -> dict[str, int]:
    """Clean up old data from the database.

    Args:
        db: Database session
        days_to_keep: Number of days of data to keep
        dry_run: If True, only count what would be deleted

    Returns:
        dict[str, int]: Counts of records that would be/were deleted
    """
    cutoff_date = datetime.datetime.now(datetime.UTC) - timedelta(days=days_to_keep)

    try:
        # Count old reports
        old_reports_query = select(func.count(models.AnalysisReport.id)).where(
            models.AnalysisReport.analysis_date < cutoff_date
        )
        old_reports_count = await db.scalar(old_reports_query) or 0

        # Count old snapshots
        old_snapshots_query = select(func.count(models.HabitProgressSnapshot.id)).where(
            models.HabitProgressSnapshot.snapshot_date < cutoff_date.date()
        )
        old_snapshots_count = await db.scalar(old_snapshots_query) or 0

        cleanup_counts = {
            "reports": old_reports_count,
            "snapshots": old_snapshots_count,
        }

        if not dry_run and (old_reports_count > 0 or old_snapshots_count > 0):
            # Delete old reports (findings will be cascade deleted)
            if old_reports_count > 0:
                await db.execute(
                    models.AnalysisReport.__table__.delete().where(models.AnalysisReport.analysis_date < cutoff_date)
                )

            # Delete old snapshots
            if old_snapshots_count > 0:
                await db.execute(
                    models.HabitProgressSnapshot.__table__.delete().where(
                        models.HabitProgressSnapshot.snapshot_date < cutoff_date.date()
                    )
                )

            await db.commit()
            logger.info("Cleaned up old data: %d reports, %d snapshots", old_reports_count, old_snapshots_count)

        return cleanup_counts

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        if not dry_run:
            await db.rollback()
        logger.error("Failed to cleanup old data: %s", e)
        raise
