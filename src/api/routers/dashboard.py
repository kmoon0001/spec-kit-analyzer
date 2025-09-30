from typing import List, Optional, Tuple, Dict, Any
import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import get_current_active_user, require_admin
from ...database import crud, models, schemas
from ...database.schemas import DirectorDashboardData, CoachingFocus
from ...database import get_async_db
from ...core.report_generator import ReportGenerator
from ...config import get_settings
from ...core.llm_service import LLMService

settings = get_settings()


def _resolve_generator_model(cfg) -> Tuple[str, str]:
    """Resolve the generator model repo and filename from settings.

    Prefers a named profile if provided; otherwise falls back to legacy fields.
    """
    # Prefer profile lookup if configured
    profile_key = cfg.models.generator
    profiles = cfg.models.generator_profiles or {}
    if profile_key and profile_key in profiles:
        profile = profiles[profile_key]
        return profile.repo, profile.filename

    # Fallback to legacy fields
    if cfg.models.generator and cfg.models.generator_filename:
        return cfg.models.generator, cfg.models.generator_filename

    raise ValueError("Generator model configuration is missing (repo/filename)")


router = APIRouter()
report_generator = ReportGenerator()


@router.get("/reports", response_model=List[schemas.Report])
async def read_reports(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return await crud.get_reports(db, skip=skip, limit=limit)


@router.get("/reports/{report_id}", response_class=HTMLResponse)
async def read_report(
    report_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_report = await crud.get_report(db, report_id=report_id)
    if db_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    report_html = report_generator.generate_html_report(
        analysis_result=db_report.analysis_result,
        doc_name=db_report.document_name,
        analysis_mode="rubric",
    )
    return HTMLResponse(content=report_html)


@router.get("/findings-summary", response_model=List[schemas.FindingSummary])
async def read_findings_summary(
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    if hasattr(crud, "get_findings_summary"):
        return await crud.get_findings_summary(db)
    return []


@router.get(
    "/director-dashboard",
    response_model=DirectorDashboardData,
    dependencies=[Depends(require_admin)],
)
async def get_director_dashboard_data(
    db: AsyncSession = Depends(get_async_db),
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    discipline: Optional[str] = None,
):
    """
    Provides aggregated analytics data for the director's dashboard.
    Accessible only by admin users and filterable by date and discipline.
    """
    if not settings.enable_director_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Director Dashboard feature is not enabled.",
        )

    total_findings = await crud.get_total_findings_count(
        db, start_date=start_date, end_date=end_date, discipline=discipline
    )
    team_summary = await crud.get_team_habit_summary(
        db, start_date=start_date, end_date=end_date, discipline=discipline
    )
    clinician_breakdown = await crud.get_clinician_habit_breakdown(
        db, start_date=start_date, end_date=end_date, discipline=discipline
    )

    return DirectorDashboardData(
        total_findings=total_findings,
        team_habit_summary=team_summary,
        clinician_habit_breakdown=clinician_breakdown,
    )


@router.post(
    "/coaching-focus",
    response_model=CoachingFocus,
    dependencies=[Depends(require_admin)],
)
async def generate_coaching_focus(dashboard_data: DirectorDashboardData):
    """
    Generates an AI-powered weekly coaching focus based on team analytics.
    """
    if not settings.enable_director_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Director Dashboard feature is not enabled.",
        )

    # In a larger application, this service would be managed via a dependency injection system.
    repo_id, filename = _resolve_generator_model(settings)
    llm_service = LLMService(
        model_repo_id=repo_id,
        model_filename=filename,
        llm_settings={
            "model_type": settings.llm_settings.model_type,
            "context_length": settings.llm_settings.context_length,
            "generation_params": settings.llm_settings.generation_params,
        },
    )

    if not llm_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service is not available.",
        )

    prompt = f'''
You are an expert clinical director AI assistant. Based on the following team performance data, generate a concise and actionable weekly coaching focus. The focus should identify the most critical issue and provide concrete steps for improvement.

**Team Analytics Data:**
- **Total Compliance Findings:** {dashboard_data.total_findings}
- **Top Habit-Related Issues:**
'''
    for item in dashboard_data.team_habit_summary[:3]:
        prompt += f"  - {item.habit_name}: {item.count} findings\\n"

    prompt += "\\n**Clinician-Specific Breakdown (Top 5):**\\n"
    for item in dashboard_data.clinician_habit_breakdown[:5]:
        prompt += f"  - {item.clinician_name} ({item.habit_name}): {item.count} findings\\n"

    prompt += """
**Your Task:**
Generate a JSON object with the following structure. Infer a likely root cause for the primary issue based on the data.
{{
  "focus_title": "A compelling title for the weekly focus.",
  "summary": "A brief summary explaining the most significant issue and its impact.",
  "root_cause": "The inferred root cause of the issue (e.g., 'Lack of familiarity with new guidelines', 'Time management during patient care').",
  "action_steps": [
    "A concrete, actionable step for the team related to the root cause.",
    "Another actionable step.",
    "A final actionable step."
  ]
}}

Return only the JSON object.
"""

    try:
        raw_response = llm_service.generate_analysis(prompt)
        coaching_data = llm_service.parse_json_output(raw_response)
        return CoachingFocus(**coaching_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate coaching focus: {e}",
        )


@router.get(
    "/habit-trends",
    response_model=List[schemas.HabitTrendPoint],
    dependencies=[Depends(require_admin)],
)
async def get_habit_trends(
    db: AsyncSession = Depends(get_async_db),
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
):
    """
    Provides data for habit trend analysis over time.
    """
    if not settings.enable_director_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Director Dashboard feature is not enabled.",
        )
    return await crud.get_habit_trend_data(
        db, start_date=start_date, end_date=end_date
    )
