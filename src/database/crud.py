# MODIFIED: Added timezone and timedelta imports.
"""
Database CRUD operations for the Therapy Compliance Analyzer.

Provides async database operations for users, rubrics, reports, and findings.
"""

import datetime
import logging
import math
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
    """Computes team performance trends grouped by week."""
    if days_back <= 0:
        return []

    now = datetime.datetime.now(timezone.utc)
    num_weeks = max(1, math.ceil(days_back / 7))
    cutoff_date = now - datetime.timedelta(days=days_back)

    query = (
        select(models.AnalysisReport)
        .options(selectinload(models.AnalysisReport.findings))
        .where(models.AnalysisReport.analysis_date >= cutoff_date)
    )
    result = await db.execute(query)
    reports = list(result.scalars().unique().all())

    def _as_aware(dt: datetime.datetime) -> datetime.datetime:
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    trends: List[Dict[str, Any]] = []
    for index in range(num_weeks):
        week_end = now - datetime.timedelta(days=index * 7)
        week_start = week_end - datetime.timedelta(days=7)

        week_reports = [
            report
            for report in reports
            if week_start <= _as_aware(report.analysis_date) < week_end
        ]

        if week_reports:
            avg_score = float(np.mean([report.compliance_score for report in week_reports]))
            total_findings = sum(len(report.findings) for report in week_reports)
        else:
            avg_score = 0.0
            total_findings = 0

        trends.append(
            {
                "week": index + 1,
                "avg_compliance_score": avg_score,
                "total_findings": total_findings,
            }
        )

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


async def get_report(db: AsyncSession, report_id: int) -> Optional[models.AnalysisReport]:
    """Fetches a single analysis report with its findings eagerly loaded."""
    query = (
        select(models.AnalysisReport)
        .options(selectinload(models.AnalysisReport.findings))
        .where(models.AnalysisReport.id == report_id)
    )
    result = await db.execute(query)
    return result.scalars().first()


async def find_similar_report(
    db: AsyncSession,
    document_type: Optional[str],
    exclude_report_id: Optional[int] = None,
    embedding: Optional[bytes] = None,
    threshold: float = 0.85,
) -> Optional[models.AnalysisReport]:
    """Finds a similar report using the vector store, with a fallback to recency."""
    candidate_ids: List[int] = []
    vector_store = get_vector_store()

    if embedding:
        if not vector_store.is_initialized:
            vector_store.initialize_index()

        if vector_store.is_initialized:
            try:
                query_vector = np.frombuffer(embedding, dtype=np.float32)
                if query_vector.size:
                    query_vector = query_vector.reshape(1, -1)
                    for report_id, _ in vector_store.search(query_vector, k=5, threshold=threshold):
                        report_id = int(report_id)
                        if exclude_report_id is not None and report_id == exclude_report_id:
                            continue
                        if report_id not in candidate_ids:
                            candidate_ids.append(report_id)
            except (ValueError, TypeError) as exc:
                logger.warning("Invalid embedding supplied to find_similar_report: %s", exc)

    for candidate_id in candidate_ids:
        candidate = await get_report(db, candidate_id)
        if candidate and (document_type is None or candidate.document_type == document_type):
            return candidate

    for candidate_id in candidate_ids:
        candidate = await get_report(db, candidate_id)
        if candidate:
            return candidate

    query = select(models.AnalysisReport)
    if document_type is not None:
        query = query.where(models.AnalysisReport.document_type == document_type)

    if exclude_report_id is not None:
        query = query.where(models.AnalysisReport.id != exclude_report_id)

    query = query.order_by(models.AnalysisReport.analysis_date.desc())
    result = await db.execute(query)
    return result.scalars().first()


# ... (rest of the file remains the same) ...
