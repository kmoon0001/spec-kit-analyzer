"""Meta Analytics API router for organizational-level insights.

Provides endpoints for team performance analytics, training needs identification,
and anonymous benchmarking data. Admin-only access.
"""

import logging
import sqlite3

import sqlalchemy
import sqlalchemy.exc
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...core.meta_analytics_service import MetaAnalyticsService
from ...database import models
from ...database.database import get_async_db
from ..dependencies import require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/meta-analytics", tags=["Meta Analytics"])


@router.get("/widget_data")
async def get_widget_meta_analytics_data(
    days_back: int = Query(90, ge=7, le=365, description="Days to analyze (7-365)"),
    discipline: str | None = Query(None, description="Filter by discipline (PT, OT, SLP)"),
    _admin_user: models.User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    """Get comprehensive organizational analytics overview for the MetaAnalyticsWidget.

    **Admin Only**
    """
    try:
        meta_service = MetaAnalyticsService()
        overview_data = await meta_service.get_organizational_overview(
            db=db, days_back=days_back, discipline_filter=discipline
        )
        return overview_data
    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        logger.exception("Failed to get organizational overview for widget")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organizational analytics for widget",
        ) from None


@router.get("/organizational-overview")
async def get_organizational_overview(
    days_back: int = Query(90, ge=7, le=365, description="Days to analyze (7-365)"),
    discipline: str | None = Query(None, description="Filter by discipline (PT, OT, SLP)"),
    _admin_user: models.User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    """Get comprehensive organizational analytics overview.

    **Admin Only** - Provides team-wide insights including:
    - Overall team performance metrics
    - Discipline-specific breakdowns
    - Team habit distribution
    - Training needs identification
    - Performance trends over time
    """
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    if not settings.enable_director_dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Director dashboard is not enabled")

    try:
        meta_service = MetaAnalyticsService()

        overview_data = await meta_service.get_organizational_overview(
            db=db, days_back=days_back, discipline_filter=discipline
        )

        return overview_data

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        logger.exception("Failed to get organizational overview")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve organizational analytics"
        ) from None


