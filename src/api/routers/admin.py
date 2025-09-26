from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
import os

from ... import crud, schemas, models
from ...database import get_async_db as get_db
from ...auth import get_current_admin_user, get_auth_service, AuthService

router = APIRouter()

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
ADMIN_HTML_PATH = os.path.join(ROOT_DIR, "src", "resources", "admin.html")

@router.get("/dashboard", response_class=FileResponse)
async def get_admin_dashboard(admin_user: models.User = Depends(get_current_admin_user)):
    if not os.path.exists(ADMIN_HTML_PATH):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="admin.html not found")
    return FileResponse(ADMIN_HTML_PATH)

@router.get("/users", response_model=List[schemas.User])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    hashed_password = auth_service.get_password_hash(user.password)
    license_key = str(uuid.uuid4())

    new_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        license_key=license_key,
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.put("/users/{user_id}/activate", response_model=schemas.User)
async def activate_user(
    user_id: int, 
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    db_user = await crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_user.is_active = True
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.put("/users/{user_id}/deactivate", response_model=schemas.User)
async def deactivate_user(
    user_id: int, 
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    db_user = await crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_user.is_active = False
    await db.commit()
    await db.refresh(db_user)
    return db_user