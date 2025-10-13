"""Individual Habits API Router.
from scipy import stats

Provides endpoints for personal habit tracking, growth journey,
achievements, and individual analytics.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Any

import sqlalchemy
import sqlalchemy.exc
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import get_current_active_user
from ...config import get_settings
from ...core.enhanced_habit_mapper import SevenHabitsFramework
from ...core.individual_habit_tracker import IndividualHabitTracker
from ...database import crud, models
from ...database.database import get_async_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/habits/individual", tags=["Individual Habits"])


@router.get("/profile")
async def get_personal_habit_profile(
    days_back: int = Query(90, ge=7, le=365, description="Days to analyze (7-365)"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Get comprehensive personal habit profile for the current user.

    Returns detailed habit progression, achievements, streaks, and
    personalized recommendations based on the user's analysis history.
    """
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    # Initialize habits framework and tracker
    habits_framework = SevenHabitsFramework(use_ai_mapping=settings.habits_framework.ai_features.use_ai_mapping)

    tracker = IndividualHabitTracker(user_id=current_user.id, habits_framework=habits_framework)

    try:
        profile = await tracker.get_personal_habit_profile(db, days_back)
        return profile

    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.exception("Failed to get habit profile for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate habit profile: {e!s}"
        ) from e


@router.get("/timeline/{habit_id}")
async def get_habit_timeline(
    habit_id: str,
    days_back: int = Query(30, ge=7, le=90, description="Days to analyze (7-90)"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Get detailed timeline for a specific habit.

    Shows daily breakdown of findings, compliance scores, and progress
    for the specified habit over the requested time period.
    """
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    # Validate habit_id
    valid_habits = [f"habit_{i}" for i in range(1, 8)]
    if habit_id not in valid_habits:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid habit_id. Must be one of: {valid_habits}"
        )

    habits_framework = SevenHabitsFramework()
    tracker = IndividualHabitTracker(user_id=current_user.id, habits_framework=habits_framework)

    try:
        timeline = await tracker.get_habit_timeline(db, habit_id, days_back)
        return timeline

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        logger.exception("Failed to get habit timeline for user %s, habit %s", current_user.id, habit_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate habit timeline: {e!s}"
        ) from e


@router.get("/goals")
async def get_personal_goals(
    active_only: bool = Query(True, description="Return only active goals"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Get user's personal habit improvement goals."""
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    try:
        goals = await crud.get_user_habit_goals(db, current_user.id, active_only)

        return {
            "user_id": current_user.id,
            "goals": [
                {
                    "id": goal.id,
                    "habit_id": goal.habit_id,
                    "habit_name": goal.habit_name,
                    "goal_type": goal.goal_type,
                    "target_value": goal.target_value,
                    "current_value": goal.current_value,
                    "progress_percentage": (goal.current_value / goal.target_value * 100)
                    if goal.target_value > 0
                    else 0,
                    "target_date": goal.target_date.isoformat(),
                    "created_at": goal.created_at.isoformat(),
                    "status": goal.status,
                    "days_remaining": (goal.target_date - datetime.now()).days
                    if goal.target_date > datetime.now()
                    else 0,
                }
                for goal in goals
            ],
            "total_goals": len(goals),
        }

    except Exception as e:
        logger.exception("Failed to get goals for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get goals: {e!s}"
        ) from e


@router.post("/goals")
async def create_personal_goal(
    goal_data: dict[str, Any],
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Create a new personal habit improvement goal.

    Expected goal_data format:
    {
        "habit_id": "habit_1",
        "goal_type": "reduce_findings",
        "target_value": 5.0,
        "target_date": "2025-03-01T00:00:00Z"
    }
    """
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    # Validate required fields
    required_fields = ["habit_id", "goal_type", "target_value", "target_date"]
    for field in required_fields:
        if field not in goal_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required field: {field}")

    # Validate habit_id
    valid_habits = [f"habit_{i}" for i in range(1, 8)]
    if goal_data["habit_id"] not in valid_habits:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid habit_id. Must be one of: {valid_habits}"
        )

    # Get habit name
    habits_framework = SevenHabitsFramework()
    habit_details = habits_framework.get_habit_details(goal_data["habit_id"])

    try:
        # Parse target date
        target_date = datetime.fromisoformat(goal_data["target_date"].replace("Z", "+00:00"))

        goal_create_data = {
            "habit_id": goal_data["habit_id"],
            "habit_name": habit_details["name"],
            "goal_type": goal_data["goal_type"],
            "target_value": float(goal_data["target_value"]),
            "target_date": target_date,
            "current_value": 0.0,
            "status": "active",
        }

        goal = await crud.create_personal_habit_goal(db, current_user.id, goal_create_data)

        return {
            "message": "Personal goal created successfully",
            "goal": {
                "id": goal.id,
                "habit_id": goal_create_data["habit_id"],
                "habit_name": goal_create_data["habit_name"],
                "goal_type": goal_create_data["goal_type"],
                "target_value": goal_create_data["target_value"],
                "target_date": goal.target_date.isoformat() if goal.target_date else None,
                "status": goal.status,
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid data format: {e!s}") from e
    except (ImportError, ModuleNotFoundError) as e:
        logger.exception("Failed to create goal for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create goal: {e!s}"
        ) from e


@router.get("/achievements")
async def get_personal_achievements(
    category: str | None = Query(None, description="Filter by achievement category"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Get user's personal achievements and badges."""
    settings = get_settings()

    if not settings.habits_framework.enabled or not settings.habits_framework.gamification.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Achievements system is not enabled")

    try:
        achievements = await crud.get_user_achievements(db, current_user.id, category)

        # Group by category
        by_category: dict[str, list[dict[str, Any]]] = {}
        total_points = 0

        for achievement in achievements:
            cat = str(achievement.get("category", "Uncategorized"))
            by_category.setdefault(cat, []).append(
                {
                    "id": achievement.get("achievement_id", ""),
                    "name": achievement.get("achievement_name", ""),
                    "description": achievement.get("achievement_description", ""),
                    "icon": achievement.get("achievement_icon", "??"),
                    "points": achievement.get("points_earned", 0),
                    "earned_date": (
                        achievement["earned_date"].isoformat()
                        if isinstance(achievement.get("earned_date"), datetime)
                        else ""
                    ),
                    "metadata": achievement.get("metadata", {}),
                }
            )
            total_points += int(achievement.get("points_earned", 0))

        return {
            "user_id": current_user.id,
            "total_achievements": len(achievements),
            "total_points": total_points,
            "achievements_by_category": by_category,
            "categories": list(by_category.keys()),
        }

    except Exception as e:
        logger.exception("Failed to get achievements for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get achievements: {e!s}"
        ) from e


@router.get("/statistics")
async def get_personal_statistics(
    days_back: int = Query(90, ge=7, le=365, description="Days to analyze (7-365)"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Get comprehensive personal habit statistics."""
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    try:
        stats = await crud.get_user_habit_statistics(db, current_user.id, days_back)
        return stats

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        logger.exception("Failed to get statistics for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get statistics: {e!s}"
        ) from e


@router.get("/habits-info")
async def get_all_habits_info(current_user: models.User = Depends(get_current_active_user)) -> dict[str, Any]:
    """Get information about all 7 habits for reference."""
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    habits_framework = SevenHabitsFramework()
    all_habits = habits_framework.get_all_habits()

    return {
        "habits": all_habits,
        "total_habits": len(all_habits),
        "framework_info": {
            "name": "Stephen Covey's 7 Habits of Highly Effective People",
            "description": "Applied to clinical documentation compliance",
            "categories": [
                {"name": "Private Victory", "habits": [1, 2, 3]},
                {"name": "Public Victory", "habits": [4, 5, 6]},
                {"name": "Renewal", "habits": [7]},
            ],
        },
    }


@router.post("/snapshot")
async def create_progress_snapshot(
    current_user: models.User = Depends(get_current_active_user), db: AsyncSession = Depends(get_async_db)
) -> dict[str, Any]:
    """Create a progress snapshot for trend tracking.

    This is typically called automatically by the system, but can be
    triggered manually for immediate snapshot creation.
    """
    settings = get_settings()

    if not settings.habits_framework.enabled or not settings.habits_framework.privacy.track_progression:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress tracking is not enabled")

    try:
        # Get current habit profile
        habits_framework = SevenHabitsFramework()
        tracker = IndividualHabitTracker(user_id=current_user.id, habits_framework=habits_framework)

        profile = await tracker.get_personal_habit_profile(db, days_back=90)

        # Create snapshot data
        snapshot_data = {
            "habit_breakdown": profile["habit_progression"]["habit_breakdown"],
            "total_findings": profile["habit_progression"]["total_findings"],
            "total_analyses": profile["analysis_period"]["total_reports"],
            "overall_progress_score": 100
            - (
                profile["habit_progression"]["total_findings"]
                / max(profile["analysis_period"]["total_reports"], 1)
                * 10
            ),  # Simple mastery calculation
            "improvement_trend": profile["personal_insights"]["improvement_trend"],
        }

        snapshot = await crud.create_habit_progress_snapshot(db, current_user.id, snapshot_data)

        return {
            "message": "Progress snapshot created successfully",
            "snapshot_id": snapshot.id,
            "snapshot_date": snapshot.snapshot_date.isoformat(),
            "mastery_score": snapshot.overall_progress_score,
        }

    except Exception as e:
        logger.exception("Failed to create snapshot for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create snapshot: {e!s}"
        ) from e
