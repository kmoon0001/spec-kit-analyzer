from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    """
    Performs a health check of the API.
    This endpoint can be called by a monitoring service to verify that the
    application is running and can connect to the database.
    """
    try:
        # Perform a simple, fast query to check the database connection
        db.execute('SELECT 1')
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "database": "disconnected", "reason": str(e)}
        )
