from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ...database import crud, schemas
from ...database.database import get_async_db as get_db
from ...auth import get_current_admin_user

router = APIRouter(prefix="/rubrics", tags=["rubrics"])


@router.post("/", response_model=schemas.Rubric)
async def create_rubric(
    rubric: schemas.RubricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_admin_user),
):
    return await crud.create_rubric(db=db, rubric=rubric)


@router.get("/", response_model=List[schemas.Rubric])
async def read_rubrics(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_admin_user),
):
    return await crud.get_rubrics(db, skip=skip, limit=limit)


@router.get("/{rubric_id}", response_model=schemas.Rubric)
async def read_rubric(
    rubric_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_admin_user),
):
    db_rubric = await crud.get_rubric(db, rubric_id=rubric_id)
    if db_rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return db_rubric


@router.put("/{rubric_id}", response_model=schemas.Rubric)
async def update_rubric(
    rubric_id: int,
    rubric: schemas.RubricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_admin_user),
):
    db_rubric = await crud.update_rubric(db, rubric_id=rubric_id, rubric=rubric)
    if db_rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return db_rubric


@router.delete("/{rubric_id}", response_model=schemas.Rubric)
async def delete_rubric(
    rubric_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: schemas.User = Depends(get_current_admin_user),
):
    db_rubric = await crud.get_rubric(db, rubric_id=rubric_id)
    if db_rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found")
    await crud.delete_rubric(db, rubric_id=rubric_id)
    return db_rubric