@router.get("/training-needs")
async def get_training_needs(
    days_back: int = Query(90, ge=30, le=365, description="Days to analyze"),
    discipline: str | None = Query(None, description="Filter by discipline"),
    _admin_user: models.User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    """Identify organizational training needs based on habit patterns.

    **Admin Only** - Analyzes team-wide findings to identify:
    - Habits requiring focused training
    - Number of users affected
    - Priority levels and recommendations
    - Specific training strategies
    """
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    try:
        meta_service = MetaAnalyticsService()

        overview_data = await meta_service.get_organizational_overview(
            db=db, days_back=days_back, discipline_filter=discipline
        )

        return {
            "training_needs": overview_data["training_needs"],
            "insights": [insight for insight in overview_data["insights"] if insight["type"] == "training"],
            "analysis_period": days_back,
            "discipline_filter": discipline,
        }

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        logger.exception("Failed to get training needs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve training needs"
        ) from None


@router.get("/team-trends")
async def get_team_trends(
    weeks_back: int = Query(12, ge=4, le=52, description="Number of weeks to analyze"),
    discipline: str | None = Query(None, description="Filter by discipline"),
    _admin_user: models.User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    """Get team-wide performance trends over time.

    **Admin Only** - Provides weekly trend data for:
    - Team compliance scores
    - Total findings and analyses
    - Habit distribution changes
    - Performance trajectory
    """
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    try:
        meta_service = MetaAnalyticsService()

        overview_data = await meta_service.get_organizational_overview(
            db=db, days_back=weeks_back * 7, discipline_filter=discipline
        )

        return {
            "team_trends": overview_data["team_trends"],
            "trend_insights": [insight for insight in overview_data["insights"] if insight["type"] == "trend"],
            "weeks_analyzed": weeks_back,
            "discipline_filter": discipline,
        }

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        logger.exception("Failed to get team trends")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve team trends"
        ) from None


@router.get("/benchmarks")
async def get_benchmarks(
    days_back: int = Query(90, ge=30, le=365, description="Days to analyze"),
    _admin_user: models.User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    """Get organizational benchmarking data.

    **Admin Only** - Provides percentile data for:
    - Compliance score distribution
    - Findings per user distribution
    - Analysis frequency distribution
    - Performance benchmarks
    """
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    try:
        meta_service = MetaAnalyticsService()

        overview_data = await meta_service.get_organizational_overview(db=db, days_back=days_back)

        return {
            "benchmarks": overview_data["benchmarks"],
            "organizational_metrics": overview_data["organizational_metrics"],
            "analysis_period": days_back,
        }

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        logger.exception("Failed to get benchmarks")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve benchmarks"
        ) from None


@router.get("/peer-comparison/{user_id}")
async def get_peer_comparison(
    user_id: int,
    days_back: int = Query(90, ge=30, le=365, description="Days to analyze"),
    _admin_user: models.User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    """Get anonymous peer comparison data for a specific user.

    **Admin Only** - Provides anonymous comparison including:
    - User's performance vs team averages
    - Percentile rankings
    - Comparison insights and recommendations
    """
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    if not settings.habits_framework.dashboard_integration.show_peer_comparison:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer comparison is not enabled")

    try:
        meta_service = MetaAnalyticsService()

        comparison_data = await meta_service.get_peer_comparison_data(db=db, user_id=user_id, days_back=days_back)

        return comparison_data

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        logger.exception("Failed to get peer comparison for user %s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve peer comparison data"
        ) from None


@router.get("/discipline-comparison")
async def get_discipline_comparison(
    days_back: int = Query(90, ge=30, le=365, description="Days to analyze"),
    _admin_user: models.User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    """Compare performance across therapy disciplines.

    **Admin Only** - Provides discipline comparison including:
    - PT vs OT vs SLP performance metrics
    - Discipline-specific habit patterns
    - Training needs by discipline
    - Best practices identification
    """
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    try:
        meta_service = MetaAnalyticsService()

        # Get data for each discipline
        disciplines = ["PT", "OT", "SLP"]
        discipline_data = {}

        for discipline in disciplines:
            overview = await meta_service.get_organizational_overview(
                db=db, days_back=days_back, discipline_filter=discipline
            )

            if overview["organizational_metrics"]:
                discipline_data[discipline] = {
                    "metrics": overview["organizational_metrics"]["discipline_breakdown"].get(discipline, {}),
                    "training_needs": overview["training_needs"],
                    "insights": overview["insights"],
                }

        return {
            "discipline_comparison": discipline_data,
            "analysis_period": days_back,
            "disciplines_analyzed": list(discipline_data.keys()),
        }

    except (requests.RequestException, ConnectionError, TimeoutError, HTTPError):
        logger.exception("Failed to get discipline comparison")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve discipline comparison"
        ) from None


@router.get("/performance-alerts")
async def get_performance_alerts(
    _admin_user: models.User = Depends(require_admin), db: AsyncSession = Depends(get_async_db)
) -> dict:
    """Get performance alerts and recommendations for immediate action.

    **Admin Only** - Identifies urgent issues requiring attention:
    - Declining performance trends
    - Critical training needs
    - Users requiring intervention
    - System-wide concerns
    """
    settings = get_settings()

    if not settings.habits_framework.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habits framework is not enabled")

    try:
        meta_service = MetaAnalyticsService()

        # Get recent data for alerts (last 30 days)
        overview_data = await meta_service.get_organizational_overview(db=db, days_back=30)

        # Filter for high-priority insights
        alerts = [
            insight for insight in overview_data["insights"] if insight["level"] in ["concern", "action_required"]
        ]

        # Add urgent training needs
        urgent_training = [need for need in overview_data["training_needs"] if need["priority"] == "high"]

        return {
            "performance_alerts": alerts,
            "urgent_training_needs": urgent_training,
            "alert_count": len(alerts) + len(urgent_training),
            "generated_at": overview_data["generated_at"],
        }

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        logger.exception("Failed to get performance alerts: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve performance alerts"
        ) from None
