import logging
import os
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException

from ...database import models
from ...auth import get_current_active_user
from ...core.analysis_service import AnalysisService
from ..dependencies import get_analysis_service
from ...database import get_async_db
from ...database import crud
from ...config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

tasks = {}

def get_analysis_service():
    return AnalysisService()

def _calculate_compliance_score(analysis_result: Dict[str, Any]) -> str:
    """Calculates a numeric compliance score from analysis findings."""
    base_score = 100
    if "findings" not in analysis_result or not analysis_result["findings"]:
        return str(base_score)

    score_deductions = {"High": 10, "Medium": 5, "Low": 2}
    current_score = base_score
    for finding in analysis_result["findings"]:
        risk = finding.get("risk", "Low")
        current_score -= score_deductions.get(risk, 0)
    return str(max(0, current_score))

async def anext(gen: AsyncGenerator):