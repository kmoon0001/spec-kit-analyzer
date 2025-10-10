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
    result = await db.execute(
        select(models.User).where(models.User.id == user_id))
    return result.scalars().first()

default_admin_flag = False

async def get_user_by_username(db: AsyncSession, username: str) -> models.User | None:
    result = await db.execute(
        select(models.User).where(models.User.username == username))
    return result.scalars().first()

async def create_user(
    db: AsyncSession,
    user: schemas.UserCreate,
    hashed_password: str,
    *,
    is_admin: bool | None = None) -> models.User:
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=is_admin if is_admin is not None else getattr(user, "is_admin", False))
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def change_user_password(
    db: AsyncSession,
    user: models.User,
    new_hashed_password: str) -> models.User:
    user.hashed_password = new_hashed_password  # type: ignore[attr-defined]
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# ---------------------------------------------------------------------------
# Rubric management
# ---------------------------------------------------------------------------

async def create_rubric(
    db: AsyncSession, rubric: schemas.RubricCreate) -> models.ComplianceRubric:
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
    db: AsyncSession, skip: int = 0, limit: int = 100) -> list[models.ComplianceRubric]:
    """Return a page of rubrics."""
    query = (
        select(models.ComplianceRubric)
        .order_by(models.ComplianceRubric.name)
        .offset(max(skip, 0))
        .limit(max(limit, 1))
    )
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_rubric(
    db: AsyncSession, rubric_id: int) -> models.ComplianceRubric | None:
    """Return a single rubric by identifier."""
    query = select(models.ComplianceRubric).where(
        models.ComplianceRubric.id == rubric_id)
    result = await db.execute(query)
    return result.scalars().first()

async def update_rubric(
    db: AsyncSession, rubric_id: int, rubric: schemas.RubricCreate) -> models.ComplianceRubric | None:
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

async def delete_rubric(db: AsyncSession, rubric_id: int) -> None:
    """Delete a rubric if it exists."""
    db_rubric = await get_rubric(db, rubric_id)
    if db_rubric is None:
        return
    await db.delete(db_rubric)
    await db.commit()

async def get_dashboard_statistics(db: AsyncSession) -> dict[str, Any]:
    """Computes and returns key statistics for the main dashboard."""
    total_docs_query = select(func.count(models.AnalysisReport.id))
    total_docs_result = await db.execute(total_docs_query)
    total_documents_analyzed = total_docs_result.scalar_one_or_none() or 0

    avg_score_query = select(func.avg(models.AnalysisReport.compliance_score))
    avg_score_result = await db.execute(avg_score_query)
    overall_compliance_score = avg_score_result.scalar_one_or_none() or 0.0

    category_query = (
        select(
            models.AnalysisReport.document_type,
            func.avg(models.AnalysisReport.compliance_score).label("average_score"))
        .group_by(models.AnalysisReport.document_type)
        .order_by(models.AnalysisReport.document_type)
    )
    category_result = await db.execute(category_query)
    compliance_by_category = {row.document_type: row.average_score for row in category_result.all() if row.document_type}

    return {
        "total_documents_analyzed": total_documents_analyzed,
        "overall_compliance_score": overall_compliance_score,
        "compliance_by_category": compliance_by_category,
    }

async def get_organizational_metrics(db: AsyncSession, days_back: int) -> dict[str, Any]:
    """Computes high-level organizational metrics."""
    cutoff_date = datetime.datetime.now(datetime.UTC) - timedelta(days=days_back)

    report_query = select(models.AnalysisReport).filter(models.AnalysisReport.analysis_date >= cutoff_date)
    reports = list((await db.execute(report_query.options(selectinload(models.AnalysisReport.findings)))).scalars().unique().all())

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
            func.count(models.AnalysisReport.id).label("user_count"))
        .filter(models.AnalysisReport.analysis_date >= cutoff_date)
        .group_by(models.AnalysisReport.analysis_result["discipline"].as_string())
    )
    result = await db.execute(query)
    return {row.discipline: {"avg_compliance_score": row.avg_score, "user_count": row.user_count} for row in result.all()}

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
        {"habit_name": "Put First Things First", "percentage_of_findings": 20.0, "priority": "high", "affected_users": 10, "training_focus": "Time management and prioritization"},
        {"habit_name": "Be Proactive", "percentage_of_findings": 25.0, "priority": "medium", "affected_users": 15, "training_focus": "Identifying and addressing potential issues"},
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

        week_reports = [
            report
            for report in reports
            if week_start <= _as_aware(report.analysis_date) < week_end
        ]

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
            })

    return trends

