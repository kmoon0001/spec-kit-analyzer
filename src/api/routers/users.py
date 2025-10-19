from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import AuthService, get_auth_service, get_current_active_user
from src.core.security_validator import SecurityValidator
from src.database import models, schemas
from src.database.database import get_async_db

router = APIRouter()


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str


@router.get("/users/me", response_model=schemas.User)
async def get_current_user(
    current_user: models.User = Depends(get_current_active_user),
):
    """Get the current user's information."""
    return current_user


@router.put("/users/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_current_user_password(
    password_data: PasswordUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Allows the currently logged-in user to change their password."""
    # 1. Validate new password strength
    is_valid, error_msg = SecurityValidator.validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # 2. Verify the old password is correct
    if not auth_service.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password.")

    # 3. Hash the new password
    new_hashed_password = auth_service.get_password_hash(password_data.new_password)

    # 4. Update the user in the database
    current_user.hashed_password = new_hashed_password
    db.add(current_user)
    await db.commit()
