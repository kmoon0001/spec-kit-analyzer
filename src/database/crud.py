"""
Database CRUD operations for the Therapy Compliance Analyzer.

Provides async database operations for users, rubrics, reports, and findings.
"""

import datetime
import logging
import numpy as np
from typing import List, Optional, Dict, Any

from sqlalchemy import delete, select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from . import models, schemas
from ..core.vector_store import get_vector_store

logger = logging.getLogger(__name__)

# ... (existing user, rubric, feedback functions remain the same) ...

async def get_organizational_metrics(db: AsyncSession, days_back: int) -> Dict[str, Any]:
    """Computes high-level organizational metrics."""
    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_back)
    
    report_query = select(models.AnalysisReport).filter(models.AnalysisReport.analysis_date >= cutoff_date)
    reports = list((await db.execute(report_query)).scalars().all())
    
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

async def get_discipline_breakdown(db: AsyncSession, days_back: int) -> Dict[str, Dict[str, Any]]:
    """Computes compliance metrics broken down by discipline."""
    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_back)
    
    query = (
        select(
            models.AnalysisReport.discipline,
            func.avg(models.AnalysisReport.compliance_score).label("avg_score"),
            func.count(models.AnalysisReport.user_id).label("user_count")
        )
        .filter(models.AnalysisReport.analysis_date >= cutoff_date)
        .group_by(models.AnalysisReport.discipline)
    )
    result = await db.execute(query)
    return {row.discipline: {"avg_compliance_score": row.avg_score, "user_count": row.user_count} for row in result.all()}

async def get_team_habit_breakdown(db: AsyncSession, days_back: int) -> Dict[str, Dict[str, Any]]:
    """Computes the distribution of findings related to habits."""
    # This is a simplified example. A real implementation would join with a habits table.
    return {
        "habit_1": {"habit_number": 1, "habit_name": "Be Proactive", "percentage": 25.0},
        "habit_2": {"habit_number": 2, "habit_name": "Begin with the End in Mind", "percentage": 15.0},
        "habit_3": {"habit_number": 3, "habit_name": "Put First Things First", "percentage": 20.0},
    }

async def get_training_needs(db: AsyncSession, days_back: int) -> List[Dict[str, Any]]:
    """Identifies potential training needs based on finding frequency."""
    # This is a simplified example.
    return [
        {"habit_name": "Put First Things First", "percentage_of_findings": 20.0, "priority": "high", "affected_users": 10, "training_focus": "Time management and prioritization"},
        {"habit_name": "Be Proactive", "percentage_of_findings": 25.0, "priority": "medium", "affected_users": 15, "training_focus": "Identifying and addressing potential issues"},
    ]

async def get_team_performance_trends(db: AsyncSession, days_back: int) -> List[Dict[str, Any]]:
    """Computes team performance trends over time."""
    num_weeks = days_back // 7
    trends = []
    for i in range(num_weeks, 0, -1):
        end_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(weeks=i-1)
        start_date = end_date - datetime.timedelta(weeks=1)
        
        query = (
            select(
                func.avg(models.AnalysisReport.compliance_score).label("avg_score"),
                func.count(models.Finding.id).label("total_findings")
            )
            .join(models.Finding, models.AnalysisReport.id == models.Finding.report_id)
            .filter(and_(models.AnalysisReport.analysis_date >= start_date, models.AnalysisReport.analysis_date < end_date))
        )
        result = (await db.execute(query)).first()
        trends.append({
            "week": num_weeks - i + 1,
            "avg_compliance_score": result.avg_score or 0,
            "total_findings": result.total_findings or 0,
        })
    return trends

async def get_benchmark_data(db: AsyncSession) -> Dict[str, Any]:
    """Computes benchmark data across the organization."""
    query = select(models.AnalysisReport.compliance_score)
    scores = list((await db.execute(query)).scalars().all())
    
    if not scores:
        return {}

    return {
        "total_users_in_benchmark": (await db.execute(select(func.count(models.User.id)))).scalar_one(),
        "compliance_score_percentiles": {
            "p25": np.percentile(scores, 25),
            "p50": np.percentile(scores, 50),
            "p75": np.percentile(scores, 75),
            "p90": np.percentile(scores, 90),
        },
    }

