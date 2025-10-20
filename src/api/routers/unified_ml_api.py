"""API Integration Module for Clinical Compliance Analysis.

This module provides comprehensive API integration that connects all ML components,
security middleware, caching, and utilities using expert patterns and best practices.

Features:
- Unified API endpoints for all ML functionality
- Comprehensive security integration
- Integrated caching and performance monitoring
- Type-safe API operations
- Comprehensive error handling and logging
- Audit trail integration
- Real-time metrics and health monitoring
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uuid

from src.core.unified_ml_system import (
    UnifiedMLSystem, MLRequest, MLResponse, ml_container, unified_ml_system
)
from src.core.centralized_logging import (
    get_logger, log_async_function_call, audit_logger, performance_tracker
)
from src.core.shared_utils import (
    data_validator, file_utils, text_utils, security_utils
)
from src.core.multi_tier_cache import MultiTierCacheSystem
from src.core.advanced_security_system import AdvancedSecuritySystem
from src.core.human_feedback_system import HumanFeedbackSystem
from src.core.clinical_education_engine import ClinicalEducationEngine
from src.api.middleware.security_middleware import SecurityMiddleware

# Initialize logger
logger = get_logger(__name__)

# Security
security = HTTPBearer()

# API Router
router = APIRouter(prefix="/api/v2", tags=["Unified ML API"])


# Pydantic Models for API
class DocumentAnalysisRequest(BaseModel):
    """Request model for document analysis."""
    document_text: str = Field(..., min_length=1, max_length=100000, description="Document text to analyze")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="Pre-extracted entities")
    retrieved_rules: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved compliance rules")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    priority: str = Field(default="normal", description="Processing priority")
    timeout_seconds: float = Field(default=30.0, ge=1.0, le=300.0, description="Request timeout")
    explanation_types: Optional[List[str]] = Field(None, description="Types of explanations to generate")


class DocumentAnalysisResponse(BaseModel):
    """Response model for document analysis."""
    request_id: str
    analysis_result: Dict[str, Any]
    confidence_metrics: Optional[Dict[str, Any]] = None
    ensemble_result: Optional[Dict[str, Any]] = None
    bias_metrics: Optional[Dict[str, Any]] = None
    explanation_result: Optional[Dict[str, Any]] = None
    processing_time_ms: float
    cache_hit: bool = False
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    timestamp: datetime


class SystemHealthResponse(BaseModel):
    """System health response model."""
    overall_status: str
    components: Dict[str, Any]
    metrics: Dict[str, Any]
    circuit_breakers: Dict[str, Any]
    performance: Dict[str, Any]
    timestamp: datetime


class CacheStatsResponse(BaseModel):
    """Cache statistics response model."""
    hits: int
    misses: int
    hit_rate: float
    total_size_bytes: int
    tier_distribution: Dict[str, int]
    operations: int
    evictions: int


class FeedbackSubmissionRequest(BaseModel):
    """Request model for feedback submission."""
    analysis_id: str = Field(..., description="ID of the analysis being feedback on")
    finding_id: Optional[str] = Field(None, description="Specific finding ID")
    feedback_type: str = Field(..., description="Type of feedback")
    content: str = Field(..., min_length=1, max_length=5000, description="Feedback content")
    confidence_rating: Optional[float] = Field(None, ge=0.0, le=1.0, description="User confidence in feedback")
    priority: str = Field(default="medium", description="Feedback priority")


class LearningPathRequest(BaseModel):
    """Request model for learning path creation."""
    competency_focus: str = Field(..., description="Primary competency area")
    learning_level: str = Field(..., description="User's learning level")
    analysis_findings: Optional[List[Dict[str, Any]]] = Field(None, description="Recent analysis findings")


# Dependency injection functions
async def get_ml_system() -> UnifiedMLSystem:
    """Get ML system instance."""
    return unified_ml_system


async def get_cache_system() -> MultiTierCacheSystem:
    """Get cache system instance."""
    return ml_container.get('cache_system')


async def get_security_system() -> AdvancedSecuritySystem:
    """Get security system instance."""
    return ml_container.get('security_system')


async def get_feedback_system() -> HumanFeedbackSystem:
    """Get feedback system instance."""
    return HumanFeedbackSystem()


async def get_education_engine() -> ClinicalEducationEngine:
    """Get education engine instance."""
    return ClinicalEducationEngine()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user."""
    # This would integrate with your existing auth system
    # For now, return a mock user
    return {
        "user_id": 1,
        "username": "test_user",
        "is_active": True,
        "permissions": ["read", "write"]
    }


