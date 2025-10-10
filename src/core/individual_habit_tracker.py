"""Individual Habit Tracker for Personal Growth Journey.

Tracks individual therapist's habit progression, mastery levels, achievements,
and provides personalized coaching recommendations.

This is separate from organizational analytics and maintains user privacy.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from ..database import crud
from .enhanced_habit_mapper import SevenHabitsFramework

logger = logging.getLogger(__name__)


class IndividualHabitTracker:
    """Tracks individual user's habit progression and provides personalized insights.

    Features:
    - Personal habit mastery tracking
    - Individual achievement system
    - Progress streaks and milestones
    - Personalized coaching recommendations
    - Goal setting and tracking
    """

    def __init__(self, user_id: int, habits_framework: SevenHabitsFramework):
        """Initialize individual habit tracker.

        Args:
            user_id: User ID for tracking
            habits_framework: Enhanced habits framework instance

        """
        self.user_id = user_id
        self.habits_framework = habits_framework

    async def get_personal_habit_profile(
        self,
        db_session,
        days_back: int = 90) -> dict[str, Any]:
        """Get comprehensive personal habit profile for the user.

        Args:
            db_session: Database session
            days_back: Number of days to look back for analysis

        Returns:
            Complete personal habit profile with progression metrics

        """
        # Get user's recent analysis history
        cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

        # Get user's reports with findings
        user_reports = await crud.get_user_reports_with_findings(
            db_session,
            user_id=self.user_id,
            start_date=cutoff_date)

        if not user_reports:
            return self._empty_profile()

        # Extract all findings and map to habits
        all_findings = []
        for report in user_reports:
            for finding in report.findings:
                # Map finding to habit
                habit_info = self.habits_framework.map_finding_to_habit(
                    {
                        "issue_title": finding.issue_title or "",
                        "text": finding.problematic_text or "",
                        "risk": finding.risk or "LOW",
                    })

                all_findings.append(
                    {
                        "habit_id": habit_info["habit_id"],
                        "habit_number": habit_info["habit_number"],
                        "habit_name": habit_info["name"],
                        "date": report.analysis_date,
                        "risk": finding.risk,
                        "confidence": finding.confidence_score or 0.8,
                    })

        # Calculate progression metrics
        progression_metrics = self.habits_framework.get_habit_progression_metrics(
            all_findings)

        # Calculate personal insights
        personal_insights = await self._calculate_personal_insights(
            db_session,
            all_findings,
            user_reports)

        # Get achievement status
        achievements = await self._calculate_achievements(db_session, all_findings)

        # Calculate streaks and milestones
        streaks = self._calculate_streaks(user_reports)

        # Generate personalized recommendations
        recommendations = self._generate_personal_recommendations(
            progression_metrics,
            personal_insights)

        return {
            "user_id": self.user_id,
            "analysis_period": {
                "days_back": days_back,
                "start_date": cutoff_date.isoformat(),
                "end_date": datetime.now(UTC).isoformat(),
                "total_reports": len(user_reports),
                "total_findings": len(all_findings),
            },
            "habit_progression": progression_metrics,
            "personal_insights": personal_insights,
            "achievements": achievements,
            "streaks": streaks,
            "recommendations": recommendations,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def get_habit_timeline(
        self,
        db_session,
        habit_id: str,
        days_back: int = 30) -> dict[str, Any]:
        """Get detailed timeline for a specific habit.

        Args:
            db_session: Database session
            habit_id: Specific habit to analyze
            days_back: Number of days to analyze

        Returns:
            Detailed habit timeline with daily breakdown

        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

        user_reports = await crud.get_user_reports_with_findings(
            db_session,
            user_id=self.user_id,
            start_date=cutoff_date)

        # Create daily timeline
        timeline = {}
        for report in user_reports:
            date_key = report.analysis_date.date().isoformat()

            if date_key not in timeline:
                timeline[date_key] = {
                    "date": date_key,
                    "total_findings": 0,
                    "habit_findings": 0,
                    "compliance_score": report.compliance_score or 0,
                    "findings_details": [],
                }

            timeline[date_key]["total_findings"] += len(report.findings)

            # Check findings for this habit
            for finding in report.findings:
                finding_habit = self.habits_framework.map_finding_to_habit(
                    {
                        "issue_title": finding.issue_title or "",
                        "text": finding.problematic_text or "",
                    })

                if finding_habit["habit_id"] == habit_id:
                    timeline[date_key]["habit_findings"] += 1
                    timeline[date_key]["findings_details"].append(
                        {
                            "issue": finding.issue_title,
                            "risk": finding.risk,
                            "confidence": finding.confidence_score,
                        })

        # Sort timeline by date
        sorted_timeline = sorted(timeline.values(), key=lambda x: x["date"])

        habit_details = self.habits_framework.get_habit_details(habit_id)

        return {
            "habit_id": habit_id,
            "habit_details": habit_details,
            "timeline": sorted_timeline,
            "summary": {
                "total_days": len(sorted_timeline),
                "days_with_findings": len(
                    [d for d in sorted_timeline if d["habit_findings"] > 0]),
                "total_habit_findings": sum(d["habit_findings"] for d in sorted_timeline),
                "avg_findings_per_day": sum(d["habit_findings"] for d in sorted_timeline)
                / max(len(sorted_timeline), 1),
            },
        }

    async def set_personal_goal(
        self,
        db_session,
        habit_id: str,
        goal_type: str,
        target_value: float,
        target_date: datetime) -> dict[str, Any]:
        """Set a personal habit improvement goal.

        Args:
            db_session: Database session
            habit_id: Habit to improve
            goal_type: Type of goal (reduce_findings, improve_mastery, etc.)
            target_value: Target value to achieve
            target_date: Date to achieve goal by

        Returns:
            Goal creation confirmation

        """
        # Create personal goal record
        goal_data = {
            "user_id": self.user_id,
            "habit_id": habit_id,
            "goal_type": goal_type,
            "target_value": target_value,
            "target_date": target_date,
            "created_at": datetime.now(UTC),
            "status": "active",
        }

        # Store in database (would need to create PersonalGoal model)
        # For now, return the goal data
        return {
            "goal_id": f"goal_{self.user_id}_{habit_id}_{int(datetime.now(UTC).timestamp())}",
            "message": "Personal goal set successfully",
            "goal_details": goal_data,
        }

    def _empty_profile(self) -> dict[str, Any]:
        """Return empty profile for users with no data."""
        return {
            "user_id": self.user_id,
            "analysis_period": {"total_reports": 0, "total_findings": 0},
            "habit_progression": {
                "total_findings": 0,
                "habit_breakdown": {},
                "top_focus_areas": [],
            },
            "personal_insights": {
                "improvement_trend": "No data available",
                "strongest_habits": [],
                "focus_areas": [],
            },
            "achievements": {"badges": [], "milestones": [], "total_points": 0},
            "streaks": {
                "current_streak": 0,
                "longest_streak": 0,
                "streak_type": "No findings",
            },
            "recommendations": [],
            "message": "Complete more analyses to see your personal growth journey!",
        }

    async def _calculate_personal_insights(
        self,
        db_session,
        findings: list[dict],
        reports: list[Any]) -> dict[str, Any]:
        """Calculate personalized insights from user's data."""
        if not findings:
            return {
                "improvement_trend": "No data",
                "strongest_habits": [],
                "focus_areas": [],
            }

        # Calculate improvement trend (last 30 days vs previous 30 days)
        now = datetime.now(UTC)
        recent_cutoff = now - timedelta(days=30)
        older_cutoff = now - timedelta(days=60)

        recent_findings = [f for f in findings if f["date"] >= recent_cutoff]
        older_findings = [f for f in findings if older_cutoff <= f["date"] < recent_cutoff]

        trend = "stable"
        if len(older_findings) > 0:
            recent_rate = len(recent_findings) / 30
            older_rate = len(older_findings) / 30

            if recent_rate < older_rate * 0.8:
                trend = "improving"
            elif recent_rate > older_rate * 1.2:
                trend = "declining"

        # Find strongest habits (lowest finding rates)
        habit_counts = {}
        for finding in findings:
            habit_id = finding["habit_id"]
            habit_counts[habit_id] = habit_counts.get(habit_id, 0) + 1

        # Sort by count (ascending = strongest)
        sorted_habits = sorted(habit_counts.items(), key=lambda x: x[1])
        strongest_habits = []

        for habit_id, count in sorted_habits[:3]:
            habit_details = self.habits_framework.get_habit_details(habit_id)
            strongest_habits.append(
                {
                    "habit_id": habit_id,
                    "habit_name": habit_details["name"],
                    "finding_count": count,
                    "strength_level": "Strong" if count < len(findings) * 0.1 else "Good",
                })

        # Focus areas (highest finding rates)
        focus_areas = []
        for habit_id, count in sorted_habits[-3:]:
            if count > len(findings) * 0.15:  # More than 15% of findings
                habit_details = self.habits_framework.get_habit_details(habit_id)
                focus_areas.append(
                    {
                        "habit_id": habit_id,
                        "habit_name": habit_details["name"],
                        "finding_count": count,
                        "percentage": round(count / len(findings) * 100, 1),
                    })

        return {
            "improvement_trend": trend,
            "strongest_habits": strongest_habits,
            "focus_areas": focus_areas,
            "total_analysis_days": len(set(f["date"].date() for f in findings)),
        }

    async def _calculate_achievements(
        self,
        db_session,
        findings: list[dict]) -> dict[str, Any]:
        """Calculate user achievements and badges."""
        badges = []
        milestones = []
        points = 0

        if not findings:
            return {"badges": badges, "milestones": milestones, "total_points": points}

        # Habit mastery badges
        habit_counts = {}
        for finding in findings:
            habit_id = finding["habit_id"]
            habit_counts[habit_id] = habit_counts.get(habit_id, 0) + 1

        total_findings = len(findings)
        for habit_id, count in habit_counts.items():
            percentage = count / total_findings
            habit_details = self.habits_framework.get_habit_details(habit_id)

            if percentage < 0.05:  # Less than 5% = Mastered
                badges.append(
                    {
                        "id": f"habit_{habit_details['number']}_master",
                        "name": f"Habit {habit_details['number']} Master",
                        "description": f"Mastered {habit_details['name']}",
                        "icon": "🏆",
                        "earned_date": datetime.now(UTC).isoformat(),
                        "points": 100,
                    })
                points += 100

        # Analysis milestones
        analysis_count = len(set(f["date"].date() for f in findings))

        milestone_thresholds = [10, 25, 50, 100, 250, 500]
        for threshold in milestone_thresholds:
            if analysis_count >= threshold:
                milestones.append(
                    {
                        "id": f"analyses_{threshold}",
                        "name": f"{threshold} Analyses",
                        "description": f"Completed {threshold} compliance analyses",
                        "icon": "📊",
                        "achieved": True,
                        "points": threshold // 10,
                    })
                points += threshold // 10

        return {"badges": badges, "milestones": milestones, "total_points": points}

    def _calculate_streaks(self, reports: list[Any]) -> dict[str, Any]:
        """Calculate improvement streaks."""
        if not reports:
            return {"current_streak": 0, "longest_streak": 0, "streak_type": "No data"}

        # Sort reports by date
        sorted_reports = sorted(reports, key=lambda r: r.analysis_date)

        # Calculate "no findings" streaks (days without compliance issues)
        current_streak = 0
        longest_streak = 0
        temp_streak = 0

        for report in sorted_reports:
            if len(report.findings) == 0:
                temp_streak += 1
                current_streak = temp_streak
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 0

        longest_streak = max(longest_streak, temp_streak)

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "streak_type": "Days without findings",
            "last_analysis_date": sorted_reports[-1].analysis_date.isoformat() if sorted_reports else None,
        }

    def _generate_personal_recommendations(
        self,
        progression_metrics: dict,
        insights: dict) -> list[dict[str, Any]]:
        """Generate personalized improvement recommendations."""
        recommendations = []

        # Focus area recommendations
        if progression_metrics.get("top_focus_areas"):
            primary_focus = progression_metrics["top_focus_areas"][0]
            habit_id, habit_data = primary_focus

            habit_details = self.habits_framework.get_habit_details(habit_id)

            recommendations.append(
                {
                    "type": "primary_focus",
                    "priority": "high",
                    "title": f"Focus on {habit_details['name']}",
                    "description": f"This habit represents {habit_data['percentage']}% of your findings. Focusing here will have the biggest impact.",
                    "action_items": habit_details["improvement_strategies"][:3],
                    "habit_id": habit_id,
                })

        # Improvement trend recommendations
        if insights.get("improvement_trend") == "declining":
            recommendations.append(
                {
                    "type": "trend_alert",
                    "priority": "medium",
                    "title": "Compliance Trend Alert",
                    "description": "Your findings have increased recently. Consider reviewing your documentation practices.",
                    "action_items": [
                        "Review recent analyses for common patterns",
                        "Schedule time for documentation review",
                        "Consider additional training or resources",
                    ],
                })
        elif insights.get("improvement_trend") == "improving":
            recommendations.append(
                {
                    "type": "positive_reinforcement",
                    "priority": "low",
                    "title": "Great Progress!",
                    "description": "Your compliance has improved recently. Keep up the excellent work!",
                    "action_items": [
                        "Continue current practices",
                        "Share successful strategies with colleagues",
                        "Set new improvement goals",
                    ],
                })

        # Strongest habit reinforcement
        if insights.get("strongest_habits"):
            strongest = insights["strongest_habits"][0]
            recommendations.append(
                {
                    "type": "strength_reinforcement",
                    "priority": "low",
                    "title": f"Strength: {strongest['habit_name']}",
                    "description": f"You excel at {strongest['habit_name']}. Consider mentoring others in this area.",
                    "action_items": [
                        "Document your successful practices",
                        "Share tips with team members",
                        "Maintain current excellence",
                    ],
                })

        return recommendations
