"""
API Router for the Collaborative Review Mode feature.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from ...database import crud, models, schemas
from ...database import get_async_db as get_db
from ...auth import get_current_active_user, get_current_admin_user

logger = logging.getLogger(__name__)
router = APIRouter()

def require_supervisor(current_user: models.User = Depends(get_current_active_user)):
    """Dependency to ensure the current user has the 'supervisor' role."""
    if current_user.role != "supervisor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires supervisor privileges.",
        )
    return current_user

@router.post("/reports/{report_id}/request-review", response_model=schemas.Review)
async def request_review_for_report(
    report_id: int,
    db: get_db = Depends(),
    current_user: models.User = Depends(get_current_active_user),
):
    """Endpoint for a therapist to request a review for their report."""
    db_report = await crud.get_report(db, report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")

    # In a real system, you might check ownership. For now, we assume users can request reviews for any report.

    review = await crud.create_review(db=db, report_id=report_id, author_id=current_user.id)
    logger.info(f"User '{current_user.username}' requested a review for report {report_id}.")
    return review

@router.get("/reviews/pending", response_model=List[schemas.Review])
async def get_pending_reviews_for_supervisor(
    db: get_db = Depends(),
    supervisor: models.User = Depends(require_supervisor),
):
    """Endpoint for supervisors to get a list of all pending reviews."""
    logger.info(f"Supervisor '{supervisor.username}' fetched pending reviews.")
    pending_reviews = await crud.get_pending_reviews(db)
    return pending_reviews

@router.post("/reviews/{review_id}/comments", response_model=schemas.Comment)
async def add_comment_to_review(
    review_id: int,
    comment: schemas.CommentCreate,
    db: get_db = Depends(),
    current_user: models.User = Depends(get_current_active_user),
):
    """Endpoint to add a comment to a specific review."""
    db_review = await crud.get_review(db, review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")

    # In a real system, you'd check if the commenter is the author or an assigned reviewer.
    new_comment = await crud.add_comment_to_review(
        db=db,
        review_id=review_id,
        commenter_id=current_user.id,
        content=comment.content,
    )
    logger.info(f"User '{current_user.username}' added a comment to review {review_id}.")
    return new_comment

@router.put("/reviews/{review_id}/status", response_model=schemas.Review)
async def update_review_status(
    review_id: int,
    status_update: schemas.ReviewBase, # We can reuse this to get the status
    db: get_db = Depends(),
    supervisor: models.User = Depends(require_supervisor),
):
    """Endpoint for a supervisor to update the status of a review (e.g., 'completed')."""
    updated_review = await crud.update_review_status(
        db=db,
        review_id=review_id,
        new_status=status_update.status,
        reviewer_id=supervisor.id,
    )
    if not updated_review:
        raise HTTPException(status_code=404, detail="Review not found")

    logger.info(f"Supervisor '{supervisor.username}' updated status of review {review_id} to '{status_update.status}'.")
    return updated_review