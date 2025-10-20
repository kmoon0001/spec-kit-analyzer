"""Security API Router for Clinical Compliance Analysis API.

This module provides security-related API endpoints.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.config.security_config import get_security_config
from src.api.utils.security_utils import generate_secure_token, validate_password_strength
from src.core.advanced_security_system import security_system, SecurityLevel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["Security"])


class SecurityStatusResponse(BaseModel):
    """Security status response."""
    status: str = Field(..., description="Security status")
    threats_detected: int = Field(..., description="Number of threats detected")
    blocked_ips: int = Field(..., description="Number of blocked IPs")
    security_events: int = Field(..., description="Number of security events")
    last_updated: datetime = Field(..., description="Last update timestamp")


class ThreatDetectionRequest(BaseModel):
    """Threat detection request."""
    data: dict = Field(..., description="Data to analyze for threats")
    sensitivity: str = Field(default="medium", description="Detection sensitivity")


class ThreatDetectionResponse(BaseModel):
    """Threat detection response."""
    threats_detected: list[str] = Field(..., description="Detected threats")
    risk_level: str = Field(..., description="Risk level")
    recommendations: list[str] = Field(..., description="Security recommendations")


class PasswordStrengthRequest(BaseModel):
    """Password strength validation request."""
    password: str = Field(..., description="Password to validate")


class PasswordStrengthResponse(BaseModel):
    """Password strength validation response."""
    is_strong: bool = Field(..., description="Whether password is strong")
    errors: list[str] = Field(..., description="Password strength errors")
    score: int = Field(..., description="Password strength score (0-100)")


class SecurityEventRequest(BaseModel):
    """Security event logging request."""
    event_type: str = Field(..., description="Type of security event")
    severity: str = Field(..., description="Event severity")
    description: str = Field(..., description="Event description")
    details: Optional[dict] = Field(default=None, description="Additional event details")


@router.get("/status", response_model=SecurityStatusResponse)
async def get_security_status():
    """Get current security status."""
    try:
        # Get security metrics
        threats_detected = security_system.get_threat_count()
        blocked_ips = security_system.get_blocked_ip_count()
        security_events = security_system.get_security_event_count()

        return SecurityStatusResponse(
            status="active",
            threats_detected=threats_detected,
            blocked_ips=blocked_ips,
            security_events=security_events,
            last_updated=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Failed to get security status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security status"
        )


@router.post("/threat-detection", response_model=ThreatDetectionResponse)
async def detect_threats(request: ThreatDetectionRequest):
    """Detect threats in provided data."""
    try:
        # Detect threats
        threats = security_system.detect_threats(request.data)

        # Determine risk level
        risk_level = "low"
        if len(threats) > 2:
            risk_level = "high"
        elif len(threats) > 0:
            risk_level = "medium"

        # Generate recommendations
        recommendations = []
        if threats:
            recommendations.append("Review input data for suspicious patterns")
            recommendations.append("Consider implementing additional validation")
            recommendations.append("Monitor for similar patterns in the future")

        return ThreatDetectionResponse(
            threats_detected=[t.value for t in threats],
            risk_level=risk_level,
            recommendations=recommendations
        )
    except Exception as e:
        logger.error(f"Failed to detect threats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect threats"
        )


@router.post("/password-strength", response_model=PasswordStrengthResponse)
async def validate_password_strength_endpoint(request: PasswordStrengthRequest):
    """Validate password strength."""
    try:
        is_strong, errors = validate_password_strength(request.password)

        # Calculate strength score
        score = 0
        if len(request.password) >= 8:
            score += 20
        if len(request.password) >= 12:
            score += 20
        if any(c.isupper() for c in request.password):
            score += 20
        if any(c.islower() for c in request.password):
            score += 20
        if any(c.isdigit() for c in request.password):
            score += 20

        return PasswordStrengthResponse(
            is_strong=is_strong,
            errors=errors,
            score=score
        )
    except Exception as e:
        logger.error(f"Failed to validate password strength: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate password strength"
        )


@router.post("/log-event")
async def log_security_event(request: SecurityEventRequest):
    """Log a security event."""
    try:
        # Convert severity string to enum
        severity_map = {
            "low": SecurityLevel.LOW,
            "medium": SecurityLevel.MEDIUM,
            "high": SecurityLevel.HIGH,
            "critical": SecurityLevel.CRITICAL
        }
        severity = severity_map.get(request.severity.lower(), SecurityLevel.MEDIUM)

        # Log the event
        security_system.log_security_event(
            event_type=request.event_type,
            severity=severity,
            description=request.description,
            details=request.details
        )

        return {"status": "success", "message": "Security event logged"}
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log security event"
        )


@router.get("/config")
async def get_security_config_endpoint():
    """Get security configuration."""
    try:
        config = get_security_config()
        return {
            "password_min_length": config.password_min_length,
            "rate_limit_requests_per_minute": config.rate_limit_requests_per_minute,
            "enable_threat_detection": config.enable_threat_detection,
            "enable_data_encryption": config.enable_data_encryption,
            "enable_phi_detection": config.enable_phi_detection
        }
    except Exception as e:
        logger.error(f"Failed to get security config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security configuration"
        )


@router.post("/generate-token")
async def generate_security_token():
    """Generate a secure token."""
    try:
        token = generate_secure_token()
        return {"token": token, "expires_at": datetime.utcnow() + timedelta(hours=1)}
    except Exception as e:
        logger.error(f"Failed to generate security token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate security token"
        )
