"""
Database CRUD operations for the Therapy Compliance Analyzer.

Provides async database operations for users, rubrics, reports, and findings.
"""

import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from . import models, schemas


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
    result = await db.execute(
        select(models.ComplianceRubric).offset(skip).limit(limit)
    )
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
    db: AsyncSession, embedding: bytes, threshold: float = 0.9
) -> Optional[models.AnalysisReport]:
    """
    Find similar report based on embedding similarity.

    This is a placeholder for actual similarity search logic.
    In production, this would use a vector database.

    Args:
        db: Database session
        embedding: Document embedding bytes
        threshold: Similarity threshold

    Returns:
        Similar report if found, None otherwise
    """
    # Placeholder - would implement vector similarity search in production
    return None


async def create_report_and_findings(
    db: AsyncSession,
    report_data: schemas.ReportCreate,
    findings_data: List[schemas.FindingCreate],
) -> models.AnalysisReport:
    """
    Create a report with associated findings in a single transaction.

    Args:
        db: Database session
        report_data: Report creation data
        findings_data: List of finding creation data

    Returns:
        Created AnalysisReport with findings
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

    await db.commit()
    await db.refresh(db_report)
    return db_report

# Individual Habit Tracking CRUD Operations

async def get_user_reports_with_findings(
    db: AsyncSession,
    user_id: int,
    start_date: Optional[datetime.datetime] = None,
    limit: int = 100
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
    query = select(models.AnalysisReport).options(
        selectinload(models.AnalysisReport.findings)
    ).filter(models.AnalysisReport.user_id == user_id)
    
    if start_date:
        query = query.filter(models.AnalysisReport.analysis_date >= start_date)
    
    query = query.order_by(models.AnalysisReport.analysis_date.desc()).limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_personal_habit_goal(
    db: AsyncSession, user_id: int, goal_data: Dict[str, Any]
) -> models.HabitGoal:
    """Create a personal habit improvement goal."""
    goal = models.HabitGoal(
        user_id=user_id,
        **goal_data
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


async def get_user_habit_goals(
    db: AsyncSession, user_id: int, active_only: bool = True
) -> List[models.HabitGoal]:
    """Get user's habit goals."""
    query = select(models.HabitGoal).filter(
        models.HabitGoal.user_id == user_id
    )
    
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
    achievement = models.HabitAchievement(
        user_id=user_id,
        **achievement_data
    )
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
    snapshot = models.HabitProgressSnapshot(
        user_id=user_id,
        **snapshot_data
    )
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)
    return snapshot


async def get_user_habit_snapshots(
    db: AsyncSession,
    user_id: int,
    start_date: Optional[datetime.datetime] = None,
    limit: int = 50
) -> List[models.HabitProgressSnapshot]:
    """Get user's habit progress snapshots for trend analysis."""
    query = select(models.HabitProgressSnapshot).filter(
        models.HabitProgressSnapshot.user_id == user_id
    )
    
    if start_date:
        query = query.filter(models.HabitProgressSnapshot.snapshot_date >= start_date)
    
    query = query.order_by(models.HabitProgressSnapshot.snapshot_date.desc()).limit(limit)
    
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
    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_back)
    
    # Get total analyses count
    analyses_query = select(models.AnalysisReport).filter(
        models.AnalysisReport.user_id == user_id,
        models.AnalysisReport.analysis_date >= cutoff_date
    )
    analyses_result = await db.execute(analyses_query)
    total_analyses = len(list(analyses_result.scalars().all()))
    
    # Get total findings count
    findings_query = select(models.Finding).join(models.AnalysisReport).filter(
        models.AnalysisReport.user_id == user_id,
        models.AnalysisReport.analysis_date >= cutoff_date
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
        models.HabitGoal.user_id == user_id,
        models.HabitGoal.status == "active"
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
        "analysis_frequency": total_analyses / days_back if days_back > 0 else 0
    }


# Habit Progression CRUD Operations



async def create_habit_goal(
    db: AsyncSession,
    user_id: int,
    goal_data: schemas.HabitGoalCreate
) -> models.HabitGoal:
    """Create a new habit goal for user."""
    db_goal = models.HabitGoal(
        user_id=user_id,
        **goal_data.model_dump()
    )
    db.add(db_goal)
    await db.commit()
    await db.refresh(db_goal)
    return db_goal





