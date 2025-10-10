"""
API router for handling user feedback on AI-generated findings.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import get_current_active_user
from ...database import crud, models, schemas
from ...database import get_async_db as get_db

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("/", response_model=schemas.FeedbackAnnotation, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback: schemas.FeedbackAnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Submit feedback for an AI-generated finding. This is a critical part of the
    Human-in-the-Loop (HITL) learning process.
    """
    try:
        # The CRUD function already exists, so we just need to call it.
        db_feedback = await crud.create_feedback_annotation(
            db=db, feedback=feedback, user_id=current_user.id
        )
        return db_feedback
    except Exception as e:
        # In a production system, you might catch more specific database errors.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while saving feedback: {e}",
        )