# ... (rest of the file remains the same, including find_similar_report and create_report_and_findings) ...

async def create_feedback_annotation(
    db: AsyncSession, feedback: schemas.FeedbackAnnotationCreate, user_id: int
) -> models.FeedbackAnnotation:
    """Create a new feedback annotation."""
    db_feedback = models.FeedbackAnnotation(**feedback.model_dump(), user_id=user_id)
    db.add(db_feedback)
    await db.commit()
    await db.refresh(db_feedback)
    return db_feedback


async def get_user_by_username(
    db: AsyncSession, username: str
) -> Optional[models.User]:
    """Get user by username."""
    result = await db.execute(
        select(models.User).filter(models.User.username == username)
    )
    return result.scalars().first()


async def get_user(db: AsyncSession, user_id: int) -> Optional[models.User]:
    """Get user by ID."""
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    return result.scalars().first()


async def create_user(
    db: AsyncSession, user: schemas.UserCreate, hashed_password: str
) -> models.User:
    """Create a new user."""
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        is_admin=user.is_admin,
        license_key=user.license_key,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def delete_user(db: AsyncSession, user_id: int) -> None:
    """Delete a user by ID."""
    await db.execute(delete(models.User).where(models.User.id == user_id))
    await db.commit()


async def change_user_password(
    db: AsyncSession, user: models.User, new_hashed_password: str
) -> models.User:
    """Change user password."""
    user.hashed_password = new_hashed_password
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_rubric(
    db: AsyncSession, rubric: schemas.RubricCreate
) -> models.ComplianceRubric:
    """Create a new compliance rubric."""
    db_rubric = models.ComplianceRubric(**rubric.model_dump())
    db.add(db_rubric)
    await db.commit()
    await db.refresh(db_rubric)
    return db_rubric


async def get_rubric(
    db: AsyncSession, rubric_id: int
) -> Optional[models.ComplianceRubric]:
    """Get rubric by ID."""
    result = await db.execute(
        select(models.ComplianceRubric).filter(models.ComplianceRubric.id == rubric_id)
    )
    return result.scalars().first()


