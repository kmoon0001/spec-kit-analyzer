"""Authentication API router for user registration, login, and password management.

Provides endpoints for JWT token generation, user registration, and password updates.
"""

import logging
from datetime import timedelta

import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import AuthService, get_auth_service, get_current_active_user
from ...config import get_settings
from ...core.enhanced_session_manager import get_session_manager
from ...core.security_validator import SecurityValidator
from ...database import crud, get_async_db, models, schemas
from ..error_handling import (
    AuthenticationError,
    AuthorizationError,
    ErrorCode,
    ValidationError,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])
settings = get_settings()


async def _authenticate_user(
    form_data: OAuth2PasswordRequestForm,
    db: AsyncSession,
    auth_service: AuthService,
    request: Request = None,
) -> dict[str, str]:
    """Validate credentials and issue an access token with session creation."""
    is_valid, error_msg = SecurityValidator.validate_username(form_data.username)
    if not is_valid:
        raise ValidationError(ErrorCode.VALIDATION_INVALID_INPUT, error_msg)

    user = await crud.get_user_by_username(db, username=form_data.username)
    if not user or not auth_service.verify_password(
        form_data.password, user.hashed_password
    ):
        raise AuthenticationError(
            ErrorCode.AUTH_INVALID_CREDENTIALS, "Incorrect username or password"
        )

    if not user.is_active:
        raise AuthorizationError(
            ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            "Account is inactive or license has expired. Please contact support.",
        )

    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Create session if request context is available
    if request:
        session_manager = get_session_manager()
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        session_id = session_manager.create_session(
            user_id=user.id,
            username=user.username,
            ip_address=ip_address,
            user_agent=user_agent,
            login_method="password"
        )

        logger.info(
            f"User {user.username} logged in successfully",
            extra={
                "user_id": user.id,
                "session_id": session_id,
                "client_ip": ip_address,
            },
        )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=schemas.User
)
async def register_user(
    user_data: schemas.UserCreate,
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> schemas.User:
    """Register a new user and return basic user info."""
    # Validate username
    is_valid, error_msg = SecurityValidator.validate_username(user_data.username)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # Validate password strength
    is_valid, error_msg = SecurityValidator.validate_password_strength(
        user_data.password
    )
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    hashed_password = auth_service.get_password_hash(user_data.password)
    try:
        created_user = await crud.create_user(db, user_data, hashed_password)
    except sqlalchemy.exc.IntegrityError as exc:
        if "UNIQUE constraint failed: users.username" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
            ) from exc
        raise HTTPException(status_code=400, detail="Registration failed") from exc
    except (
        Exception
    ) as exc:  # pragma: no cover - errors handled by global exception handler in practice
        logger.exception("User registration failed: %s", exc)
        raise HTTPException(status_code=400, detail="Registration failed") from exc

    logger.info(
        f"User registered successfully: {user_data.username}", user_id=created_user.id
    )
    return schemas.User.model_validate(created_user)


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service),
    request: Request = None,
) -> dict[str, str]:
    """Authenticate user and generate JWT access token (OAuth2 compatible) with session creation."""
    return await _authenticate_user(
        form_data=form_data, db=db, auth_service=auth_service, request=request
    )


# REMOVED: Legacy /login endpoint - redundant with OAuth2 /token endpoint
# The legacy login endpoint has been removed to standardize on OAuth2
# authentication flow. Use /token endpoint instead.


@router.post("/users/change-password")
async def change_password(
    password_data: schemas.UserPasswordChange,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Change password for the current user."""
    if not password_data.new_password:
        raise HTTPException(status_code=400, detail="New password required")

    # Validate new password strength
    is_valid, error_msg = SecurityValidator.validate_password_strength(
        password_data.new_password
    )
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # Verify current password
    if not auth_service.verify_password(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Hash new password
    new_hash = auth_service.get_password_hash(password_data.new_password)

    # Update password in database
    await crud.change_user_password(db, current_user, new_hash)

    # Invalidate all existing sessions for security
    session_manager = get_session_manager()
    invalidated_count = session_manager.invalidate_password_change_sessions(
        current_user.id
    )

    logger.info(
        f"Password changed for user {current_user.username}",
        user_id=current_user.id,
        sessions_invalidated=invalidated_count,
    )

    return {"status": "ok", "sessions_invalidated": invalidated_count}
