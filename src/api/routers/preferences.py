from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import get_current_active_user
from ...core.security_validator import SecurityValidator
from ...database import models, schemas
from ...database.database import get_async_db

router = APIRouter(prefix="/preferences", tags=["Preferences"])

_DEFAULT_PREFERENCES = schemas.UserPreferences()


def _merge_preferences(existing: dict[str, object] | None) -> schemas.UserPreferences:
    base = _DEFAULT_PREFERENCES.model_dump()
    if existing:
        base.update(existing)
    try:
        return schemas.UserPreferences(**base)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get("/me", response_model=schemas.UserPreferences)
async def get_user_preferences(
    current_user: models.User = Depends(get_current_active_user),
) -> schemas.UserPreferences:
    """Return the authenticated user's persisted application preferences."""
    return _merge_preferences(current_user.preferences)


@router.put("/me", response_model=schemas.UserPreferences)
async def update_user_preferences(
    update: schemas.UserPreferencesUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
) -> schemas.UserPreferences:
    """Persist updated user preferences after validating strictness selections."""
    payload = update.model_dump(exclude_unset=True)

    if strictness := payload.get("default_strictness"):
        is_valid, error = SecurityValidator.validate_strictness(strictness)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error
            )

    merged = _merge_preferences(current_user.preferences).model_dump()
    merged.update({k: v for k, v in payload.items() if v is not None})

    current_user.preferences = merged
    db.add(current_user)
    await db.flush()

    return schemas.UserPreferences(**merged)
