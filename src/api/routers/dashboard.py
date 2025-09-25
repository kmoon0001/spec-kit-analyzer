from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ... import crud, schemas, models
from ...database import get_db
from ...auth import get_current_active_user

router = APIRouter()

@router.get("/reports", response_model=List[schemas.Report])
def read_reports(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieves a list of historical analysis reports for the dashboard.
    """
    reports = crud.get_reports(db, skip=skip, limit=limit)
    return reports
