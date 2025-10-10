"""Intelligent Report Generator - Advanced reporting with deep insights and reasoning

This module creates comprehensive, non-repetitive reports that demonstrate deep thinking,
provide actionable insights, and serve as effective training tools while maintaining
professional presentation and compliance standards.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class InsightType(Enum):
    """Types of insights that can be generated"""

    TREND_ANALYSIS = "trend_analysis"
    ROOT_CAUSE = "root_cause"
    PREDICTIVE = "predictive"
    COMPARATIVE = "comparative"
    CORRELATION = "correlation"
    ANOMALY = "anomaly"
    OPTIMIZATION = "optimization"
    RISK_ASSESSMENT = "risk_assessment"


class ReportSection(Enum):
    """Standardized report sections"""

    EXECUTIVE_SUMMARY = "executive_summary"
    KEY_FINDINGS = "key_findings"
    DETAILED_ANALYSIS = "detailed_analysis"
    INSIGHTS_AND_REASONING = "insights_and_reasoning"
    ACTIONABLE_RECOMMENDATIONS = "actionable_recommendations"
    TRAINING_POINTS = "training_points"
    COMPLIANCE_STATUS = "compliance_status"
    VISUAL_ANALYTICS = "visual_analytics"


@dataclass
class Insight:
    """Represents a data-driven insight with reasoning"""

    insight_type: InsightType
    title: str
    description: str
    reasoning: str
    evidence: list[str]
    confidence_score: float
    impact_level: str  # high, medium, low
    actionable_steps: list[str]
    training_value: str
    compliance_relevance: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "insight_type": self.insight_type.value,
            "title": self.title,
            "description": self.description,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "confidence_score": self.confidence_score,
            "impact_level": self.impact_level,
            "actionable_steps": self.actionable_steps,
            "training_value": self.training_value,
            "compliance_relevance": self.compliance_relevance,
        }


@dataclass
class ReportContent:
    """Structured report content with insights"""

    section: ReportSection
    title: str
    content: str
    insights: list[Insight] = field(default_factory=list)
    visualizations: list[dict[str, Any]] = field(default_factory=list)
    key_metrics: dict[str, Any] = field(default_factory=dict)
    priority_level: int = 1  # 1=highest, 5=lowest