async def get_rubrics(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[models.ComplianceRubric]:
    """Get paginated list of rubrics."""
    result = await db.execute(select(models.ComplianceRubric).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_rubric(
    db: AsyncSession, rubric_id: int, rubric: schemas.RubricCreate
) -> Optional[models.ComplianceRubric]:
    """Update an existing rubric."""
    db_rubric = await get_rubric(db, rubric_id)
    if db_rubric:
        for key, value in rubric.model_dump().items():
            setattr(db_rubric, key, value)
        await db.commit()
        await db.refresh(db_rubric)
    return db_rubric


async def delete_rubric(db: AsyncSession, rubric_id: int) -> None:
    """Delete a rubric by ID."""
    await db.execute(
        delete(models.ComplianceRubric).where(models.ComplianceRubric.id == rubric_id)
    )
    await db.commit()


async def create_report(
    db: AsyncSession, report: schemas.ReportCreate
) -> models.AnalysisReport:
    """Create a new analysis report."""
    db_report = models.AnalysisReport(**report.model_dump())
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)
    return db_report


async def get_report(
    db: AsyncSession, report_id: int
) -> Optional[models.AnalysisReport]:
    """Get report by ID."""
    result = await db.execute(
        select(models.AnalysisReport).filter(models.AnalysisReport.id == report_id)
    )
    return result.scalars().first()


async def get_reports(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    document_type: Optional[str] = None,
    min_score: Optional[float] = None,
) -> List[models.AnalysisReport]:
    """
    Retrieve paginated and filtered list of reports.

    Includes eager loading for related findings to prevent N+1 query problems.

    Args:
        db: Database session
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        document_type: Optional filter by document type
        min_score: Optional filter by minimum compliance score

    Returns:
        List of AnalysisReport model instances
    """
    query = select(models.AnalysisReport).options(
        selectinload(models.AnalysisReport.findings)
    )

    if document_type:
        query = query.where(models.AnalysisReport.document_type == document_type)
    if min_score is not None:
        query = query.where(models.AnalysisReport.compliance_score >= min_score)

    query = (
        query.order_by(models.AnalysisReport.analysis_date.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_all_reports_with_embeddings(db: AsyncSession) -> List[models.AnalysisReport]:
    """Fetches all reports that have a document embedding."""
    query = select(models.AnalysisReport).filter(models.AnalysisReport.document_embedding.isnot(None))
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_dashboard_statistics(db: AsyncSession) -> Dict[str, Any]:
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
            func.avg(models.AnalysisReport.compliance_score).label("average_score"),
        )
        .group_by(models.AnalysisReport.document_type)
        .order_by(models.AnalysisReport.document_type)
    )
    category_result = await db.execute(category_query)
    compliance_by_category = {row.document_type: row.average_score for row in category_result.all()}

    return {
        "total_documents_analyzed": total_documents_analyzed,
        "overall_compliance_score": overall_compliance_score,
        "compliance_by_category": compliance_by_category,
    }


async def get_user_analysis_count(db: AsyncSession, user_id: int) -> int:
    """Get total analysis count for a user."""
    result = await db.execute(
        select(func.count(models.AnalysisReport.id)).where(
            models.AnalysisReport.user_id == user_id
        )
    )
    return result.scalar() or 0


async def delete_report(db: AsyncSession, report_id: int) -> None:
    """Delete a report and its associated findings."""
    await db.execute(
        delete(models.Finding).where(models.Finding.report_id == report_id)
    )
    await db.execute(
        delete(models.AnalysisReport).where(models.AnalysisReport.id == report_id)
    )
    await db.commit()


async def delete_reports_older_than(db: AsyncSession, days: int) -> int:
    """
    Delete reports older than specified days.

    Args:
        db: Database session
        days: Number of days threshold

    Returns:
        Number of reports deleted
    """
    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=days
    )

    # Find report IDs to delete
    reports_to_delete_query = select(models.AnalysisReport.id).filter(
        models.AnalysisReport.analysis_date < cutoff_date
    )
    reports_to_delete_result = await db.execute(reports_to_delete_query)
    report_ids_to_delete = list(reports_to_delete_result.scalars().all())

    if report_ids_to_delete:
        # Delete findings associated with these reports
        await db.execute(
            delete(models.Finding).where(
                models.Finding.report_id.in_(report_ids_to_delete)
            )
        )
        # Then delete the reports
        result = await db.execute(
            delete(models.AnalysisReport).filter(
                models.AnalysisReport.analysis_date < cutoff_date
            )
        )
        await db.commit()
        return result.rowcount
    return 0


async def find_similar_report(
    db: AsyncSession,
    document_type: str,
    exclude_report_id: int,
    embedding: Optional[bytes] = None,
    threshold: float = 0.9,
) -> Optional[models.AnalysisReport]:
    """Find a similar report based on semantic similarity of document embeddings."""
    if not embedding:
        logger.info("No embedding provided, falling back to basic search.")
        try:
            query = (
                select(models.AnalysisReport)
                .where(
                    models.AnalysisReport.document_type == document_type,
                    models.AnalysisReport.id != exclude_report_id,
                )
                .order_by(models.AnalysisReport.analysis_date.desc())
                .limit(1)
            )
            result = await db.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error in fallback similar report search: {e}")
            return None

    vector_store = get_vector_store()
    query_vector = np.frombuffer(embedding, dtype=np.float32).reshape(1, -1)
    
    # Search for the 5 most similar reports (k=5)
    similar_items = vector_store.search(query_vector, k=5, threshold=threshold)
    
    if not similar_items:
        return None

    # Filter out the original report from the search results
    similar_report_ids = [item_id for item_id, _ in similar_items if item_id != exclude_report_id]

    if not similar_report_ids:
        return None

    # Retrieve the most similar report from the database
    most_similar_report_id = similar_report_ids[0]
    return await get_report(db, most_similar_report_id)