# API Endpoints
@router.post("/analyze/document", response_model=DocumentAnalysisResponse)
@log_async_function_call(logger, include_timing=True)
async def analyze_document(
    request: DocumentAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_system: UnifiedMLSystem = Depends(get_ml_system)
) -> DocumentAnalysisResponse:
    """Comprehensive document analysis with full ML pipeline."""

    try:
        # Validate request
        validation_result = data_validator.validate_json(request.model_dump_json())
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request: {validation_result.errors}"
            )

        # Create ML request
        ml_request = MLRequest(
            document_text=text_utils.sanitize_text(request.document_text),
            entities=request.entities,
            retrieved_rules=request.retrieved_rules,
            context={
                **request.context,
                "user_id": current_user["user_id"],
                "session_id": str(uuid.uuid4())
            },
            user_id=current_user["user_id"],
            session_id=str(uuid.uuid4()),
            priority=request.priority,
            timeout_seconds=request.timeout_seconds
        )

        # Convert explanation types
        explanation_types = None
        if request.explanation_types:
            from src.core.unified_explanation_engine import ExplanationType
            explanation_types = [ExplanationType(t) for t in request.explanation_types]

        # Perform analysis
        ml_response = await ml_system.analyze_document(ml_request, explanation_types)

        # Log audit event
        audit_logger.log_user_action(
            user_id=current_user["user_id"],
            action="document_analysis",
            resource=f"document_{ml_request.request_id}",
            details={
                "document_length": len(request.document_text),
                "entities_count": len(request.entities),
                "processing_time_ms": ml_response.processing_time_ms,
                "cache_hit": ml_response.cache_hit
            },
            success=len(ml_response.errors) == 0
        )

        # Convert to response model
        return DocumentAnalysisResponse(
            request_id=ml_response.request_id,
            analysis_result=ml_response.analysis_result,
            confidence_metrics=ml_response.confidence_metrics.__dict__ if ml_response.confidence_metrics else None,
            ensemble_result=ml_response.ensemble_result.__dict__ if ml_response.ensemble_result else None,
            bias_metrics=ml_response.bias_metrics,
            explanation_result=ml_response.explanation_result,
            processing_time_ms=ml_response.processing_time_ms,
            cache_hit=ml_response.cache_hit,
            errors=ml_response.errors,
            warnings=ml_response.warnings,
            timestamp=ml_response.timestamp
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Document analysis failed: %s", e)
        audit_logger.log_user_action(
            user_id=current_user["user_id"],
            action="document_analysis",
            resource="unknown",
            details={"error": str(e)},
            success=False
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document analysis failed"
        )


@router.get("/system/health", response_model=SystemHealthResponse)
@log_async_function_call(logger)
async def get_system_health(
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_system: UnifiedMLSystem = Depends(get_ml_system)
) -> SystemHealthResponse:
    """Get comprehensive system health status."""

    try:
        health_data = ml_system.get_system_health()

        return SystemHealthResponse(
            overall_status=health_data["overall_status"],
            components=health_data["components"],
            metrics=health_data["metrics"],
            circuit_breakers=health_data["circuit_breakers"],
            performance=health_data["performance"],
            timestamp=datetime.now(timezone.utc)
        )

    except Exception as e:
        logger.exception("Failed to get system health: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system health"
        )


@router.get("/cache/stats", response_model=CacheStatsResponse)
@log_async_function_call(logger)
async def get_cache_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    cache_system: MultiTierCacheSystem = Depends(get_cache_system)
) -> CacheStatsResponse:
    """Get cache system statistics."""

    try:
        stats = await cache_system.get_stats()

        return CacheStatsResponse(
            hits=stats.hits,
            misses=stats.misses,
            hit_rate=stats.hit_rate,
            total_size_bytes=stats.total_size_bytes,
            tier_distribution=stats.tier_distribution,
            operations=stats.operations,
            evictions=stats.evictions
        )

    except Exception as e:
        logger.exception("Failed to get cache stats: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache statistics"
        )


@router.post("/cache/clear")
@log_async_function_call(logger)
async def clear_cache(
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_system: UnifiedMLSystem = Depends(get_ml_system)
) -> Dict[str, Any]:
    """Clear all cached results."""

    try:
        cleared_count = await ml_system.clear_cache()

        audit_logger.log_user_action(
            user_id=current_user["user_id"],
            action="cache_clear",
            resource="all_cache",
            details={"cleared_entries": cleared_count},
            success=True
        )

        return {
            "message": "Cache cleared successfully",
            "cleared_entries": cleared_count,
            "timestamp": datetime.now(timezone.utc)
        }

    except Exception as e:
        logger.exception("Failed to clear cache: %s", e)
        audit_logger.log_user_action(
            user_id=current_user["user_id"],
            action="cache_clear",
            resource="all_cache",
            details={"error": str(e)},
            success=False
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )


