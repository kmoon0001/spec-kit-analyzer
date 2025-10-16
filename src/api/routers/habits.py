"""Habits API router for individual habit progression tracking.

Provides endpoints for personal growth journey, goal setting,
achievement tracking, and habit analytics.
"""

import logging
import sqlite3

import requests

import sqlalchemy
import sqlalchemy.exc
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import get_current_active_user
from ...config import get_settings
from ...core.habit_progression_service import HabitProgressionService
from ...database import crud, models, schemas
from ...database.database import get_async_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/habits", tags=["Habits"])


@router.get("/progression", response_model=schemas.HabitProgressData)
async def get_habit_progression(
    days_back: int = Query(90, ge=7, le=365, description="Days to analyze (7-365)"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> schemas.HabitProgressData:
    """Get comprehensive habit progression data for the current user.

    Returns personal growth journey including:
    - Habit mastery levels
    - Weekly trends and improvement rate
    - Current streak and consistency score
    - Achievements and goals
    - Personalized recommendations
    """
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    progression_service = HabitProgressionService()

    try:
        progression_data = await progression_service.get_user_habit_progression(
            db=db, user_id=current_user.id, days_back=days_back
        )

        return schemas.HabitProgressData(**progression_data)

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        logger.exception("Failed to get habit progression for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve habit progression data"
        ) from None


@router.get("/summary", response_model=schemas.UserProgressSummary)
async def get_progress_summary(
    current_user: models.User = Depends(get_current_active_user), db: AsyncSession = Depends(get_async_db)
) -> schemas.UserProgressSummary:
    """Get a quick summary of user's habit progress.

    Returns high-level metrics for dashboard widgets.
    """
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    progression_service = HabitProgressionService()

    try:
        # Get basic progression data (last 30 days for summary)
        progression_data = await progression_service.get_user_habit_progression(
            db=db, user_id=current_user.id, days_back=30
        )

        # Get achievements
        achievements = await crud.get_user_achievements(db, current_user.id)
        recent_achievements = achievements[:3]  # Last 3 achievements

        # Get active goals
        goals = await crud.get_user_habit_goals(db, current_user.id, active_only=True)

        # Calculate mastered habits count
        mastered_count = len(progression_data["mastered_habits"])

        # Determine next milestone
        next_milestone = None
        total_analyses = progression_data["total_findings"]
        milestones = [10, 25, 50, 100, 250, 500, 1000]
        for milestone in milestones:
            if total_analyses < milestone:
                next_milestone = f"{milestone} Analyses"
                break

        return schemas.UserProgressSummary(
            user_id=current_user.id,
            overall_progress_percentage=progression_data["overall_progress"]["percentage"],
            overall_status=progression_data["overall_progress"]["status"],
            current_streak=progression_data["current_streak"],
            total_analyses=total_analyses,
            mastered_habits_count=mastered_count,
            active_goals_count=len(goals),
            recent_achievements=[schemas.HabitAchievement.model_validate(ach) for ach in recent_achievements],
            next_milestone=next_milestone,
        )

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        logger.exception("Failed to get progress summary for user %s: %s", current_user.id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve progress summary"
        ) from None


@router.get("/goals", response_model=list[schemas.HabitGoal])
async def get_user_goals(
    active_only: bool = Query(True, description="Return only active goals"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[schemas.HabitGoal]:
    """Get user's habit goals."""
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    try:
        goals = await crud.get_user_habit_goals(db, current_user.id, active_only)
        return [schemas.HabitGoal.model_validate(goal) for goal in goals]

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        logger.exception("Failed to get goals for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve goals"
        ) from None


@router.post("/goals", response_model=schemas.HabitGoal)
async def create_goal(
    goal_data: schemas.HabitGoalCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> schemas.HabitGoal:
    """Create a new habit goal for the user."""
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    try:
        goal = await crud.create_habit_goal(db, current_user.id, goal_data.model_dump())
        return schemas.HabitGoal.model_validate(goal)

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        logger.exception("Failed to create goal for user %s", current_user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create goal") from None


@router.put("/goals/{goal_id}/progress")
async def update_goal_progress(
    goal_id: int,
    progress: int = Query(..., ge=0, le=100, description="Progress percentage (0-100)"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> schemas.HabitGoal:
    """Update progress on a habit goal."""
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    try:
        goal = await crud.update_habit_goal_progress(db, goal_id, progress, current_user.id)

        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

        return schemas.HabitGoal.model_validate(goal)

    except HTTPException:
        raise
    except (sqlite3.Error, ConnectionError, sqlalchemy.exc.SQLAlchemyError, TimeoutError, requests.RequestException):
        logger.exception("Failed to update goal progress for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update goal progress"
        ) from None


@router.get("/achievements", response_model=list[schemas.HabitAchievement])
async def get_user_achievements(
    current_user: models.User = Depends(get_current_active_user), db: AsyncSession = Depends(get_async_db)
) -> list[schemas.HabitAchievement]:
    """Get user's habit achievements."""
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    try:
        achievements = await crud.get_user_achievements(db, current_user.id)
        return [schemas.HabitAchievement.model_validate(ach) for ach in achievements]

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        logger.exception("Failed to get achievements for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve achievements"
        ) from None


@router.get("/weekly-trends", response_model=list[schemas.WeeklyHabitTrend])
async def get_weekly_trends(
    weeks_back: int = Query(12, ge=4, le=52, description="Number of weeks to analyze"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[schemas.WeeklyHabitTrend]:
    """Get weekly habit trend data for visualization."""
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    progression_service = HabitProgressionService()

    try:
        progression_data = await progression_service.get_user_habit_progression(
            db=db, user_id=current_user.id, days_back=weeks_back * 7
        )

        weekly_trends = progression_data["weekly_trends"]
        return [schemas.WeeklyHabitTrend(**trend) for trend in weekly_trends]

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        logger.exception("Failed to get weekly trends for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve weekly trends"
        ) from None


@router.get("/recommendations", response_model=list[schemas.HabitRecommendation])
async def get_habit_recommendations(
    current_user: models.User = Depends(get_current_active_user), db: AsyncSession = Depends(get_async_db)
) -> list[schemas.HabitRecommendation]:
    """Get personalized habit recommendations."""
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    progression_service = HabitProgressionService()

    try:
        progression_data = await progression_service.get_user_habit_progression(
            db=db,
            user_id=current_user.id,
            days_back=60,  # 2 months for recommendations
        )

        recommendations = progression_data["recommendations"]
        return [schemas.HabitRecommendation(**rec) for rec in recommendations]

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        logger.exception("Failed to get recommendations for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve recommendations"
        ) from None


@router.get("/habit-details/{habit_number}")
async def get_habit_details(
    habit_number: int = Path(..., ge=1, le=7, description="Habit number (1-7)"),
    current_user: models.User = Depends(get_current_active_user),
) -> dict:
    """Get detailed information about a specific habit."""
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    try:
        progression_service = HabitProgressionService()
        habit_details = progression_service.habits_framework.get_habit_details(f"habit_{habit_number}")

        return {"habit_id": f"habit_{habit_number}", **habit_details}

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        logger.exception("Failed to get habit details for habit %s: %s", habit_number, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve habit details"
        ) from None
