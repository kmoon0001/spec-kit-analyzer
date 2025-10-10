"""Enhanced Analytics Service for compliance trend analysis and insights.
Provides safe, stable analytics features with optional advanced capabilities.
"""

import logging
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ComplianceTrend:
    """Data structure for compliance trend information."""

    date: str
    avg_score: float
    document_count: int
    risk_distribution: dict[str, int]


@dataclass
class AnalyticsInsight:
    """Data structure for analytics insights."""

    insight_type: str
    title: str
    description: str
    impact_level: str  # High, Medium, Low
    recommendation: str
    data_points: dict[str, Any]


class AnalyticsService:
    """Enhanced analytics service for compliance data analysis.
    Provides trend analysis, pattern detection, and actionable insights.
    """

    def __init__(self, enable_advanced_features: bool = True):
        self.enable_advanced_features = enable_advanced_features
        self.cache: dict[str, Any] = {}  # Simple caching for expensive calculations
        logger.info("Analytics service initialized (advanced features: %s)", enable_advanced_features)

    def calculate_compliance_trends(
        self,
        reports_data: list[dict[str, Any]],
        days: int = 30) -> list[ComplianceTrend]:
        """Calculate compliance trends over time.

        Args:
            reports_data: List of report dictionaries with analysis results
            days: Number of days to analyze

        Returns:
            List of ComplianceTrend objects with daily statistics

        """
        try:
            # Group reports by date
            daily_data = defaultdict(list)
            cutoff_date = datetime.now() - timedelta(days=days)

            for report in reports_data:
                report_date = report.get("analysis_date")
                if not report_date:
                    continue

                # Parse date if it's a string
                if isinstance(report_date, str):
                    try:
                        report_date = datetime.fromisoformat(
                            report_date.replace("Z", "+00:00"))
                    except ValueError:
                        continue

                if report_date >= cutoff_date:
                    date_key = report_date.strftime("%Y-%m-%d")
                    daily_data[date_key].append(report)

            # Calculate trends
            trends = []
            for date_str, day_reports in sorted(daily_data.items()):
                if not day_reports:
                    continue

                # Calculate average compliance score
                scores = [r.get("compliance_score", 0) for r in day_reports if r.get("compliance_score") is not None]
                avg_score = statistics.mean(scores) if scores else 0

                # Calculate risk distribution
                risk_dist: dict[str, int] = defaultdict(int)
                for report in day_reports:
                    findings = report.get("findings", [])
                    for finding in findings:
                        risk = finding.get("risk", "Low")
                        risk_dist[risk] += 1

                trend = ComplianceTrend(
                    date=date_str,
                    avg_score=avg_score,
                    document_count=len(day_reports),
                    risk_distribution=dict(risk_dist))
                trends.append(trend)

            logger.info("Calculated trends for %s days", len(trends))
            return trends

        except Exception as e:
            logger.exception("Error calculating compliance trends: %s", e)
            return []

    def identify_common_issues(
        self,
        reports_data: list[dict[str, Any]],
        min_frequency: int = 3) -> list[dict[str, Any]]:
        """Identify commonly occurring compliance issues.

        Args:
            reports_data: List of report data
            min_frequency: Minimum frequency for an issue to be considered common

        Returns:
            List of common issues with frequency and impact data

        """
        try:
            issue_counter: Counter[str] = Counter()
            issue_details = defaultdict(list)

            for report in reports_data:
                findings = report.get("findings", [])
                for finding in findings:
                    rule_id = finding.get("rule_id", "Unknown")
                    risk = finding.get("risk", "Low")

                    issue_counter[rule_id] += 1
                    issue_details[rule_id].append(
                        {
                            "risk": risk,
                            "document": report.get("document_name", "Unknown"),
                            "date": report.get("analysis_date", "Unknown"),
                        })

            # Filter and format common issues
            common_issues = []
            for rule_id, frequency in issue_counter.items():
                if frequency >= min_frequency:
                    details = issue_details[rule_id]

                    # Calculate risk distribution for this issue
                    risk_counts: Counter[str] = Counter(d["risk"] for d in details)

                    # Determine overall impact
                    high_risk_count = risk_counts.get("High", 0)
                    if high_risk_count > frequency * 0.5:
                        impact = "High"
                    elif high_risk_count > 0 or risk_counts.get("Medium", 0) > frequency * 0.3:
                        impact = "Medium"
                    else:
                        impact = "Low"

                    common_issues.append(
                        {
                            "rule_id": rule_id,
                            "frequency": frequency,
                            "impact": impact,
                            "risk_distribution": dict(risk_counts),
                            "affected_documents": len(
                                set(d["document"] for d in details)),
                        })

            # Sort by frequency and impact
            common_issues.sort(
                key=lambda x: (x["frequency"], x["impact"] == "High"),
                reverse=True)

            logger.info("Identified %s common compliance issues", len(common_issues))
            return common_issues

        except Exception as e:
            logger.exception("Error identifying common issues: %s", e)
            return []

    def calculate_performance_metrics(
        self,
        reports_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate key performance metrics for compliance analysis.

        Args:
            reports_data: List of report data

        Returns:
            Dictionary with performance metrics

        """
        try:
            if not reports_data:
                return {}

            # Basic metrics
            total_reports = len(reports_data)
            scores = [r.get("compliance_score", 0) for r in reports_data if r.get("compliance_score") is not None]

            if not scores:
                return {
                    "total_reports": total_reports,
                    "error": "No valid scores found",
                }

            avg_score = statistics.mean(scores)
            median_score = statistics.median(scores)
            score_std = statistics.stdev(scores) if len(scores) > 1 else 0

            # Risk analysis
            total_findings = 0
            risk_counts: dict[str, int] = defaultdict(int)

            for report in reports_data:
                findings = report.get("findings", [])
                total_findings += len(findings)
                for finding in findings:
                    risk = finding.get("risk", "Low")
                    risk_counts[risk] += 1

            # Document type analysis
            doc_type_counts: Counter[str] = Counter()
            doc_type_scores = defaultdict(list)

            for report in reports_data:
                doc_type = report.get("document_type", "Unknown")
                score = report.get("compliance_score")

                doc_type_counts[doc_type] += 1
                if score is not None:
                    doc_type_scores[doc_type].append(score)

            # Calculate averages by document type
            doc_type_averages = {}
            for doc_type, type_scores in doc_type_scores.items():
                if type_scores:
                    doc_type_averages[doc_type] = statistics.mean(type_scores)

            metrics = {
                "total_reports": total_reports,
                "total_findings": total_findings,
                "average_compliance_score": round(avg_score, 2),
                "median_compliance_score": round(median_score, 2),
                "score_standard_deviation": round(score_std, 2),
                "risk_distribution": dict(risk_counts),
                "document_type_distribution": dict(doc_type_counts),
                "document_type_averages": doc_type_averages,
                "findings_per_report": (round(total_findings / total_reports, 2) if total_reports > 0 else 0),
            }

            logger.info("Performance metrics calculated successfully")
            return metrics

        except Exception as e:
            logger.exception("Error calculating performance metrics: %s", e)
            return {"error": str(e)}

    def generate_insights(
        self,
        reports_data: list[dict[str, Any]],
        trends: list[ComplianceTrend]) -> list[AnalyticsInsight]:
        """Generate actionable insights from compliance data.

        Args:
            reports_data: List of report data
            trends: List of compliance trends

        Returns:
            List of AnalyticsInsight objects with recommendations

        """
        insights = []

        try:
            # Trend analysis insights
            if len(trends) >= 7:  # Need at least a week of data
                recent_scores = [t.avg_score for t in trends[-7:]]
                older_scores = [t.avg_score for t in trends[-14:-7]] if len(trends) >= 14 else []

                if older_scores and recent_scores:
                    recent_avg = statistics.mean(recent_scores)
                    older_avg = statistics.mean(older_scores)

                    if recent_avg < older_avg - 5:  # Significant decline
                        insights.append(
                            AnalyticsInsight(
                                insight_type="trend_decline",
                                title="Declining Compliance Trend",
                                description=f"Compliance scores have declined by {older_avg - recent_avg} points over the past week.",
                                impact_level="High",
                                recommendation="Review recent documentation practices and provide additional training if needed.",
                                data_points={
                                    "recent_avg": recent_avg,
                                    "older_avg": older_avg,
                                }))
                    elif recent_avg > older_avg + 5:  # Significant improvement
                        insights.append(
                            AnalyticsInsight(
                                insight_type="trend_improvement",
                                title="Improving Compliance Trend",
                                description=f"Compliance scores have improved by {recent_avg - older_avg} points over the past week.",
                                impact_level="Low",
                                recommendation="Continue current documentation practices and consider sharing best practices with team.",
                                data_points={
                                    "recent_avg": recent_avg,
                                    "older_avg": older_avg,
                                }))

            # Common issues insights
            common_issues = self.identify_common_issues(reports_data, min_frequency=2)
            if common_issues:
                top_issue = common_issues[0]
                insights.append(
                    AnalyticsInsight(
                        insight_type="common_issue",
                        title="Most Frequent Compliance Issue",
                        description=f"Rule {top_issue['rule_id']} appears in {top_issue['frequency']} reports.",
                        impact_level=top_issue["impact"],
                        recommendation="Focus training and quality improvement efforts on this specific compliance area.",
                        data_points=top_issue))

            # Performance insights
            metrics = self.calculate_performance_metrics(reports_data)
            avg_score = metrics.get("average_compliance_score", 0)

            if avg_score < 70:
                insights.append(
                    AnalyticsInsight(
                        insight_type="low_performance",
                        title="Below Target Compliance Score",
                        description=f"Average compliance score of {avg_score}% is below the recommended 70% threshold.",
                        impact_level="High",
                        recommendation="Implement comprehensive compliance training and review documentation standards.",
                        data_points={"current_score": avg_score, "target_score": 70}))
            elif avg_score > 90:
                insights.append(
                    AnalyticsInsight(
                        insight_type="high_performance",
                        title="Excellent Compliance Performance",
                        description=f"Average compliance score of {avg_score}% exceeds excellence threshold.",
                        impact_level="Low",
                        recommendation="Maintain current practices and consider mentoring other teams.",
                        data_points={"current_score": avg_score}))

            logger.info("Generated %s analytics insights", len(insights))
            return insights

        except Exception as e:
            logger.exception("Error generating insights: %s", e)
            return []

    def export_analytics_data(
        self,
        reports_data: list[dict[str, Any]],
        format_type: str = "summary") -> dict[str, Any]:
        """Export analytics data in various formats for external analysis.

        Args:
            reports_data: List of report data
            format_type: Type of export (summary, detailed, raw)

        Returns:
            Dictionary with exported data

        """
        try:
            if format_type == "summary":
                return {
                    "metrics": self.calculate_performance_metrics(reports_data),
                    "trends": [
                        {
                            "date": t.date,
                            "avg_score": t.avg_score,
                            "document_count": t.document_count,
                        }
                        for t in self.calculate_compliance_trends(reports_data)
                    ],
                    "common_issues": self.identify_common_issues(reports_data)[:10],
                    "export_timestamp": datetime.now().isoformat(),
                }

            if format_type == "detailed":
                trends = self.calculate_compliance_trends(reports_data)
                insights = self.generate_insights(reports_data, trends)

                return {
                    "metrics": self.calculate_performance_metrics(reports_data),
                    "trends": [
                        {
                            "date": t.date,
                            "avg_score": t.avg_score,
                            "document_count": t.document_count,
                            "risk_distribution": t.risk_distribution,
                        }
                        for t in trends
                    ],
                    "insights": [
                        {
                            "type": i.insight_type,
                            "title": i.title,
                            "description": i.description,
                            "impact": i.impact_level,
                            "recommendation": i.recommendation,
                        }
                        for i in insights
                    ],
                    "common_issues": self.identify_common_issues(reports_data),
                    "export_timestamp": datetime.now().isoformat(),
                }

            # raw format
            return {
                "reports": reports_data,
                "export_timestamp": datetime.now().isoformat(),
                "total_count": len(reports_data),
            }

        except Exception as e:
            logger.exception("Error exporting analytics data: %s", e)
            return {"error": str(e)}


# Global analytics service instance
# Global analytics service instance
# Global analytics service instance
analytics_service = AnalyticsService()


def get_analytics_service(enable_advanced: bool = True) -> AnalyticsService:
    """Get analytics service instance with specified configuration."""
    return AnalyticsService(enable_advanced_features=enable_advanced)
