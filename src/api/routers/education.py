"""API endpoints for Clinical Education Engine.

This module provides REST API endpoints for the clinical education system,
including learning paths, content delivery, progress tracking, and competency assessment.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.dependencies import get_current_active_user
from src.core.clinical_education_engine import (
    ClinicalEducationEngine,
    LearningLevel,
    ContentType,
    CompetencyArea,
    clinical_education_engine
)
from src import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/education", tags=["education"])


# Pydantic models for API
class LearningPathRequest(BaseModel):
    """Request model for creating learning paths."""
    competency_focus: str = Field(..., description="Primary competency area")
    learning_level: str = Field(..., description="User's learning level")
    analysis_findings: Optional[List[Dict[str, Any]]] = Field(None, description="Recent analysis findings")


class LearningPathResponse(BaseModel):
    """Response model for learning paths."""
    path_id: str
    title: str
    description: str
    competency_focus: str
    learning_level: str
    objectives_count: int
    content_items_count: int
    estimated_completion_hours: float
    progress_percentage: float


class LearningSessionRequest(BaseModel):
    """Request model for starting learning sessions."""
    content_id: str = Field(..., description="Content ID to learn")
    learning_path_id: Optional[str] = Field(None, description="Optional learning path ID")


class LearningSessionResponse(BaseModel):
    """Response model for learning sessions."""
    progress_id: str
    content_id: str
    learning_path_id: Optional[str]
    started_at: datetime
    content_title: str
    content_type: str
    duration_minutes: int


class LearningCompletionRequest(BaseModel):
    """Request model for completing learning sessions."""
    completion_percentage: float = Field(..., ge=0.0, le=100.0, description="Completion percentage")
    quiz_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quiz score")
    competency_rating: Optional[float] = Field(None, ge=0.0, le=1.0, description="Competency rating")
    feedback: Optional[str] = Field(None, description="User feedback")


class CompetencyAssessmentRequest(BaseModel):
    """Request model for competency assessments."""
    competency_area: str = Field(..., description="Competency area to assess")
    assessment_data: Dict[str, Any] = Field(..., description="Assessment data")


class CompetencyAssessmentResponse(BaseModel):
    """Response model for competency assessments."""
    assessment_id: str
    competency_area: str
    score: float
    level_achieved: str
    strengths: List[str]
    improvement_areas: List[str]
    recommendations: List[str]
    assessment_date: datetime


class LearningDashboardResponse(BaseModel):
    """Response model for learning dashboard."""
    user_id: int
    competencies: Dict[str, float]
    learning_statistics: Dict[str, Any]
    recent_progress: List[Dict[str, Any]]
    learning_paths: List[Dict[str, Any]]
    recent_assessments: List[Dict[str, Any]]
    recommendations: List[str]


@router.post("/learning-paths", response_model=LearningPathResponse)
async def create_learning_path(
    request: LearningPathRequest,
    current_user: models.User = Depends(get_current_active_user),
    education_engine: ClinicalEducationEngine = Depends(lambda: clinical_education_engine)
) -> LearningPathResponse:
    """Create a personalized learning path for a user.

    Args:
        request: Learning path creation request
        current_user: Current authenticated user
        education_engine: Education engine instance

    Returns:
        Created learning path
    """
    try:
        # Validate competency focus
        try:
            competency_focus = CompetencyArea(request.competency_focus)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid competency focus: {request.competency_focus}"
            )

        # Validate learning level
        try:
            learning_level = LearningLevel(request.learning_level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid learning level: {request.learning_level}"
            )

        # Create learning path
        learning_path = await education_engine.create_personalized_learning_path(
            user_id=current_user.id,
            competency_focus=competency_focus,
            learning_level=learning_level,
            analysis_findings=request.analysis_findings
        )

        logger.info("Created learning path for user %d: %s", current_user.id, learning_path.path_id)

        return LearningPathResponse(
            path_id=learning_path.path_id,
            title=learning_path.title,
            description=learning_path.description,
            competency_focus=learning_path.competency_focus.value,
            learning_level=learning_path.learning_level.value,
            objectives_count=len(learning_path.objectives),
            content_items_count=len(learning_path.content_items),
            estimated_completion_hours=learning_path.estimated_completion_hours,
            progress_percentage=learning_path.progress_percentage
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create learning path: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create learning path: {str(e)}"
        )


@router.post("/sessions", response_model=LearningSessionResponse)
async def start_learning_session(
    request: LearningSessionRequest,
    current_user: models.User = Depends(get_current_active_user),
    education_engine: ClinicalEducationEngine = Depends(lambda: clinical_education_engine)
) -> LearningSessionResponse:
    """Start a learning session for a user.

    Args:
        request: Learning session request
        current_user: Current authenticated user
        education_engine: Education engine instance

    Returns:
        Learning session information
    """
    try:
        # Start learning session
        progress = await education_engine.start_learning_session(
            user_id=current_user.id,
            content_id=request.content_id,
            learning_path_id=request.learning_path_id
        )

        # Get content information
        content = education_engine.educational_content.get(request.content_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content not found: {request.content_id}"
            )

        logger.info("Started learning session for user %d: %s", current_user.id, request.content_id)

        return LearningSessionResponse(
            progress_id=progress.progress_id,
            content_id=progress.content_id,
            learning_path_id=progress.learning_path_id,
            started_at=progress.started_at,
            content_title=content.title,
            content_type=content.content_type.value,
            duration_minutes=content.duration_minutes
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to start learning session: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start learning session: {str(e)}"
        )


@router.post("/sessions/{progress_id}/complete")
async def complete_learning_session(
    progress_id: str,
    request: LearningCompletionRequest,
    current_user: models.User = Depends(get_current_active_user),
    education_engine: ClinicalEducationEngine = Depends(lambda: clinical_education_engine)
) -> Dict[str, Any]:
    """Complete a learning session.

    Args:
        progress_id: Progress ID
        request: Completion request
        current_user: Current authenticated user
        education_engine: Education engine instance

    Returns:
        Completion confirmation
    """
    try:
        # Complete learning session
        progress = await education_engine.complete_learning_session(
            progress_id=progress_id,
            completion_percentage=request.completion_percentage,
            quiz_score=request.quiz_score,
            competency_rating=request.competency_rating,
            feedback=request.feedback
        )

        logger.info("Completed learning session for user %d: %s", current_user.id, progress_id)

        return {
            "progress_id": progress_id,
            "status": "completed",
            "completion_percentage": progress.completion_percentage,
            "time_spent_minutes": progress.time_spent_minutes,
            "quiz_score": progress.quiz_score,
            "competency_rating": progress.competency_rating,
            "completed_at": progress.completed_at.isoformat()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Failed to complete learning session: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete learning session: {str(e)}"
        )


@router.post("/assessments", response_model=CompetencyAssessmentResponse)
async def assess_competency(
    request: CompetencyAssessmentRequest,
    current_user: models.User = Depends(get_current_active_user),
    education_engine: ClinicalEducationEngine = Depends(lambda: clinical_education_engine)
) -> CompetencyAssessmentResponse:
    """Assess user competency in a specific area.

    Args:
        request: Competency assessment request
        current_user: Current authenticated user
        education_engine: Education engine instance

    Returns:
        Competency assessment result
    """
    try:
        # Validate competency area
        try:
            competency_area = CompetencyArea(request.competency_area)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid competency area: {request.competency_area}"
            )

        # Assess competency
        assessment = await education_engine.assess_competency(
            user_id=current_user.id,
            competency_area=competency_area,
            assessment_data=request.assessment_data
        )

        logger.info("Completed competency assessment for user %d in %s: %.2f",
                   current_user.id, competency_area.value, assessment.score)

        return CompetencyAssessmentResponse(
            assessment_id=assessment.assessment_id,
            competency_area=assessment.competency_area.value,
            score=assessment.score,
            level_achieved=assessment.level_achieved.value,
            strengths=assessment.strengths,
            improvement_areas=assessment.improvement_areas,
            recommendations=assessment.recommendations,
            assessment_date=assessment.assessment_date
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to assess competency: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess competency: {str(e)}"
        )


@router.get("/recommendations")
async def get_learning_recommendations(
    analysis_findings: Optional[str] = None,
    current_user: models.User = Depends(get_current_active_user),
    education_engine: ClinicalEducationEngine = Depends(lambda: clinical_education_engine)
) -> List[Dict[str, Any]]:
    """Get personalized learning recommendations for a user.

    Args:
        analysis_findings: Optional JSON string of analysis findings
        current_user: Current authenticated user
        education_engine: Education engine instance

    Returns:
        List of recommended educational content
    """
    try:
        # Parse analysis findings if provided
        findings = None
        if analysis_findings:
            import json
            findings = json.loads(analysis_findings)

        # Get recommendations
        recommendations = await education_engine.get_learning_recommendations(
            user_id=current_user.id,
            analysis_findings=findings
        )

        # Convert to response format
        response = []
        for content in recommendations:
            response.append({
                "content_id": content.content_id,
                "title": content.title,
                "content_type": content.content_type.value,
                "duration_minutes": content.duration_minutes,
                "difficulty_level": content.difficulty_level.value,
                "tags": content.tags,
                "author": content.author
            })

        logger.info("Generated %d learning recommendations for user %d",
                   len(recommendations), current_user.id)

        return response

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format for analysis_findings"
        )
    except Exception as e:
        logger.exception("Failed to get learning recommendations: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.get("/dashboard", response_model=LearningDashboardResponse)
async def get_learning_dashboard(
    current_user: models.User = Depends(get_current_active_user),
    education_engine: ClinicalEducationEngine = Depends(lambda: clinical_education_engine)
) -> LearningDashboardResponse:
    """Get comprehensive learning dashboard for a user.

    Args:
        current_user: Current authenticated user
        education_engine: Education engine instance

    Returns:
        Learning dashboard data
    """
    try:
        dashboard_data = await education_engine.get_user_learning_dashboard(current_user.id)

        if 'error' in dashboard_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=dashboard_data['error']
            )

        return LearningDashboardResponse(**dashboard_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get learning dashboard: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}"
        )


@router.get("/content")
async def get_educational_content(
    competency_area: Optional[str] = None,
    content_type: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    education_engine: ClinicalEducationEngine = Depends(lambda: clinical_education_engine)
) -> List[Dict[str, Any]]:
    """Get educational content with optional filters.

    Args:
        competency_area: Filter by competency area
        content_type: Filter by content type
        difficulty_level: Filter by difficulty level
        education_engine: Education engine instance

    Returns:
        List of educational content
    """
    try:
        content_items = list(education_engine.educational_content.values())

        # Apply filters
        if competency_area:
            try:
                competency = CompetencyArea(competency_area)
                content_items = [
                    content for content in content_items
                    if any(obj.competency_area == competency
                          for obj in education_engine.learning_objectives.values()
                          if obj.objective_id == content.learning_objective_id)
                ]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid competency area: {competency_area}"
                )

        if content_type:
            try:
                content_type_enum = ContentType(content_type)
                content_items = [
                    content for content in content_items
                    if content.content_type == content_type_enum
                ]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid content type: {content_type}"
                )

        if difficulty_level:
            try:
                difficulty = LearningLevel(difficulty_level)
                content_items = [
                    content for content in content_items
                    if content.difficulty_level == difficulty
                ]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid difficulty level: {difficulty_level}"
                )

        # Convert to response format
        response = []
        for content in content_items:
            response.append({
                "content_id": content.content_id,
                "title": content.title,
                "content_type": content.content_type.value,
                "duration_minutes": content.duration_minutes,
                "difficulty_level": content.difficulty_level.value,
                "tags": content.tags,
                "author": content.author,
                "last_updated": content.last_updated.isoformat()
            })

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get educational content: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content: {str(e)}"
        )


@router.get("/stats")
async def get_education_stats(
    education_engine: ClinicalEducationEngine = Depends(lambda: clinical_education_engine)
) -> Dict[str, Any]:
    """Get overall education system statistics.

    Args:
        education_engine: Education engine instance

    Returns:
        Education system statistics
    """
    try:
        stats = await education_engine.get_education_stats()
        return stats

    except Exception as e:
        logger.exception("Failed to get education stats: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get("/competency-areas")
async def get_competency_areas() -> List[Dict[str, str]]:
    """Get available competency areas.

    Returns:
        List of competency areas
    """
    return [
        {"value": area.value, "label": area.value.replace("_", " ").title()}
        for area in CompetencyArea
    ]


@router.get("/content-types")
async def get_content_types() -> List[Dict[str, str]]:
    """Get available content types.

    Returns:
        List of content types
    """
    return [
        {"value": content_type.value, "label": content_type.value.replace("_", " ").title()}
        for content_type in ContentType
    ]


@router.get("/learning-levels")
async def get_learning_levels() -> List[Dict[str, str]]:
    """Get available learning levels.

    Returns:
        List of learning levels
    """
    return [
        {"value": level.value, "label": level.value.title()}
        for level in LearningLevel
    ]