async def get_benchmark_data(db: AsyncSession) -> dict[str, Any]:
    """Get benchmark data for compliance score percentiles."""
    try:
        # Query all compliance scores from AnalysisReport
        result = await db.execute(
            select(models.AnalysisReport.compliance_score)
            .where(models.AnalysisReport.compliance_score.is_not(None))
        )
        scores = [row[0] for row in result.fetchall()]
        
        if not scores:
            # Return default benchmarks if no data
            return {
                "compliance_score_percentiles": {
                    "p25": 70.0,
                    "p50": 80.0,
                    "p75": 90.0,
                    "p90": 95.0
                },
                "total_analyses": 0
            }
        
        # Calculate percentiles
        import numpy as np
        percentiles = {
            "p25": float(np.percentile(scores, 25)),
            "p50": float(np.percentile(scores, 50)),
            "p75": float(np.percentile(scores, 75)),
            "p90": float(np.percentile(scores, 90))
        }
        
        return {
            "compliance_score_percentiles": percentiles,
            "total_analyses": len(scores)
        }
        
    except Exception as e:
        logger.error(f"Error getting benchmark data: {e}")
        # Return default benchmarks on error
        return {
            "compliance_score_percentiles": {
                "p25": 70.0,
                "p50": 80.0,
                "p75": 90.0,
                "p90": 95.0
            },
            "total_analyses": 0
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
    """Fetches a single analysis report with its findings eagerly loaded."""
    query = (
        select(models.AnalysisReport)
        .options(selectinload(models.AnalysisReport.findings))
        .where(models.AnalysisReport.id == report_id)
    )
    result = await db.execute(query)
    return result.scalars().first()

async def find_similar_report(
    db: AsyncSession,
    document_type: str | None,
    exclude_report_id: int | None = None,
    embedding: bytes | None = None,
    threshold: float = 0.85) -> models.AnalysisReport | None:
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

async def get_reports(
    db: AsyncSession, skip: int = 0, limit: int = 100) -> list[models.AnalysisReport]:
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
            func.max(models.Finding.confidence_score).label("max_confidence"))
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

def _as_datetime(
    value: date | None, *, end: bool = False) -> datetime.datetime | None:
    """Convert a date into a naive UTC datetime for filtering."""
    if value is None:
        return None
    if end:
        return datetime.datetime.combine(
            value, datetime.time.max).replace(microsecond=0)
    return datetime.datetime.combine(value, datetime.time.min)

async def get_total_findings_count(
    db: AsyncSession,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    discipline: str | None = None) -> int:
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
    db: AsyncSession,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    discipline: str | None = None) -> list[schemas.HabitSummary]:
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
        summaries.append(
            schemas.HabitSummary(
                habit_name=f"Habit {habit_index}",
                count=int(round(average))))
    return summaries

async def get_clinician_habit_breakdown(
    db: AsyncSession,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    discipline: str | None = None) -> list[schemas.ClinicianHabitBreakdown]:
    """Return per-clinician habit focus based on their latest snapshots."""
    query = (
        select(models.HabitProgressSnapshot, models.User)
        .join(models.User, models.HabitProgressSnapshot.user_id == models.User.id)
        .order_by(
            models.HabitProgressSnapshot.user_id,
            models.HabitProgressSnapshot.snapshot_date.desc())
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
                    count=int(round(percentage))))

    return breakdown

async def get_habit_trend_data(
    db: AsyncSession,
    *,
    start_date: date | None = None,
    end_date: date | None = None) -> list[schemas.HabitTrendPoint]:
    """Return total findings trend over time using habit snapshots."""
    query = select(
        models.HabitProgressSnapshot.snapshot_date,
        func.sum(models.HabitProgressSnapshot.total_findings).label("total_findings")).group_by(models.HabitProgressSnapshot.snapshot_date)

    if start_date is not None:
        query = query.where(models.HabitProgressSnapshot.snapshot_date >= start_date)
    if end_date is not None:
        query = query.where(models.HabitProgressSnapshot.snapshot_date <= end_date)

    query = query.order_by(models.HabitProgressSnapshot.snapshot_date)
    result = await db.execute(query)
    return [
        schemas.HabitTrendPoint(date=row.snapshot_date, count=int(row.total_findings))
        for row in result.all()
    ]

