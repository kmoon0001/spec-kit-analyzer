"""Authentication API router for user login and password management.

Provides endpoints for JWT token generation and password changes.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import AuthService, get_auth_service, get_current_active_user
from ...core.security_validator import SecurityValidator
from ...database import crud, models, schemas
from ...database import get_async_db as get_db

router = APIRouter(tags=["auth"])


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate user and generate JWT access token.

    Args:
        form_data: OAuth2 form with username and password
        db: Database session
        auth_service: Authentication service

    Returns:
        Token response with access_token and token_type

    Raises:
        HTTPException: For invalid credentials or inactive accounts

    """
    # Validate username format
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


@router.post("/users/change-password")
async def change_password(
    password_data: schemas.UserPasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Change user password with validation.

    Args:
        password_data: Current and new password data
        db: Database session
        current_user: Authenticated user
        auth_service: Authentication service

    Returns:
        Success message

    Raises:
        HTTPException: For invalid current password or weak new password

    """
    # Verify current password
    if not auth_service.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password.")

    # Validate new password strength
    is_valid, error_msg = SecurityValidator.validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    new_hashed_password = auth_service.get_password_hash(password_data.new_password)
    await crud.change_user_password(db=db, user=current_user, new_hashed_password=new_hashed_password)

    return {"message": "Password changed successfully."}
