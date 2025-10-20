"""API endpoints for Human-in-the-Loop Feedback System.

This module provides REST API endpoints for submitting, retrieving, and
managing feedback on AI analysis results.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.dependencies import get_current_active_user
from src.core.human_feedback_system import (
    HumanFeedbackSystem,
    FeedbackType,
    FeedbackPriority,
    FeedbackItem,
    human_feedback_system
)
from src import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


# Pydantic models for API
class FeedbackSubmissionRequest(BaseModel):
    """Request model for submitting feedback."""
    analysis_id: str = Field(..., description="ID of the analysis being feedback on")
    feedback_type: str = Field(..., description="Type of feedback")
    content: str = Field(..., description="Feedback content")
    finding_id: Optional[str] = Field(None, description="Specific finding ID")
    original_finding: Optional[Dict[str, Any]] = Field(None, description="Original AI finding")
    suggested_correction: Optional[Dict[str, Any]] = Field(None, description="Suggested correction")
    confidence_rating: Optional[float] = Field(None, ge=0.0, le=1.0, description="User's confidence in feedback")
    priority: str = Field("medium", description="Priority level")


class FeedbackResponse(BaseModel):
    """Response model for feedback operations."""
    feedback_id: str
    status: str
    message: str
    timestamp: datetime


class FeedbackItemResponse(BaseModel):
    """Response model for individual feedback items."""
    feedback_id: str
    analysis_id: str
    finding_id: Optional[str]
    feedback_type: str
    priority: str
    content: str
    original_finding: Optional[Dict[str, Any]]
    suggested_correction: Optional[Dict[str, Any]]
    confidence_rating: Optional[float]
    timestamp: datetime
    status: str
    processed_by: Optional[str]
    processing_notes: Optional[str]
    impact_score: float


class FeedbackAnalyticsResponse(BaseModel):
    """Response model for feedback analytics."""
    date_range: Dict[str, str]
    total_feedback: int
    feedback_by_type: Dict[str, int]
    feedback_by_priority: Dict[str, int]
    average_confidence: float
    average_impact_score: float
    processing_stats: Dict[str, int]
    top_issues: List[str]
    user_engagement: Dict[str, int]


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackSubmissionRequest,
    current_user: models.User = Depends(get_current_active_user),
    feedback_system: HumanFeedbackSystem = Depends(lambda: human_feedback_system)
) -> FeedbackResponse:
    """Submit feedback for an analysis.

    Args:
        request: Feedback submission request
        current_user: Current authenticated user
        feedback_system: Feedback system instance

    Returns:
        Feedback submission response
    """
    try:
        # Validate feedback type
        try:
            feedback_type = FeedbackType(request.feedback_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid feedback type: {request.feedback_type}"
            )

        # Validate priority
        try:
            priority = FeedbackPriority(request.priority)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {request.priority}"
            )

        # Submit feedback
        feedback_id = await feedback_system.submit_feedback(
            user_id=current_user.id,
            analysis_id=request.analysis_id,
            feedback_type=feedback_type,
            content=request.content,
            finding_id=request.finding_id,
            original_finding=request.original_finding,
            suggested_correction=request.suggested_correction,
            confidence_rating=request.confidence_rating,
            priority=priority
        )

        logger.info("Feedback submitted by user %d: %s", current_user.id, feedback_id)

        return FeedbackResponse(
            feedback_id=feedback_id,
            status="submitted",
            message="Feedback submitted successfully",
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.exception("Failed to submit feedback: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/analysis/{analysis_id}", response_model=List[FeedbackItemResponse])
async def get_feedback_for_analysis(
    analysis_id: str,
    current_user: models.User = Depends(get_current_active_user),
    feedback_system: HumanFeedbackSystem = Depends(lambda: human_feedback_system)
) -> List[FeedbackItemResponse]:
    """Get all feedback for a specific analysis.

    Args:
        analysis_id: Analysis ID
        current_user: Current authenticated user
        feedback_system: Feedback system instance

    Returns:
        List of feedback items
    """
    try:
        feedback_items = await feedback_system.get_feedback_for_analysis(
            analysis_id=analysis_id,
            user_id=current_user.id
        )

        return [
            FeedbackItemResponse(
                feedback_id=item.feedback_id,
                analysis_id=item.analysis_id,
                finding_id=item.finding_id,
                feedback_type=item.feedback_type.value,
                priority=item.priority.value,
                content=item.content,
                original_finding=item.original_finding,
                suggested_correction=item.suggested_correction,
                confidence_rating=item.confidence_rating,
                timestamp=item.timestamp,
                status=item.status.value,
                processed_by=item.processed_by,
                processing_notes=item.processing_notes,
                impact_score=item.impact_score
            )
            for item in feedback_items
        ]

    except Exception as e:
        logger.exception("Failed to get feedback for analysis %s: %s", analysis_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback: {str(e)}"
        )


@router.post("/process/{feedback_id}", response_model=FeedbackResponse)
async def process_feedback(
    feedback_id: str,
    processing_notes: Optional[str] = None,
    current_user: models.User = Depends(get_current_active_user),
    feedback_system: HumanFeedbackSystem = Depends(lambda: human_feedback_system)
) -> FeedbackResponse:
    """Process a specific feedback item.

    Args:
        feedback_id: Feedback ID to process
        processing_notes: Optional processing notes
        current_user: Current authenticated user
        feedback_system: Feedback system instance

    Returns:
        Processing response
    """
    try:
        success = await feedback_system.process_feedback_item(
            feedback_id=feedback_id,
            processor_id=str(current_user.id),
            processing_notes=processing_notes
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback item not found or could not be processed: {feedback_id}"
            )

        logger.info("Feedback processed by user %d: %s", current_user.id, feedback_id)

        return FeedbackResponse(
            feedback_id=feedback_id,
            status="processed",
            message="Feedback processed successfully",
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to process feedback %s: %s", feedback_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process feedback: {str(e)}"
        )


@router.get("/analytics", response_model=FeedbackAnalyticsResponse)
async def get_feedback_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: models.User = Depends(get_current_active_user),
    feedback_system: HumanFeedbackSystem = Depends(lambda: human_feedback_system)
) -> FeedbackAnalyticsResponse:
    """Get feedback analytics for a date range.

    Args:
        start_date: Start date in ISO format
        end_date: End date in ISO format
        current_user: Current authenticated user
        feedback_system: Feedback system instance

    Returns:
        Feedback analytics data
    """
    try:
        # Parse dates
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Get analytics
        analytics = await feedback_system.get_feedback_analytics(
            start_date=start_dt,
            end_date=end_dt
        )

        return FeedbackAnalyticsResponse(**analytics)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.exception("Failed to get feedback analytics: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


@router.get("/stats")
async def get_feedback_stats(
    current_user: models.User = Depends(get_current_active_user),
    feedback_system: HumanFeedbackSystem = Depends(lambda: human_feedback_system)
) -> Dict[str, Any]:
    """Get current feedback statistics.

    Args:
        current_user: Current authenticated user
        feedback_system: Feedback system instance

    Returns:
        Feedback statistics
    """
    try:
        stats = feedback_system.get_feedback_stats()
        return stats

    except Exception as e:
        logger.exception("Failed to get feedback stats: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_old_feedback(
    current_user: models.User = Depends(get_current_active_user),
    feedback_system: HumanFeedbackSystem = Depends(lambda: human_feedback_system)
) -> Dict[str, Any]:
    """Clean up old feedback data.

    Args:
        current_user: Current authenticated user
        feedback_system: Feedback system instance

    Returns:
        Cleanup results
    """
    try:
        removed_count = await feedback_system.cleanup_old_feedback()

        logger.info("Feedback cleanup completed by user %d: %d items removed",
                   current_user.id, removed_count)

        return {
            "removed_count": removed_count,
            "message": f"Cleaned up {removed_count} old feedback items",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.exception("Failed to cleanup feedback: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup feedback: {str(e)}"
        )


@router.get("/types")
async def get_feedback_types() -> Dict[str, List[str]]:
    """Get available feedback types and priorities.

    Returns:
        Available feedback types and priorities
    """
    return {
        "feedback_types": [ft.value for ft in FeedbackType],
        "priorities": [fp.value for fp in FeedbackPriority]
    }