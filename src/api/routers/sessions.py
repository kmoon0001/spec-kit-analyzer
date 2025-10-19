"""Session management API endpoints.

This module provides endpoints for managing user sessions including
session creation, validation, refresh, and cleanup.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from src.auth import get_current_active_user
from src.core.session_manager import get_session_manager, get_session_security_validator
from src.database import models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionCreateRequest(BaseModel):
    """Request model for creating a session."""
    client_info: Dict[str, Any]


class SessionResponse(BaseModel):
    """Response model for session data."""
    session_id: str
    created_at: float
    last_activity: float
    expires_at: float
    client_info: Dict[str, Any]
    refresh_count: int


class SessionStatsResponse(BaseModel):
    """Response model for session statistics."""
    active_sessions: int
    total_sessions: int
    unique_users: int
    max_sessions_per_user: int
    session_timeout_minutes: int


@router.post("/create", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    current_user: models.User = Depends(get_current_active_user),
    http_request: Request = None,
) -> SessionResponse:
    """Create a new session for the current user."""
    session_manager = get_session_manager()
    
    # Extract client information from request
    client_info = {
        'ip': http_request.client.host if http_request.client else 'unknown',
        'user_agent': http_request.headers.get('user-agent', 'unknown'),
        'created_via': 'api',
        **request.client_info,
    }
    
    # Create session
    session_id = session_manager.create_session(current_user, client_info)
    session = session_manager.validate_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )
    
    logger.info(f"Session created for user {current_user.username}", extra={
        'session_id': session_id,
        'user_id': current_user.id,
        'client_ip': client_info['ip'],
    })
    
    return SessionResponse(
        session_id=session['session_id'],
        created_at=session['created_at'],
        last_activity=session['last_activity'],
        expires_at=session['expires_at'],
        client_info=session['client_info'],
        refresh_count=session['refresh_count'],
    )


@router.post("/refresh/{session_id}")
async def refresh_session(
    session_id: str,
    current_user: models.User = Depends(get_current_active_user),
    http_request: Request = None,
) -> Dict[str, Any]:
    """Refresh a session to extend its expiration."""
    session_manager = get_session_manager()
    security_validator = get_session_security_validator()
    
    # Extract client information
    client_info = {
        'ip': http_request.client.host if http_request.client else 'unknown',
        'user_agent': http_request.headers.get('user-agent', 'unknown'),
    }
    
    # Validate session security
    if not security_validator.validate_session_security(session_id, client_info):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session security validation failed"
        )
    
    # Refresh session
    refreshed_session_id = session_manager.refresh_session(session_id)
    
    if not refreshed_session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session refresh failed or session expired"
        )
    
    session = session_manager.validate_session(refreshed_session_id)
    
    logger.info(f"Session refreshed for user {current_user.username}", extra={
        'session_id': refreshed_session_id,
        'user_id': current_user.id,
    })
    
    return {
        'session_id': refreshed_session_id,
        'expires_at': session['expires_at'],
        'refresh_count': session['refresh_count'],
    }


@router.delete("/{session_id}")
async def invalidate_session(
    session_id: str,
    current_user: models.User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Invalidate a specific session."""
    session_manager = get_session_manager()
    
    # Check if user owns the session
    session = session_manager.validate_session(session_id)
    if not session or session['user_id'] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or not owned by user"
        )
    
    # Invalidate session
    success = session_manager.invalidate_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    logger.info(f"Session invalidated by user {current_user.username}", extra={
        'session_id': session_id,
        'user_id': current_user.id,
    })
    
    return {'message': 'Session invalidated successfully'}


@router.delete("/all")
async def invalidate_all_sessions(
    current_user: models.User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Invalidate all sessions for the current user."""
    session_manager = get_session_manager()
    
    # Invalidate all user sessions
    invalidated_count = session_manager.invalidate_user_sessions(current_user.id)
    
    logger.info(f"All sessions invalidated for user {current_user.username}", extra={
        'user_id': current_user.id,
        'invalidated_count': invalidated_count,
    })
    
    return {
        'message': f'Invalidated {invalidated_count} sessions',
        'invalidated_count': invalidated_count,
    }


@router.get("/my-sessions", response_model=List[SessionResponse])
async def get_my_sessions(
    current_user: models.User = Depends(get_current_active_user),
) -> List[SessionResponse]:
    """Get all active sessions for the current user."""
    session_manager = get_session_manager()
    
    sessions = session_manager.get_user_sessions(current_user.id)
    
    return [
        SessionResponse(
            session_id=session['session_id'],
            created_at=session['created_at'],
            last_activity=session['last_activity'],
            expires_at=session['expires_at'],
            client_info=session['client_info'],
            refresh_count=session['refresh_count'],
        )
        for session in sessions
    ]


@router.get("/stats", response_model=SessionStatsResponse)
async def get_session_stats(
    current_user: models.User = Depends(get_current_active_user),
) -> SessionStatsResponse:
    """Get session statistics (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    session_manager = get_session_manager()
    stats = session_manager.get_session_stats()
    
    return SessionStatsResponse(**stats)


@router.post("/validate/{session_id}")
async def validate_session(
    session_id: str,
    http_request: Request = None,
) -> Dict[str, Any]:
    """Validate a session (public endpoint for session validation)."""
    session_manager = get_session_manager()
    security_validator = get_session_security_validator()
    
    # Extract client information
    client_info = {
        'ip': http_request.client.host if http_request.client else 'unknown',
        'user_agent': http_request.headers.get('user-agent', 'unknown'),
    }
    
    # Validate session security
    if not security_validator.validate_session_security(session_id, client_info):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session validation failed"
        )
    
    session = session_manager.validate_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired"
        )
    
    return {
        'valid': True,
        'user_id': session['user_id'],
        'username': session['username'],
        'expires_at': session['expires_at'],
        'last_activity': session['last_activity'],
    }
