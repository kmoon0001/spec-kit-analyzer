from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import uuid
import os

from ... import crud, schemas, models
from ...database import get_db
from ...auth import AuthService, get_auth_service, get_current_admin_user

router = APIRouter()

# Get the absolute path to the project's root directory
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
ADMIN_HTML_PATH = os.path.join(ROOT_DIR, "src", "resources", "admin.html")

@router.get("/dashboard", response_class=FileResponse)
def get_admin_dashboard(admin_user: models.User = Depends(get_current_admin_user)):
    """Serves the admin dashboard HTML page. Admin only."""
    if not os.path.exists(ADMIN_HTML_PATH):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="admin.html not found")
    return FileResponse(ADMIN_HTML_PATH)

@router.get("/users", response_model=List[schemas.User])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    """Retrieves a list of all users. Admin only."""
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.post("/users", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Creates a new user. Admin only."""
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    hashed_password = auth_service.get_password_hash(user.password)
    license_key = str(uuid.uuid4()) # Generate a unique license key

    new_user = models.User(
        username=user.username, 
        hashed_password=hashed_password, 
        license_key=license_key,
        is_active=True # New users are active by default
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/users/{user_id}/activate", response_model=schemas.User)
def activate_user(
    user_id: int, 
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    """Activates a user's license. Admin only."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_user.is_active = True  # type: ignore[assignment]
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/users/{user_id}/deactivate", response_model=schemas.User)
def deactivate_user(
    user_id: int, 
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    """Deactivates a user's license. Admin only."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_user.is_active = False  # type: ignore[assignment]
    db.commit()
    db.refresh(db_user)
    return db_user