async def create_report_and_findings(
    db: AsyncSession,
    report_data: schemas.ReportCreate,
    findings_data: List[schemas.FindingCreate],
) -> models.AnalysisReport:
    """
    Create a report with associated findings in a single transaction.
    Also adds the new report's embedding to the vector store.
    """
    db_report = models.AnalysisReport(
        document_name=report_data.document_name,
        compliance_score=report_data.compliance_score,
        analysis_result=report_data.analysis_result,
        document_embedding=report_data.document_embedding,
    )
    db.add(db_report)
    await db.flush()  # Flush to get the report ID before adding findings

    for finding_data in findings_data:
        db_finding = models.Finding(
            report_id=db_report.id,
            rule_id=finding_data.rule_id,
            risk=finding_data.risk,
            personalized_tip=finding_data.personalized_tip,
            problematic_text=finding_data.problematic_text,
        )
        db.add(db_finding)

    # Add the new report to the vector store
    if db_report.document_embedding:
        vector_store = get_vector_store()
        embedding = np.frombuffer(db_report.document_embedding, dtype=np.float32).reshape(1, -1)
        vector_store.add_vectors(embedding, [db_report.id])

    await db.commit()
    await db.refresh(db_report)
    return db_report


# Individual Habit Tracking CRUD Operations


async def get_user_reports_with_findings(
    db: AsyncSession,
    user_id: int,
    start_date: Optional[datetime.datetime] = None,
    limit: int = 100,
) -> List[models.AnalysisReport]:
    """
    Get user's analysis reports with findings for habit tracking.

    Args:
        db: Database session
        user_id: User ID
        start_date: Optional start date filter
        limit: Maximum number of reports

    Returns:
        List of analysis reports with findings
    """
    query = (
        select(models.AnalysisReport)
        .options(selectinload(models.AnalysisReport.findings))
        .filter(models.AnalysisReport.user_id == user_id)
    )

    if start_date:
        query = query.filter(models.AnalysisReport.analysis_date >= start_date)

    query = query.order_by(models.AnalysisReport.analysis_date.desc()).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


async def create_personal_habit_goal(
    db: AsyncSession, user_id: int, goal_data: Dict[str, Any]
) -> models.HabitGoal:
    """Create a personal habit improvement goal."""
    goal = models.HabitGoal(user_id=user_id, **goal_data)
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


async def get_user_habit_goals(
    db: AsyncSession, user_id: int, active_only: bool = True
) -> List[models.HabitGoal]:
    """Get user's habit goals."""
    query = select(models.HabitGoal).filter(models.HabitGoal.user_id == user_id)

    if active_only:
        query = query.filter(models.HabitGoal.status == "active")

    result = await db.execute(query)
    return list(result.scalars().all())


async def update_habit_goal_progress(
    db: AsyncSession, goal_id: int, current_value: float, status: Optional[str] = None
) -> Optional[models.HabitGoal]:
    """Update progress on a habit goal."""
    query = select(models.HabitGoal).filter(models.HabitGoal.id == goal_id)
    result = await db.execute(query)
    goal = result.scalar_one_or_none()

    if goal:
        goal.current_value = current_value
        goal.updated_at = datetime.datetime.now(datetime.timezone.utc)

        if status:
            goal.status = status
            if status == "completed":
                goal.completed_at = datetime.datetime.now(datetime.timezone.utc)

        await db.commit()
        await db.refresh(goal)

    return goal


