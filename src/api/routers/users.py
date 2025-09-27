from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ... import crud, schemas, models
from ...database import get_db
from ...auth import auth_service, get_current_active_user

router = APIRouter()

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

@router.put("/users/me/password", status_code=status.HTTP_204_NO_CONTENT)
def update_current_user_password(
    password_data: PasswordUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Allows the currently logged-in user to change their password.
    """
    # 1. Verify the old password is correct
    if not auth_service.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Incorrect old password."
        )

    # 2. Hash the new password
    new_hashed_password = auth_service.get_password_hash(password_data.new_password)

    # 3. Update the user in the database
    current_user.hashed_password = new_hashed_password
    db.add(current_user)
    db.commit()
