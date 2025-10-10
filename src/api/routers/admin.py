import os
import uuid
from typing import Any

import yaml
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import AuthService, get_auth_service, get_current_admin_user
from ...config import Settings, get_settings
from ...database import crud, models, schemas
from ...database import get_async_db as get_db

router = APIRouter()

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ADMIN_HTML_PATH = os.path.join(ROOT_DIR, "src", "resources", "admin.html")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.yaml")


def get_filtered_settings() -> dict[str, Any]:
    """Loads settings and returns them as a dict, excluding sensitive fields."""
    settings = get_settings()
    # Exclude sensitive or complex fields that shouldn't be edited directly
    excluded_fields = {"auth", "database", "secret_key"}
    return settings.model_dump(exclude=excluded_fields)


@router.get("/dashboard", response_class=FileResponse)
async def get_admin_dashboard(
    admin_user: models.User = Depends(get_current_admin_user),
):
    if not os.path.exists(ADMIN_HTML_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="admin.html not found"
        )
    return FileResponse(ADMIN_HTML_PATH)


@router.get("/settings", response_model=dict[str, Any])
async def get_current_settings(
    admin_user: models.User = Depends(get_current_admin_user),
):
    """Endpoint to get the current, non-sensitive application settings."""
    return get_filtered_settings()


@router.post("/settings")
async def update_settings(
    new_settings: dict[str, Any] = Body(...),
    admin_user: models.User = Depends(get_current_admin_user),
):
    """Endpoint to validate and save new application settings."""
    try:
        # Load the current full settings to provide defaults
        with open(CONFIG_PATH) as f:
            current_config_data = yaml.safe_load(f)

        # Merge the new settings into the current ones
        updated_data = {**current_config_data, **new_settings}

        # Validate the merged data
        Settings.model_validate(updated_data)

        # Write the validated data back to the config file
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(new_settings, f, default_flow_style=False, sort_keys=False)

        return JSONResponse({"message": "Settings updated successfully. Restart the application for changes to take effect."})

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/users", response_model=list[schemas.User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
):
    result = await db.execute(select(models.User).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/users", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    db_user = await crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    hashed_password = auth_service.get_password_hash(user.password)
    license_key = str(uuid.uuid4())

    new_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        license_key=license_key,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.put("/users/{user_id}/activate", response_model=schemas.User)
async def activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
):
    # Assuming crud.get_user is an async function that gets a user by ID
    db_user = await crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    db_user.is_active = True
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.put("/users/{user_id}/deactivate", response_model=schemas.User)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
):
    # Assuming crud.get_user is an async function that gets a user by ID
    db_user = await crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    db_user.is_active = False
    await db.commit()
    await db.refresh(db_user)
    return db_user