async def create_personal_achievement(
    db: AsyncSession, user_id: int, achievement_data: Dict[str, Any]
) -> models.HabitAchievement:
    """Create a personal achievement record."""
    achievement = models.HabitAchievement(user_id=user_id, **achievement_data)
    db.add(achievement)
    await db.commit()
    await db.refresh(achievement)
    return achievement


async def get_user_achievements(
    db: AsyncSession, user_id: int, category: Optional[str] = None
) -> List[models.HabitAchievement]:
    """Get user's achievements."""
    query = select(models.HabitAchievement).filter(
        models.HabitAchievement.user_id == user_id
    )

    if category:
        query = query.filter(models.HabitAchievement.category == category)

    query = query.order_by(models.HabitAchievement.earned_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def create_habit_progress_snapshot(
    db: AsyncSession, user_id: int, snapshot_data: Dict[str, Any]
) -> models.HabitProgressSnapshot:
    """Create a habit progress snapshot for trend tracking."""
    snapshot = models.HabitProgressSnapshot(user_id=user_id, **snapshot_data)
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)
    return snapshot


async def get_user_habit_snapshots(
    db: AsyncSession,
    user_id: int,
    start_date: Optional[datetime.datetime] = None,
    limit: int = 50,
) -> List[models.HabitProgressSnapshot]:
    """Get user's habit progress snapshots for trend analysis."""
    query = select(models.HabitProgressSnapshot).filter(
        models.HabitProgressSnapshot.user_id == user_id
    )

    if start_date:
        query = query.filter(models.HabitProgressSnapshot.snapshot_date >= start_date)

    query = query.order_by(models.HabitProgressSnapshot.snapshot_date.desc()).limit(
        limit
    )

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_user_habit_statistics(
    db: AsyncSession, user_id: int, days_back: int = 90
) -> Dict[str, Any]:
    """
    Get comprehensive habit statistics for a user.

    Args:
        db: Database session
        user_id: User ID
        days_back: Number of days to analyze

    Returns:
        Comprehensive habit statistics
    """
    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=days_back
    )

    # Get total analyses count
    analyses_query = select(models.AnalysisReport).filter(
        models.AnalysisReport.user_id == user_id,
        models.AnalysisReport.analysis_date >= cutoff_date,
    )
    analyses_result = await db.execute(analyses_query)
    total_analyses = len(list(analyses_result.scalars().all()))

    # Get total findings count
    findings_query = (
        select(models.Finding)
        .join(models.AnalysisReport)
        .filter(
            models.AnalysisReport.user_id == user_id,
            models.AnalysisReport.analysis_date >= cutoff_date,
        )
    )
    findings_result = await db.execute(findings_query)
    total_findings = len(list(findings_result.scalars().all()))

    # Get achievements count
    achievements_query = select(models.PersonalAchievement).filter(
        models.PersonalAchievement.user_id == user_id
    )
    achievements_result = await db.execute(achievements_query)
    achievements = list(achievements_result.scalars().all())

    total_points = sum(a.points_earned for a in achievements)

    # Get active goals count
    goals_query = select(models.HabitGoal).filter(
        models.HabitGoal.user_id == user_id, models.HabitGoal.status == "active"
    )
    goals_result = await db.execute(goals_query)
    active_goals = len(list(goals_result.scalars().all()))

    return {
        "user_id": user_id,
        "period_days": days_back,
        "total_analyses": total_analyses,
        "total_findings": total_findings,
        "findings_per_analysis": total_findings / max(total_analyses, 1),
        "total_achievements": len(achievements),
        "total_points": total_points,
        "active_goals": active_goals,
        "analysis_frequency": total_analyses / days_back if days_back > 0 else 0,
    }


# Habit Progression CRUD Operations


async def create_habit_goal(
    db: AsyncSession, user_id: int, goal_data: schemas.HabitGoalCreate
) -> models.HabitGoal:
    """Create a new habit goal for user."""
    db_goal = models.HabitGoal(user_id=user_id, **goal_data.model_dump())
    db.add(db_goal)
    await db.commit()
    await db.refresh(db_goal)
    return db_goal
