# MODIFIED: Added timezone and timedelta imports.
"""
Database CRUD operations for the Therapy Compliance Analyzer.

Provides async database operations for users, rubrics, reports, and findings.
"""

import datetime
import logging
import numpy as np
from typing import List, Optional, Dict, Any
from collections import defaultdict
from datetime import timezone, timedelta

from sqlalchemy import delete, select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from . import models, schemas
from ..core.vector_store import get_vector_store

logger = logging.getLogger(__name__)

# ... (user, rubric, feedback functions remain the same) ...

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
    compliance_by_category = {row.document_type: row.average_score for row in category_result.all() if row.document_type}

    return {
        "total_documents_analyzed": total_documents_analyzed,
        "overall_compliance_score": overall_compliance_score,
        "compliance_by_category": compliance_by_category,
    }

async def get_organizational_metrics(db: AsyncSession, days_back: int) -> Dict[str, Any]:
    """Computes high-level organizational metrics."""
    cutoff_date = datetime.datetime.now(timezone.utc) - timedelta(days=days_back)
    
    report_query = select(models.AnalysisReport).filter(models.AnalysisReport.analysis_date >= cutoff_date)
    reports = list((await db.execute(report_query.options(selectinload(models.AnalysisReport.findings)))).scalars().unique().all())
    
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
    """Computes compliance metrics broken down by discipline, querying the JSON field."""
    cutoff_date = datetime.datetime.now(timezone.utc) - timedelta(days=days_back)
    
    query = (
        select(
            models.AnalysisReport.analysis_result["discipline"].as_string().label("discipline"),
            func.avg(models.AnalysisReport.compliance_score).label("avg_score"),
            func.count(models.AnalysisReport.id).label("user_count")
        )
        .filter(models.AnalysisReport.analysis_date >= cutoff_date)
        .group_by(models.AnalysisReport.analysis_result["discipline"].as_string())
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
    for i in range(num_weeks):
        end_date = datetime.datetime.now(timezone.utc) - datetime.timedelta(weeks=i)
        start_date = end_date - datetime.timedelta(weeks=1)
        
        query = (
            select(
                func.avg(models.AnalysisReport.compliance_score).label("avg_score"),
                func.count(models.Finding.id).label("total_findings")
            )
            .join(models.AnalysisReport, models.Finding.report_id == models.AnalysisReport.id, isouter=True)
            .filter(and_(models.AnalysisReport.analysis_date >= start_date, models.AnalysisReport.analysis_date < end_date))
        )
        result = (await db.execute(query)).first()
        trends.append({
            "week": i + 1,
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
        "total_users_in_benchmark": (await db.execute(select(func.count(models.User.id)))).scalar_one_or_none() or 0,
        "compliance_score_percentiles": {
            "p25": np.percentile(scores, 25),
            "p50": np.percentile(scores, 50),
            "p75": np.percentile(scores, 75),
            "p90": np.percentile(scores, 90),
        },
    }

# ... (rest of the file remains the same) ...
