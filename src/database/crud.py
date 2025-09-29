from . import models, schemas
import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete


async def get_user_by_username(
    db: AsyncSession, username: str
) -> Optional[models.User]:
    result = await db.execute(
        select(models.User).filter(models.User.username == username)
    )
    return result.scalars().first()


async def get_user(db: AsyncSession, user_id: int) -> Optional[models.User]:
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    return result.scalars().first()


async def create_user(
    db: AsyncSession, user: schemas.UserCreate, hashed_password: str
) -> models.User:
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def delete_user(db: AsyncSession, user_id: int) -> None:
    await db.execute(delete(models.User).where(models.User.id == user_id))
    await db.commit()


async def change_user_password(
    db: AsyncSession, user: models.User, new_hashed_password: str
) -> models.User:
    user.hashed_password = new_hashed_password
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_rubric(
    db: AsyncSession, rubric: schemas.RubricCreate
) -> models.Rubric:
    db_rubric = models.Rubric(**rubric.model_dump())
    db.add(db_rubric)
    await db.commit()
    await db.refresh(db_rubric)
    return db_rubric


async def get_rubric(db: AsyncSession, rubric_id: int) -> Optional[models.Rubric]:
    result = await db.execute(
        select(models.Rubric).filter(models.Rubric.id == rubric_id)
    )
    return result.scalars().first()


async def get_rubrics(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[models.Rubric]:
    result = await db.execute(select(models.Rubric).offset(skip).limit(limit))
    return result.scalars().all()


async def update_rubric(
    db: AsyncSession, rubric_id: int, rubric: schemas.RubricCreate
) -> Optional[models.Rubric]:
    db_rubric = await get_rubric(db, rubric_id)
    if db_rubric:
        for key, value in rubric.model_dump().items():
            setattr(db_rubric, key, value)
        await db.commit()
        await db.refresh(db_rubric)
    return db_rubric


async def delete_rubric(db: AsyncSession, rubric_id: int) -> None:
    await db.execute(delete(models.Rubric).where(models.Rubric.id == rubric_id))
    await db.commit()


async def create_report(
    db: AsyncSession, report: schemas.ReportCreate
) -> models.Report:
    db_report = models.Report(**report.model_dump())
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)
    return db_report


# --- CRUD for Collaborative Review Mode ---

async def create_review(db: AsyncSession, report_id: int, author_id: int) -> models.Review:
    """Creates a new review request for a report."""
    db_review = models.Review(report_id=report_id, author_id=author_id, status="pending")
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    return db_review

async def get_review(db: AsyncSession, review_id: int) -> Optional[models.Review]:
    """Gets a single review by its ID."""
    result = await db.execute(
        select(models.Review).filter(models.Review.id == review_id)
    )
    return result.scalars().first()

async def get_pending_reviews(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.Review]:
    """Gets a list of all reviews with a 'pending' status."""
    result = await db.execute(
        select(models.Review)
        .filter(models.Review.status == "pending")
        .order_by(models.Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def add_comment_to_review(db: AsyncSession, review_id: int, commenter_id: int, content: str) -> models.Comment:
    """Adds a new comment to a review."""
    db_comment = models.Comment(
        review_id=review_id,
        commenter_id=commenter_id,
        content=content,
    )
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    return db_comment

async def update_review_status(db: AsyncSession, review_id: int, new_status: str, reviewer_id: int) -> Optional[models.Review]:
    """Updates the status of a review and assigns the reviewer."""
    db_review = await get_review(db, review_id)
    if db_review:
        db_review.status = new_status
        db_review.reviewer_id = reviewer_id
        await db.commit()
        await db.refresh(db_review)
    return db_review


async def get_report(db: AsyncSession, report_id: int) -> Optional[models.Report]:
    result = await db.execute(
        select(models.Report).filter(models.Report.id == report_id)
    )
    return result.scalars().first()


async def get_reports(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[models.Report]:
    result = await db.execute(select(models.Report).offset(skip).limit(limit))
    return result.scalars().all()


async def delete_report(db: AsyncSession, report_id: int) -> None:
    await db.execute(
        delete(models.Finding).where(models.Finding.report_id == report_id)
    )
    await db.execute(delete(models.Report).where(models.Report.id == report_id))
    await db.commit()


async def delete_reports_older_than(db: AsyncSession, days: int) -> int:
    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    # Delete associated findings first due to foreign key constraints
    # Find report IDs to delete
    reports_to_delete_query = select(models.Report.id).filter(
        models.Report.analysis_date < cutoff_date
    )
    reports_to_delete_result = await db.execute(reports_to_delete_query)
    report_ids_to_delete = reports_to_delete_result.scalars().all()

    if report_ids_to_delete:
        # Delete findings associated with these reports
        await db.execute(
            delete(models.Finding).where(
                models.Finding.report_id.in_(report_ids_to_delete)
            )
        )
        # Then delete the reports
        result = await db.execute(
            delete(models.Report).filter(models.Report.analysis_date < cutoff_date)
        )
        await db.commit()
        return result.rowcount
    return 0


async def find_similar_report(
    db: AsyncSession, embedding: bytes, threshold: float = 0.9
) -> Optional[models.Report]:
    # This is a placeholder for actual similarity search logic.
    # In a real application, this would involve a vector database or a more sophisticated similarity search.
    # For now, we'll return None, simulating no similar report found.
    return None


async def create_report_and_findings(
    db: AsyncSession,
    report_data: schemas.ReportCreate,
    findings_data: List[schemas.FindingCreate],
) -> models.Report:
    db_report = models.Report(
        document_name=report_data.document_name,
        compliance_score=report_data.compliance_score,
        analysis_result=report_data.analysis_result,
        document_embedding=report_data.document_embedding,
    )
    db.add(db_report)
    await db.flush()  # Flush to get the report ID before adding findings

    for finding_data in findings_data:
        db_finding = models.Finding(
            report_id=db_report.id,
            rule_id=finding_data.rule_id,
            risk=finding_data.risk,
            personalized_tip=finding_data.personalized_tip,
            problematic_text=finding_data.problematic_text,
        )
        db.add(db_finding)

    await db.commit()
    await db.refresh(db_report)
    return db_report
