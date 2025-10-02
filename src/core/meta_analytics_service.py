"""
Meta Analytics Service for Organizational-Level Insights.

Provides aggregated, anonymized analytics across all users for directors
and administrators. Includes team performance trends, benchmarking,
and training needs identification.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import crud, models
from .enhanced_habit_mapper import SevenHabitsFramework

logger = logging.getLogger(__name__)


class MetaAnalyticsService:
    """
    Service for organizational-level habit and compliance analytics.

    Features:
    - Team-wide compliance trends (anonymized)
    - Organizational benchmarking and KPIs
    - Training needs identification
    - Comparative analytics across disciplines
    - Anonymous peer comparison data
    """

    def __init__(self):
        self.habits_framework = SevenHabitsFramework()

    async def get_organizational_overview(
        self,
        db: AsyncSession,
        days_back: int = 90,
        discipline_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive organizational analytics overview.

        Args:
            db: Database session
            days_back: Number of days to analyze
            discipline_filter: Optional discipline filter (PT, OT, SLP)

        Returns:
            Dict with organizational metrics and trends
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

        # Get all users and their analysis data
        users_data = await self._get_users_analysis_data(
            db, cutoff_date, discipline_filter
        )

        if not users_data:
            return self._empty_organizational_data()

        # Calculate organizational metrics
        org_metrics = self._calculate_organizational_metrics(users_data)

        # Calculate team trends
        team_trends = await self._calculate_team_trends(
            db, cutoff_date, discipline_filter
        )

        # Identify training needs
        training_needs = self._identify_training_needs(users_data)

        # Calculate benchmarking data
        benchmarks = self._calculate_benchmarks(users_data)

        # Generate insights and recommendations
        insights = self._generate_organizational_insights(
            org_metrics, team_trends, training_needs
        )

        return {
            "analysis_period_days": days_back,
            "discipline_filter": discipline_filter,
            "organizational_metrics": org_metrics,
            "team_trends": team_trends,
            "training_needs": training_needs,
            "benchmarks": benchmarks,
            "insights": insights,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def _get_users_analysis_data(
        self,
        db: AsyncSession,
        cutoff_date: datetime,
        discipline_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get anonymized analysis data for all users."""

        # Get all reports with findings since cutoff date
        query = (
            select(models.AnalysisReport)
            .options(selectinload(models.AnalysisReport.findings))
            .filter(models.AnalysisReport.analysis_date >= cutoff_date)
        )

        if discipline_filter:
            query = query.filter(
                models.AnalysisReport.discipline.ilike(f"%{discipline_filter}%")
            )

        result = await db.execute(query)
        reports = result.scalars().all()

        # Group by user (anonymized)
        users_data = {}

        for report in reports:
            user_id = report.user_id

            if user_id not in users_data:
                users_data[user_id] = {
                    # Anonymized ID
                    "user_id": f"user_{hash(str(user_id)) % 10000}",
                    "discipline": report.discipline or "Unknown",
                    "reports": [],
                    "total_findings": 0,
                    "habit_breakdown": {f"habit_{i}": 0 for i in range(1, 8)},
                }

            user_data = users_data[user_id]
            user_data["reports"].append(
                {
                    "date": report.analysis_date.date(),
                    "compliance_score": report.compliance_score or 0,
                    "findings_count": len(report.findings),
                }
            )

            # Map findings to habits
            for finding in report.findings:
                habit_info = self.habits_framework.map_finding_to_habit(
                    {
                        "issue_title": finding.issue_title or "",
                        "text": finding.problematic_text or "",
                        "risk": finding.risk,
                    }
                )

                habit_key = habit_info["habit_id"]
                user_data["habit_breakdown"][habit_key] += 1
                user_data["total_findings"] += 1

        return list(users_data.values())

    def _calculate_organizational_metrics(
        self, users_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate key organizational metrics."""

        if not users_data:
            return {}

        # Basic metrics
        total_users = len(users_data)
        total_analyses = sum(len(user["reports"]) for user in users_data)
        total_findings = sum(user["total_findings"] for user in users_data)

        # Average compliance score
        all_scores = []
        for user in users_data:
            for report in user["reports"]:
                if report["compliance_score"] > 0:
                    all_scores.append(report["compliance_score"])

        avg_compliance_score = sum(all_scores) / len(all_scores) if all_scores else 0

        # Discipline breakdown
        discipline_stats = {}
        for user in users_data:
            discipline = user["discipline"]
            if discipline not in discipline_stats:
                discipline_stats[discipline] = {
                    "user_count": 0,
                    "total_findings": 0,
                    "total_analyses": 0,
                    "compliance_scores": [],
                }

            discipline_stats[discipline]["user_count"] += 1
            discipline_stats[discipline]["total_findings"] += user["total_findings"]
            discipline_stats[discipline]["total_analyses"] += len(user["reports"])

            for report in user["reports"]:
                if report["compliance_score"] > 0:
                    discipline_stats[discipline]["compliance_scores"].append(
                        report["compliance_score"]
                    )

        # Calculate averages for each discipline
        for discipline, stats in discipline_stats.items():
            scores = stats["compliance_scores"]
            stats["avg_compliance_score"] = sum(scores) / len(scores) if scores else 0
            stats["avg_findings_per_user"] = (
                stats["total_findings"] / stats["user_count"]
            )
            stats["avg_analyses_per_user"] = (
                stats["total_analyses"] / stats["user_count"]
            )

        # Team-wide habit breakdown
        team_habit_breakdown = {f"habit_{i}": 0 for i in range(1, 8)}
        for user in users_data:
            for habit_id, count in user["habit_breakdown"].items():
                team_habit_breakdown[habit_id] += count

        # Convert to percentages
        team_habit_percentages = {}
        for habit_id, count in team_habit_breakdown.items():
            percentage = (count / total_findings * 100) if total_findings > 0 else 0
            habit_info = self.habits_framework.get_habit_details(habit_id)
            team_habit_percentages[habit_id] = {
                "habit_number": habit_info["number"],
                "habit_name": habit_info["name"],
                "count": count,
                "percentage": round(percentage, 1),
            }

        return {
            "total_users": total_users,
            "total_analyses": total_analyses,
            "total_findings": total_findings,
            "avg_compliance_score": round(avg_compliance_score, 1),
            "avg_findings_per_user": round(total_findings / total_users, 1),
            "avg_analyses_per_user": round(total_analyses / total_users, 1),
            "discipline_breakdown": discipline_stats,
            "team_habit_breakdown": team_habit_percentages,
        }

    async def _calculate_team_trends(
        self,
        db: AsyncSession,
        cutoff_date: datetime,
        discipline_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Calculate team-wide trends over time."""

        trends = []
        current_date = datetime.now(UTC).date()

        # Calculate weekly trends for the past 12 weeks
        for week_offset in range(12):
            week_start = current_date - timedelta(days=(week_offset + 1) * 7)
            week_end = current_date - timedelta(days=week_offset * 7)

            # Get reports for this week
            query = (
                select(models.AnalysisReport)
                .options(selectinload(models.AnalysisReport.findings))
                .filter(
                    and_(
                        models.AnalysisReport.analysis_date >= week_start,
                        models.AnalysisReport.analysis_date < week_end,
                    )
                )
            )

            if discipline_filter:
                query = query.filter(
                    models.AnalysisReport.discipline.ilike(f"%{discipline_filter}%")
                )

            result = await db.execute(query)
            week_reports = result.scalars().all()

            # Calculate week metrics
            week_analyses = len(week_reports)
            week_findings = sum(len(report.findings) for report in week_reports)
            week_scores = [
                report.compliance_score
                for report in week_reports
                if report.compliance_score and report.compliance_score > 0
            ]
            week_avg_score = sum(week_scores) / len(week_scores) if week_scores else 0

            # Habit breakdown for the week
            week_habit_breakdown = {f"habit_{i}": 0 for i in range(1, 8)}
            for report in week_reports:
                for finding in report.findings:
                    habit_info = self.habits_framework.map_finding_to_habit(
                        {
                            "issue_title": finding.issue_title or "",
                            "text": finding.problematic_text or "",
                            "risk": finding.risk,
                        }
                    )
                    week_habit_breakdown[habit_info["habit_id"]] += 1

            trends.append(
                {
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "total_analyses": week_analyses,
                    "total_findings": week_findings,
                    "avg_compliance_score": round(week_avg_score, 1),
                    "habit_breakdown": week_habit_breakdown,
                }
            )

        return list(reversed(trends))  # Chronological order

    def _identify_training_needs(
        self, users_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify organizational training needs based on habit patterns."""

        if not users_data:
            return []

        # Aggregate habit data across all users
        total_findings = sum(user["total_findings"] for user in users_data)
        team_habit_totals = {f"habit_{i}": 0 for i in range(1, 8)}

        for user in users_data:
            for habit_id, count in user["habit_breakdown"].items():
                team_habit_totals[habit_id] += count

        # Identify habits that need focus (>20% of findings)
        training_needs = []

        for habit_id, count in team_habit_totals.items():
            percentage = (count / total_findings * 100) if total_findings > 0 else 0

            if percentage > 20:  # High-need threshold
                habit_info = self.habits_framework.get_habit_details(habit_id)

                # Count users affected
                affected_users = sum(
                    1
                    for user in users_data
                    if user["habit_breakdown"].get(habit_id, 0) > 0
                )

                training_needs.append(
                    {
                        "habit_id": habit_id,
                        "habit_number": habit_info["number"],
                        "habit_name": habit_info["name"],
                        "principle": habit_info["principle"],
                        "percentage_of_findings": round(percentage, 1),
                        "total_findings": count,
                        "affected_users": affected_users,
                        "priority": "high" if percentage > 30 else "medium",
                        "training_focus": habit_info["clinical_application"],
                        "recommended_strategies": habit_info["improvement_strategies"][
                            :3
                        ],
                    }
                )

        # Sort by percentage (highest need first)
        training_needs.sort(key=lambda x: x["percentage_of_findings"], reverse=True)

        return training_needs

    def _calculate_benchmarks(self, users_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate benchmarking data for peer comparison."""

        if not users_data:
            return {}

        # Calculate percentiles for key metrics
        compliance_scores = []
        findings_per_user = []
        analyses_per_user = []

        for user in users_data:
            user_scores = [
                report["compliance_score"]
                for report in user["reports"]
                if report["compliance_score"] > 0
            ]
            if user_scores:
                compliance_scores.extend(user_scores)

            findings_per_user.append(user["total_findings"])
            analyses_per_user.append(len(user["reports"]))

        def calculate_percentiles(data: List[float]) -> Dict[str, float]:
            if not data:
                return {"p25": 0, "p50": 0, "p75": 0, "p90": 0}

            sorted_data = sorted(data)
            n = len(sorted_data)

            return {
                "p25": sorted_data[int(n * 0.25)],
                "p50": sorted_data[int(n * 0.50)],
                "p75": sorted_data[int(n * 0.75)],
                "p90": sorted_data[int(n * 0.90)],
            }

        return {
            "compliance_score_percentiles": calculate_percentiles(compliance_scores),
            "findings_per_user_percentiles": calculate_percentiles(findings_per_user),
            "analyses_per_user_percentiles": calculate_percentiles(analyses_per_user),
            "total_users_in_benchmark": len(users_data),
        }

    def _generate_organizational_insights(
        self,
        org_metrics: Dict[str, Any],
        team_trends: List[Dict[str, Any]],
        training_needs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate actionable organizational insights."""

        insights = []

        # Overall performance insight
        avg_score = org_metrics.get("avg_compliance_score", 0)
        if avg_score >= 85:
            insights.append(
                {
                    "type": "performance",
                    "level": "positive",
                    "title": "Excellent Team Performance",
                    "description": (
                        f"Team average compliance score of {avg_score}% "
                        "exceeds industry standards"
                    ),
                    "recommendation": (
                        "Continue current practices and consider sharing "
                        "best practices with other teams"
                    ),
                }
            )
        elif avg_score >= 70:
            insights.append(
                {
                    "type": "performance",
                    "level": "neutral",
                    "title": "Good Team Performance",
                    "description": (
                        f"Team average compliance score of {avg_score}% "
                        "meets acceptable standards"
                    ),
                    "recommendation": (
                        "Focus on targeted improvements in specific habit areas"
                    ),
                }
            )
        else:
            insights.append(
                {
                    "type": "performance",
                    "level": "concern",
                    "title": "Performance Improvement Needed",
                    "description": (
                        f"Team average compliance score of {avg_score}% "
                        "is below recommended threshold"
                    ),
                    "recommendation": (
                        "Implement comprehensive training program and "
                        "increase documentation review frequency"
                    ),
                }
            )

        # Trend analysis insight
        if len(team_trends) >= 4:
            recent_scores = [
                t["avg_compliance_score"]
                for t in team_trends[-4:]
                if t["avg_compliance_score"] > 0
            ]
            earlier_scores = [
                t["avg_compliance_score"]
                for t in team_trends[:4]
                if t["avg_compliance_score"] > 0
            ]

            if recent_scores and earlier_scores:
                recent_avg = sum(recent_scores) / len(recent_scores)
                earlier_avg = sum(earlier_scores) / len(earlier_scores)
                trend_change = recent_avg - earlier_avg

                if trend_change > 2:
                    insights.append(
                        {
                            "type": "trend",
                            "level": "positive",
                            "title": "Improving Compliance Trend",
                            "description": (
                                f"Team compliance has improved by {trend_change:.1f} "
                                "points over recent weeks"
                            ),
                            "recommendation": (
                                "Identify and replicate successful practices "
                                "across the team"
                            ),
                        }
                    )
                elif trend_change < -2:
                    insights.append(
                        {
                            "type": "trend",
                            "level": "concern",
                            "title": "Declining Compliance Trend",
                            "description": (
                                f"Team compliance has declined by "
                                f"{abs(trend_change):.1f} points over recent weeks"
                            ),
                            "recommendation": (
                                "Investigate causes and implement "
                                "corrective measures immediately"
                            ),
                        }
                    )

        # Training needs insights
        if training_needs:
            top_need = training_needs[0]
            insights.append(
                {
                    "type": "training",
                    "level": "action_required",
                    "title": f"Priority Training: {top_need['habit_name']}",
                    "description": (
                        f"{top_need['percentage_of_findings']}% of findings "
                        f"relate to {top_need['habit_name']}, affecting "
                        f"{top_need['affected_users']} team members"
                    ),
                    "recommendation": (
                        f"Implement focused training on {top_need['training_focus']}"
                    ),
                }
            )

        # Discipline-specific insights
        discipline_breakdown = org_metrics.get("discipline_breakdown", {})
        if len(discipline_breakdown) > 1:
            # Find best and worst performing disciplines
            discipline_scores = {
                d: stats["avg_compliance_score"]
                for d, stats in discipline_breakdown.items()
                if stats["avg_compliance_score"] > 0
            }

            if discipline_scores:
                best_discipline = max(discipline_scores, key=discipline_scores.get)
                worst_discipline = min(discipline_scores, key=discipline_scores.get)

                score_gap = (
                    discipline_scores[best_discipline]
                    - discipline_scores[worst_discipline]
                )
                if score_gap > 5:
                    insights.append(
                        {
                            "type": "discipline",
                            "level": "opportunity",
                            "title": "Discipline Performance Gap",
                            "description": (
                                f"{best_discipline} outperforms {worst_discipline} "
                                f"by {score_gap:.1f} points"
                            ),
                            "recommendation": (
                                f"Share best practices from {best_discipline} team "
                                f"with {worst_discipline} team"
                            ),
                        }
                    )

        return insights

    def _empty_organizational_data(self) -> Dict[str, Any]:
        """Return empty organizational data structure."""
        return {
            "analysis_period_days": 0,
            "discipline_filter": None,
            "organizational_metrics": {},
            "team_trends": [],
            "training_needs": [],
            "benchmarks": {},
            "insights": [],
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def get_peer_comparison_data(
        self, db: AsyncSession, user_id: int, days_back: int = 90
    ) -> Dict[str, Any]:
        """
        Get anonymous peer comparison data for a specific user.

        Args:
            db: Database session
            user_id: User ID for comparison
            days_back: Days to analyze

        Returns:
            Anonymous peer comparison metrics
        """
        # Get user's own data
        user_reports = await crud.get_user_reports_with_findings(
            db, user_id, since_date=datetime.now(UTC) - timedelta(days=days_back)
        )

        if not user_reports:
            return {"error": "No user data available for comparison"}

        # Calculate user metrics
        user_scores = [r.compliance_score for r in user_reports if r.compliance_score]
        user_avg_score = sum(user_scores) / len(user_scores) if user_scores else 0
        user_total_findings = sum(len(r.findings) for r in user_reports)

        # Get organizational data for comparison
        org_data = await self.get_organizational_overview(db, days_back)
        org_metrics = org_data["organizational_metrics"]
        benchmarks = org_data["benchmarks"]

        # Calculate user's percentile ranking
        def get_percentile_rank(value: float, percentiles: Dict[str, float]) -> str:
            if value >= percentiles.get("p90", 0):
                return "Top 10%"
            if value >= percentiles.get("p75", 0):
                return "Top 25%"
            if value >= percentiles.get("p50", 0):
                return "Above Average"
            if value >= percentiles.get("p25", 0):
                return "Below Average"
            return "Bottom 25%"

        compliance_percentiles = benchmarks.get("compliance_score_percentiles", {})
        findings_percentiles = benchmarks.get("findings_per_user_percentiles", {})

        return {
            "user_metrics": {
                "avg_compliance_score": round(user_avg_score, 1),
                "total_findings": user_total_findings,
                "total_analyses": len(user_reports),
            },
            "team_averages": {
                "avg_compliance_score": org_metrics.get("avg_compliance_score", 0),
                "avg_findings_per_user": org_metrics.get("avg_findings_per_user", 0),
                "avg_analyses_per_user": org_metrics.get("avg_analyses_per_user", 0),
            },
            "percentile_rankings": {
                "compliance_score": get_percentile_rank(
                    user_avg_score, compliance_percentiles
                ),
                "findings_count": get_percentile_rank(
                    user_total_findings, findings_percentiles
                ),
            },
            "comparison_insights": self._generate_peer_comparison_insights(
                user_avg_score, user_total_findings, org_metrics
            ),
        }

    def _generate_peer_comparison_insights(
        self, user_score: float, user_findings: int, org_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from peer comparison."""
        insights = []

        team_avg_score = org_metrics.get("avg_compliance_score", 0)
        team_avg_findings = org_metrics.get("avg_findings_per_user", 0)

        # Compliance score comparison
        score_diff = user_score - team_avg_score
        if score_diff > 5:
            insights.append(
                f"Your compliance score is {score_diff:.1f} points above "
                "team average - excellent work!"
            )
        elif score_diff > 0:
            insights.append(
                f"Your compliance score is {score_diff:.1f} points above team average"
            )
        elif score_diff > -5:
            insights.append(
                f"Your compliance score is {abs(score_diff):.1f} points below "
                "team average - room for improvement"
            )
        else:
            insights.append(
                f"Your compliance score is {abs(score_diff):.1f} points below "
                "team average - consider focused training"
            )

        # Findings comparison
        findings_diff = user_findings - team_avg_findings
        if findings_diff < -2:
            insights.append(
                f"You have {abs(findings_diff):.0f} fewer findings than average - "
                "great documentation quality!"
            )
        elif findings_diff > 2:
            insights.append(
                f"You have {findings_diff:.0f} more findings than average - "
                "focus on documentation improvement"
            )

        return insights
