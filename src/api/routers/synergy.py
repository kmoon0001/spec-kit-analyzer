"""
API Router for the Synergy Session feature.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

from ..dependencies import get_analysis_service
from ...auth import get_current_active_user
from ...core.analysis_service import AnalysisService
from ...database import models

logger = logging.getLogger(__name__)
router = APIRouter()

class SynergyRequest(BaseModel):
    """Request model for a synergy session."""
    scenario: str
    discipline: str = "Physical Therapy"

class SynergyResponse(BaseModel):
    """Response model for a synergy session."""
    suggestions: list[str]
    guidelines: list[Dict[str, Any]]

@router.post("/synergy-session", response_model=SynergyResponse)
async def run_synergy_session(
    request: SynergyRequest,
    service: AnalysisService = Depends(get_analysis_service),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Endpoint to run a synergy session. Takes a clinical scenario and returns
    AI-generated documentation suggestions and relevant compliance guidelines.
    """
    logger.info(f"User '{current_user.username}' initiated a synergy session.")
    try:
        synergy_data = await service.synergy_service.generate_synergy_data(
            scenario=request.scenario,
            discipline=request.discipline
        )

        if "error" in synergy_data:
            raise HTTPException(status_code=500, detail=synergy_data["error"])

        return SynergyResponse(**synergy_data)

    except Exception as e:
        logger.error(f"Error during synergy session for user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {e}")