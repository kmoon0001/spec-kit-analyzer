"""Individual Habit Progression Tracking Service.

Tracks personal growth journey for each therapist using the 7 Habits framework.
Provides individual analytics, goal setting, and achievement tracking.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import crud
from .enhanced_habit_mapper import SevenHabitsFramework

logger = logging.getLogger(__name__)


class HabitProgressionService:
    """Service for tracking individual habit progression and growth journey.

    Features:
    - Personal habit mastery tracking
    - Individual goal setting and achievement
    - Progress visualization data
    - Achievement badge system
    - Personalized coaching recommendations
    """

    def __init__(self):
        self.habits_framework = SevenHabitsFramework()

    async def get_user_habit_progression(
        self, db: AsyncSession, user_id: int, days_back: int = 90,
    ) -> dict[str, Any]:
        """Get comprehensive habit progression data for a user.

        Args:
            db: Database session
            user_id: User ID
            days_back: Number of days to look back for analysis

        Returns:
            Dict with complete progression data

        """
        # Get user's analysis history
        cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

        # Get user's reports with findings
        user_reports = await crud.get_user_reports_with_findings(
            db, user_id=user_id, since_date=cutoff_date,
        )

        if not user_reports:
            return self._empty_progression_data()

        # Extract all findings and map to habits
        all_findings = []
        findings_by_date = {}

        for report in user_reports:
            report_date = report.analysis_date.date()
            findings_by_date[report_date] = []

            for finding in report.findings:
                # Map finding to habit
                habit_info = self.habits_framework.map_finding_to_habit(
                    {
                        "issue_title": finding.issue_title or "",
                        "text": finding.problematic_text or "",
                        "risk": finding.risk,
                    },
                )

                finding_with_habit = {
                    "habit_id": habit_info["habit_id"],
                    "habit_number": habit_info["habit_number"],
                    "habit_name": habit_info["name"],
                    "date": report_date,
                    "risk": finding.risk,
                    "confidence": finding.confidence_score,
                }

                all_findings.append(finding_with_habit)
                findings_by_date[report_date].append(finding_with_habit)

        # Calculate progression metrics
        progression_data = self._calculate_progression_metrics(
            all_findings, findings_by_date, days_back,
        )

        # Add achievement data
        progression_data["achievements"] = await self._calculate_achievements(
            db, user_id, all_findings,
        )

        # Add goals and recommendations
        progression_data["current_goals"] = await self._get_user_goals(db, user_id)
        progression_data["recommendations"] = self._generate_recommendations(
            progression_data,
        )

        return progression_data

    def _calculate_progression_metrics(
        self, all_findings: list[dict], findings_by_date: dict, days_back: int,
    ) -> dict[str, Any]:
        """Calculate detailed progression metrics."""

        # Overall metrics
        total_findings = len(all_findings)

        # Habit breakdown
        habit_metrics = self.habits_framework.get_habit_progression_metrics(
            all_findings,
        )

        # Time-based analysis
        weekly_trends = self._calculate_weekly_trends(findings_by_date, days_back)
        improvement_rate = self._calculate_improvement_rate(weekly_trends)

        # Current status
        current_focus_areas = habit_metrics["top_focus_areas"][:2]  # Top 2
        mastery_achievements = [
            (hid, data)
            for hid, data in habit_metrics["habit_breakdown"].items()
            if data["mastery_level"] == "Mastered"
        ]

        # Streaks and consistency
        current_streak = self._calculate_current_streak(findings_by_date)
        consistency_score = self._calculate_consistency_score(
            findings_by_date, days_back,
        )

        return {
            "total_findings": total_findings,
            "analysis_period_days": days_back,
            "habit_breakdown": habit_metrics["habit_breakdown"],
            "focus_areas": current_focus_areas,
            "mastered_habits": mastery_achievements,
            "weekly_trends": weekly_trends,
            "improvement_rate": improvement_rate,
            "current_streak": current_streak,
            "consistency_score": consistency_score,
            "overall_progress": self._calculate_overall_progress(habit_metrics),
        }

    def _calculate_weekly_trends(
        self, findings_by_date: dict, days_back: int,
    ) -> list[dict[str, Any]]:
        """Calculate weekly trend data for visualization."""
        weeks = []
        current_date = datetime.now(UTC).date()

        for week_offset in range(min(12, days_back // 7)):  # Max 12 weeks
            week_start = current_date - timedelta(days=(week_offset + 1) * 7)
            week_end = current_date - timedelta(days=week_offset * 7)

            week_findings = []
            for date, findings in findings_by_date.items():
                if week_start <= date < week_end:
                    week_findings.extend(findings)

            # Calculate week metrics
            week_habit_counts = {}
            for finding in week_findings:
                habit_id = finding["habit_id"]
                week_habit_counts[habit_id] = week_habit_counts.get(habit_id, 0) + 1

            weeks.append(
                {
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "total_findings": len(week_findings),
                    "habit_breakdown": week_habit_counts,
                    "avg_confidence": sum(f["confidence"] for f in week_findings)
                    / len(week_findings)
                    if week_findings
                    else 0,
                },
            )

        return list(reversed(weeks))  # Chronological order

    def _calculate_improvement_rate(self, weekly_trends: list[dict]) -> float:
        """Calculate improvement rate based on weekly trends."""
        if len(weekly_trends) < 2:
            return 0.0

        # Compare recent weeks to earlier weeks
        recent_avg = sum(w["total_findings"] for w in weekly_trends[-4:]) / min(
            4, len(weekly_trends),
        )
        earlier_avg = sum(w["total_findings"] for w in weekly_trends[:4]) / min(
            4, len(weekly_trends),
        )

        if earlier_avg == 0:
            return 0.0

        # Negative improvement rate means fewer findings (better)
        improvement_rate = (recent_avg - earlier_avg) / earlier_avg * 100
        return -improvement_rate  # Flip sign so positive = improvement

    def _calculate_current_streak(self, findings_by_date: dict) -> int:
        """Calculate current streak of days without findings."""
        current_date = datetime.now(UTC).date()
        streak = 0

        for days_back in range(30):  # Check last 30 days
            check_date = current_date - timedelta(days=days_back)

            if check_date in findings_by_date and findings_by_date[check_date]:
                break  # Streak broken
            else:
                streak += 1

        return streak

    def _calculate_consistency_score(
        self, findings_by_date: dict, days_back: int,
    ) -> float:
        """Calculate consistency score (0-100) based on regular improvement."""
        if days_back < 7:
            return 0.0

        # Count days with analysis
        analysis_days = len([d for d, findings in findings_by_date.items() if findings])
        expected_days = days_back // 7 * 2  # Expect ~2 analyses per week

        consistency = min(analysis_days / max(expected_days, 1), 1.0) * 100
        return round(consistency, 1)

    def _calculate_overall_progress(self, habit_metrics: dict) -> dict[str, Any]:
        """Calculate overall progress score and status."""
        habit_breakdown = habit_metrics["habit_breakdown"]

        # Weight habits by mastery level
        mastery_weights = {
            "Mastered": 4,
            "Proficient": 3,
            "Developing": 2,
            "Needs Focus": 1,
        }

        total_score = 0
        max_possible = len(habit_breakdown) * 4

        for habit_data in habit_breakdown.values():
            mastery = habit_data["mastery_level"]
            total_score += mastery_weights.get(mastery, 1)

        progress_percentage = (
            (total_score / max_possible) * 100 if max_possible > 0 else 0
        )

        # Determine status
        if progress_percentage >= 85:
            status = "Expert"
        elif progress_percentage >= 70:
            status = "Advanced"
        elif progress_percentage >= 50:
            status = "Intermediate"
        else:
            status = "Developing"

        return {
            "percentage": round(progress_percentage, 1),
            "status": status,
            "score": total_score,
            "max_score": max_possible,
        }

    async def _calculate_achievements(
        self, db: AsyncSession, user_id: int, all_findings: list[dict],
    ) -> list[dict[str, Any]]:
        """Calculate and award achievements."""
        achievements = []

        # Habit mastery achievements
        habit_counts = {}
        for finding in all_findings:
            habit_id = finding["habit_id"]
            habit_counts[habit_id] = habit_counts.get(habit_id, 0) + 1

        total_findings = len(all_findings)

        for habit_id, count in habit_counts.items():
            percentage = (count / total_findings * 100) if total_findings > 0 else 0
            habit_info = self.habits_framework.get_habit_details(habit_id)

            if percentage < 5:  # Mastered
                achievements.append(
                    {
                        "id": f"habit_{habit_info['number']}_master",
                        "title": f"Habit {habit_info['number']} Master",
                        "description": f"Mastered {habit_info['name']} - less than 5% of findings",
                        "icon": "🏆",
                        "earned_date": datetime.now(UTC).isoformat(),
                        "category": "mastery",
                    },
                )

        # Analysis count achievements
        analysis_count = await self._get_user_analysis_count(db, user_id)

        milestones = [10, 25, 50, 100, 250, 500]
        for milestone in milestones:
            if analysis_count >= milestone:
                achievements.append(
                    {
                        "id": f"analysis_{milestone}",
                        "title": f"{milestone} Analyses",
                        "description": f"Completed {milestone} compliance analyses",
                        "icon": "📊",
                        "earned_date": datetime.now(UTC).isoformat(),
                        "category": "milestone",
                    },
                )

        # Improvement achievements
        # (Could add streak achievements, improvement rate achievements, etc.)

        return achievements

    async def _get_user_analysis_count(self, db: AsyncSession, user_id: int) -> int:
        """Get total analysis count for user."""
        try:
            return await crud.get_user_analysis_count(db, user_id)
        except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
            logger.exception("Error getting user analysis count: %s", e)
            return 0

    async def _get_user_goals(
        self, db: AsyncSession, user_id: int,
    ) -> list[dict[str, Any]]:
        """Get user's current goals from the database."""
        try:
            goals = await crud.get_user_habit_goals(db, user_id=user_id, active_only=True)

            # Format goals into the dictionary structure expected by the frontend
            return [
                {
                    "id": goal.id,
                    "title": goal.title,
                    "description": goal.description,
                    "target_date": goal.target_date.isoformat() if goal.target_date else None,
                    "progress": goal.progress,
                    "status": goal.status,
                }
                for goal in goals
            ]
        except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
            logger.exception("Error getting user goals: %s", e)
            return []

    def _generate_recommendations(self, progression_data: dict) -> list[dict[str, Any]]:
        """Generate personalized recommendations based on progression data."""
        recommendations = []

        # Focus area recommendations
        for habit_id, metrics in progression_data["focus_areas"]:
            habit_info = self.habits_framework.get_habit_details(habit_id)

            recommendations.append(
                {
                    "type": "focus_area",
                    "priority": "high",
                    "title": f"Focus on {habit_info['name']}",
                    "description": f"This habit represents {metrics['percentage']}% of your findings",
                    "action_items": habit_info["improvement_strategies"][:3],
                    "habit_number": habit_info["number"],
                },
            )

        # Improvement rate recommendations
        if progression_data["improvement_rate"] < 0:
            recommendations.append(
                {
                    "type": "improvement",
                    "priority": "medium",
                    "title": "Maintain Your Progress",
                    "description": f"You're improving at {abs(progression_data['improvement_rate']):.1f}% rate",
                    "action_items": [
                        "Continue current documentation practices",
                        "Set new challenge goals",
                        "Share your success strategies with peers",
                    ],
                },
            )
        elif progression_data["improvement_rate"] < 5:
            recommendations.append(
                {
                    "type": "improvement",
                    "priority": "high",
                    "title": "Accelerate Your Progress",
                    "description": "Your improvement rate has slowed recently",
                    "action_items": [
                        "Review recent findings for patterns",
                        "Try new documentation strategies",
                        "Schedule focused practice sessions",
                    ],
                },
            )

        # Consistency recommendations
        if progression_data["consistency_score"] < 50:
            recommendations.append(
                {
                    "type": "consistency",
                    "priority": "medium",
                    "title": "Improve Analysis Consistency",
                    "description": f"Your consistency score is {progression_data['consistency_score']}%",
                    "action_items": [
                        "Set a regular analysis schedule",
                        "Use reminders for documentation review",
                        "Analyze smaller batches more frequently",
                    ],
                },
            )

        return recommendations

    def _empty_progression_data(self) -> dict[str, Any]:
        """Return empty progression data structure."""
        return {
            "total_findings": 0,
            "analysis_period_days": 0,
            "habit_breakdown": {},
            "focus_areas": [],
            "mastered_habits": [],
            "weekly_trends": [],
            "improvement_rate": 0.0,
            "current_streak": 0,
            "consistency_score": 0.0,
            "overall_progress": {
                "percentage": 0,
                "status": "New",
                "score": 0,
                "max_score": 28,
            },
            "achievements": [],
            "current_goals": [],
            "recommendations": [],
        }

    async def set_user_goal(
        self, db: AsyncSession, user_id: int, goal_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Set a new goal for the user."""
        # This would create a new goal in the database
        # For now, return the goal data with an ID
        goal = {
            "id": hash(str(goal_data)) % 10000,  # Simple ID generation
            "user_id": user_id,
            "created_at": datetime.now(UTC).isoformat(),
            **goal_data,
        }

        logger.info("Created goal for user %s: %s", user_id, goal['title'])
        return goal

    async def update_goal_progress(
        self, db: AsyncSession, user_id: int, goal_id: int, progress: int,
    ) -> bool:
        """Update progress on a user's goal."""
        # This would update the goal in the database
        logger.info(
            "Updated goal %s progress to %s%% for user %s", goal_id, progress, user_id
        )
        return True
