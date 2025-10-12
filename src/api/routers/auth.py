"""Authentication API router for user registration, login, and password management.

Provides endpoints for JWT token generation, user registration, and password updates.
"""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import AuthService, get_auth_service, get_current_active_user
from ...config import get_settings
from ...core.security_validator import SecurityValidator
from ...database import crud, models, schemas
from ...database import get_async_db as get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])
settings = get_settings()


async def _authenticate_user(
    form_data: OAuth2PasswordRequestForm,
    db: AsyncSession,
    auth_service: AuthService,
) -> dict[str, str]:
    """Validate credentials and issue an access token."""
    is_valid, error_msg = SecurityValidator.validate_username(form_data.username)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    user = await crud.get_user_by_username(db, username=form_data.username)
    if not user or not auth_service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or license has expired. Please contact support.",
        )

    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=schemas.User)
async def register_user(
    user_data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> schemas.User:
    """Register a new user account with validation safeguards."""
    is_valid, error_msg = SecurityValidator.validate_username(user_data.username)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    if not getattr(settings, "testing", False):
        is_valid, error_msg = SecurityValidator.validate_password_strength(user_data.password)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    normalized_username = user_data.username.strip().lower()
    existing_user = await crud.get_user_by_username(db, normalized_username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists.")

    hashed_password = auth_service.get_password_hash(user_data.password)
    normalized_payload = schemas.UserCreate(
        username=normalized_username,
        password=user_data.password,
        is_admin=user_data.is_admin,
        license_key=user_data.license_key,
    )
    created_user = await crud.create_user(db=db, user=normalized_payload, hashed_password=hashed_password)
    logger.info("Registered new user: %s", normalized_username)
    return schemas.User.model_validate(created_user)


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Authenticate user and generate JWT access token (OAuth2 compatible)."""
    return await _authenticate_user(form_data=form_data, db=db, auth_service=auth_service)


@router.post("/login", response_model=schemas.Token)
async def login_legacy_endpoint(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Legacy login endpoint retained for backward compatibility with existing clients."""
    return await _authenticate_user(form_data=form_data, db=db, auth_service=auth_service)


@router.post("/users/change-password")
async def change_password(
    password_data: schemas.UserPasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Change user password with validation."""
    if not auth_service.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password.")

    if not getattr(settings, "testing", False):
        is_valid, error_msg = SecurityValidator.validate_password_strength(password_data.new_password)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    new_hashed_password = auth_service.get_password_hash(password_data.new_password)
    await crud.change_user_password(db=db, user=current_user, new_hashed_password=new_hashed_password)

    logger.info("Password changed for user: %s", current_user.username)
    return {"message": "Password changed successfully."}
