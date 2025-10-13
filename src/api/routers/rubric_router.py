from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import get_current_active_user, get_current_admin_user
from ...database import crud, schemas
from ...database.database import get_async_db as get_db

router = APIRouter(tags=["rubrics"])


def _serialize_rubric(rubric: Any) -> schemas.RubricPublic:
    """Convert a rubric model into the public API representation."""
    rubric_data = schemas.Rubric.model_validate(rubric).model_dump()
    rubric_data["value"] = rubric_data["id"]
    return schemas.RubricPublic.model_validate(rubric_data)


@router.post("/", response_model=schemas.RubricPublic)
async def create_rubric(
    rubric: schemas.RubricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_admin_user),
) -> schemas.RubricPublic:
    created_rubric = await crud.create_rubric(db=db, rubric=rubric)
    return _serialize_rubric(created_rubric)


@router.get("/", response_model=schemas.RubricListResponse)
async def read_rubrics(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user),
) -> schemas.RubricListResponse:
    rubrics = await crud.get_rubrics(db, skip=skip, limit=limit)
    serialized = [_serialize_rubric(rubric) for rubric in rubrics]
    return schemas.RubricListResponse(rubrics=serialized)


@router.get("/{rubric_id}", response_model=schemas.RubricPublic)
async def read_rubric(
    rubric_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user),
) -> schemas.RubricPublic:
    db_rubric = await crud.get_rubric(db, rubric_id=rubric_id)
    if db_rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return _serialize_rubric(db_rubric)


@router.put("/{rubric_id}", response_model=schemas.RubricPublic)
async def update_rubric(
    rubric_id: int,
    rubric: schemas.RubricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_admin_user),
) -> schemas.RubricPublic:
    db_rubric = await crud.update_rubric(db, rubric_id=rubric_id, rubric=rubric)
    if db_rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return _serialize_rubric(db_rubric)


@router.delete("/{rubric_id}", response_model=schemas.RubricPublic)
async def delete_rubric(
    rubric_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_admin_user),
) -> schemas.RubricPublic:
    db_rubric = await crud.get_rubric(db, rubric_id=rubric_id)
    if db_rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found")
    await crud.delete_rubric(db, rubric_id=rubric_id)
    return _serialize_rubric(db_rubric)