@router.post("/feedback/submit")
@log_async_function_call(logger)
async def submit_feedback(
    request: FeedbackSubmissionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    feedback_system: HumanFeedbackSystem = Depends(get_feedback_system)
) -> Dict[str, Any]:
    """Submit human feedback for analysis improvement."""

    try:
        # Submit feedback
        feedback_id = await feedback_system.submit_feedback(
            user_id=current_user["user_id"],
            analysis_id=request.analysis_id,
            finding_id=request.finding_id,
            feedback_type=request.feedback_type,
            content=text_utils.sanitize_text(request.content),
            confidence_rating=request.confidence_rating,
            priority=request.priority
        )

        audit_logger.log_user_action(
            user_id=current_user["user_id"],
            action="feedback_submit",
            resource=f"analysis_{request.analysis_id}",
            details={
                "feedback_id": feedback_id,
                "feedback_type": request.feedback_type,
                "priority": request.priority
            },
            success=True
        )

        return {
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_id,
            "timestamp": datetime.now(timezone.utc)
        }

    except Exception as e:
        logger.exception("Failed to submit feedback: %s", e)
        audit_logger.log_user_action(
            user_id=current_user["user_id"],
            action="feedback_submit",
            resource=f"analysis_{request.analysis_id}",
            details={"error": str(e)},
            success=False
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


@router.post("/education/learning-path")
@log_async_function_call(logger)
async def create_learning_path(
    request: LearningPathRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    education_engine: ClinicalEducationEngine = Depends(get_education_engine)
) -> Dict[str, Any]:
    """Create personalized learning path."""

    try:
        # Create learning path
        learning_path = await education_engine.create_learning_path(
            user_id=current_user["user_id"],
            competency_focus=request.competency_focus,
            learning_level=request.learning_level,
            analysis_findings=request.analysis_findings
        )

        audit_logger.log_user_action(
            user_id=current_user["user_id"],
            action="learning_path_create",
            resource=f"learning_path_{learning_path.path_id}",
            details={
                "competency_focus": request.competency_focus,
                "learning_level": request.learning_level,
                "objectives_count": len(learning_path.objectives)
            },
            success=True
        )

        return {
            "message": "Learning path created successfully",
            "learning_path_id": learning_path.path_id,
            "title": learning_path.title,
            "estimated_completion_hours": learning_path.estimated_completion_hours,
            "timestamp": datetime.now(timezone.utc)
        }

    except Exception as e:
        logger.exception("Failed to create learning path: %s", e)
        audit_logger.log_user_action(
            user_id=current_user["user_id"],
            action="learning_path_create",
            resource="unknown",
            details={"error": str(e)},
            success=False
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create learning path"
        )


@router.get("/performance/metrics")
@log_async_function_call(logger)
async def get_performance_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive performance metrics."""

    try:
        # Get performance statistics
        performance_stats = performance_tracker.get_all_statistics()

        # Get audit trail summary
        recent_audit = audit_logger.get_audit_trail(
            start_time=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        )

        return {
            "performance_statistics": performance_stats,
            "audit_summary": {
                "total_events_today": len(recent_audit),
                "user_actions": len([e for e in recent_audit if "user_id" in e]),
                "system_events": len([e for e in recent_audit if "event_type" in e])
            },
            "timestamp": datetime.now(timezone.utc)
        }

    except Exception as e:
        logger.exception("Failed to get performance metrics: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance metrics"
        )


@router.get("/audit/trail")
@log_async_function_call(logger)
async def get_audit_trail(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    user_id: Optional[int] = None,
    event_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get filtered audit trail."""

    try:
        # Check permissions (admin only for audit trail)
        if "admin" not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access audit trail"
            )

        audit_trail = audit_logger.get_audit_trail(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
            event_type=event_type
        )

        return {
            "audit_trail": audit_trail,
            "total_events": len(audit_trail),
            "filters": {
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "user_id": user_id,
                "event_type": event_type
            },
            "timestamp": datetime.now(timezone.utc)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get audit trail: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit trail"
        )


@router.post("/system/reset-metrics")
@log_async_function_call(logger)
async def reset_system_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user),
    ml_system: UnifiedMLSystem = Depends(get_ml_system)
) -> Dict[str, Any]:
    """Reset system metrics (admin only)."""

    try:
        # Check permissions (admin only)
        if "admin" not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to reset metrics"
            )

        ml_system.reset_metrics()

        audit_logger.log_user_action(
            user_id=current_user["user_id"],
            action="metrics_reset",
            resource="system_metrics",
            details={},
            success=True
        )

        return {
            "message": "System metrics reset successfully",
            "timestamp": datetime.now(timezone.utc)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to reset metrics: %s", e)
        audit_logger.log_user_action(
            user_id=current_user["user_id"],
            action="metrics_reset",
            resource="system_metrics",
            details={"error": str(e)},
            success=False
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset metrics"
        )


# Health check endpoint
@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "version": "2.0.0"
    }
