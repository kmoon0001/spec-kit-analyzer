from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.database import crud, models, schemas
from src.database.database import get_db
from src.api.routers.auth import get_current_admin_user

router = APIRouter()

@router.post("/rubrics/", response_model=schemas.Rubric, dependencies=[Depends(get_current_admin_user)])
def create_rubric(rubric: schemas.RubricCreate, db: Session = Depends(get_db)):
    return crud.create_rubric(db=db, rubric=rubric)

@router.get("/rubrics/", response_model=List[schemas.Rubric], dependencies=[Depends(get_current_admin_user)])
def read_rubrics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rubrics = crud.get_rubrics(db, skip=skip, limit=limit)
    return rubrics

@router.get("/rubrics/{rubric_id}", response_model=schemas.Rubric, dependencies=[Depends(get_current_admin_user)])
def read_rubric(rubric_id: int, db: Session = Depends(get_db)):
    db_rubric = crud.get_rubric(db, rubric_id=rubric_id)
    if db_rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return db_rubric

@router.put("/rubrics/{rubric_id}", response_model=schemas.Rubric, dependencies=[Depends(get_current_admin_user)])
def update_rubric(rubric_id: int, rubric: schemas.RubricCreate, db: Session = Depends(get_db)):
    db_rubric = crud.update_rubric(db, rubric_id=rubric_id, rubric=rubric)
    if db_rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return db_rubric

@router.delete("/rubrics/{rubric_id}", response_model=schemas.Rubric, dependencies=[Depends(get_current_admin_user)])
def delete_rubric(rubric_id: int, db: Session = Depends(get_db)):
    db_rubric = crud.delete_rubric(db, rubric_id=rubric_id)
    if db_rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return db_rubric