# ---------------------------------------------------------------------------
# Habit utilities for individual tracking
# ---------------------------------------------------------------------------

async def get_user_habit_goals(
    db: AsyncSession, user_id: int, active_only: bool = True) -> list[models.HabitGoal]:
    """Return goals for the given user."""
    query = select(models.HabitGoal).where(models.HabitGoal.user_id == user_id)
    if active_only:
        query = query.where(models.HabitGoal.status == "active")
    query = query.order_by(models.HabitGoal.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())

async def create_personal_habit_goal(
    db: AsyncSession, user_id: int, goal_data: dict[str, Any]) -> models.HabitGoal:
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
        target_value=float(goal_data.get("target_value", 0.0))
        if goal_data.get("target_value") is not None
        else None,
        target_date=goal_data.get("target_date"),
        status=goal_data.get("status", "active"))
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

async def create_habit_goal(
    db: AsyncSession, user_id: int, goal_data: dict[str, Any]) -> models.HabitGoal:
    """Compatibility wrapper for legacy API."""
    return await create_personal_habit_goal(db, user_id, goal_data)

async def update_habit_goal_progress(
    db: AsyncSession, goal_id: int, progress: int, user_id: int) -> models.HabitGoal | None:
    """Update the progress percentage for a user's goal."""
    query = select(models.HabitGoal).where(
        models.HabitGoal.id == goal_id, models.HabitGoal.user_id == user_id)
    result = await db.execute(query)
    goal = result.scalars().first()
    if goal is None:
        return None

    goal.progress = progress
    goal.updated_at = datetime.datetime.utcnow()

    await db.commit()
    await db.refresh(goal)
    return goal

async def get_user_achievements(
    db: AsyncSession, user_id: int, category: str | None = None) -> list[dict[str, Any]]:
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
            })
    return achievements

async def get_user_habit_statistics(
    db: AsyncSession, user_id: int, days_back: int) -> dict[str, Any]:
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
    snapshots = [
        snapshot
        for snapshot in result.scalars().all()
        if snapshot.snapshot_date >= cutoff.date()
    ]

    total_findings = sum(snapshot.total_findings for snapshot in snapshots)
    average_consistency = (
        sum(snapshot.consistency_score for snapshot in snapshots) / len(snapshots)
        if snapshots
        else 0.0
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
        "achievement_categories": Counter(
            achievement["category"] for achievement in achievements
        ),
    }

async def create_habit_progress_snapshot(
    db: AsyncSession, user_id: int, snapshot_data: dict[str, Any]) -> models.HabitProgressSnapshot:
    """Persist a habit progress snapshot for a user."""
    habit_breakdown = snapshot_data.get("habit_breakdown", {})
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
            else 0.0),
        consistency_score=float(snapshot_data.get("consistency_score", 0.0)))
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
    db: AsyncSession,
    feedback: schemas.FeedbackAnnotationCreate,
    user_id: int) -> models.FeedbackAnnotation:
    """Persist a feedback annotation for a finding."""
    db_feedback = models.FeedbackAnnotation(
        finding_id=int(feedback.finding_id),
        user_id=user_id,
        is_correct=feedback.is_correct,
        user_comment=feedback.user_comment,
        correction=feedback.correction,
        feedback_type=feedback.feedback_type)
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
    db: AsyncSession,
    user_id: int,
    start_date: datetime.datetime | None = None) -> list[models.AnalysisReport]:
    """Fetch analysis reports associated with a user.

    Current datasets do not persist a user relationship on reports, so this
    returns all recent reports as a best-effort placeholder for the tracker.
    """
    query = select(models.AnalysisReport).options(
        selectinload(models.AnalysisReport.findings))
    if start_date is not None:
        query = query.where(models.AnalysisReport.analysis_date >= start_date)

    result = await db.execute(query.order_by(models.AnalysisReport.analysis_date.desc()))
    return list(result.scalars().unique().all())

