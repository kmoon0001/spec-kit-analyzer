from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from src.database.database import get_db

router = APIRouter()

@router.get("/health", status_code=200)
def health_check(db: Session = Depends(get_db)):
    """
    Checks the operational status of the API and its database connection.
    """
    start_time = time.time()
    try:
        # A simple query to check if the database is responsive
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    end_time = time.time()
    response_time = round((end_time - start_time) * 1000, 2)

    return {
        "status": "ok",
        "details": {
            "database": db_status,
            "response_time_ms": response_time
        }
    }