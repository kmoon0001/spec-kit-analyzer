import datetime
import logging
from time import perf_counter
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from src.database.schemas import DirectorDashboardData, CoachingFocus
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import crud, models, schemas
from src.api.dependencies import require_admin
from src.api.limiter import limiter
from src.auth import get_current_active_user
from src.config import Settings, get_settings
from src.core.llm_service import LLMService
from src.core.report_generator import ReportGenerator
from src.database.database import get_async_db

logger = logging.getLogger(__name__)
router = APIRouter()
report_generator = ReportGenerator()


# --- Helper Functions ---#


def _resolve_generator_model(settings: Settings) -> Tuple[str, str]:
    """Resolves the generator model from settings, preferring profiles."""
    if settings.models.generator_profiles:
        # In this context, we can just use the first available profile.
        profile = next(iter(settings.models.generator_profiles.values()))
        return profile.repo, profile.filename

    if settings.models.generator and settings.models.generator_filename:
        return settings.models.generator, settings.models.generator_filename

    # If no generator model is configured, something is wrong.
    raise ValueError("Could not resolve a generator model from the settings.")


@router.get("/reports", response_model=List[schemas.AnalysisReport])
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