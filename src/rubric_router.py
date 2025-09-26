from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import crud, schemas
from .database import get_db

router = APIRouter()

@router.post("/rubrics/", response_model=schemas.Rubric)
def create_rubric_endpoint(rubric: schemas.RubricCreate, db: Session = Depends(get_db)):
    db_rubric = crud.get_rubric_by_name(db, name=rubric.name)
    if db_rubric:
        raise HTTPException(status_code=400, detail="A rubric with this name already exists.")
    return crud.create_rubric(db=db, rubric=rubric)

@router.get("/rubrics/", response_model=List[schemas.Rubric])
def read_rubrics_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rubrics = crud.get_rubrics(db, skip=skip, limit=limit)
    return rubrics

@router.get("/rubrics/{rubric_id}", response_model=schemas.Rubric)
def read_rubric_endpoint(rubric_id: int, db: Session = Depends(get_db)):
    db_rubric = crud.get_rubric(db, rubric_id=rubric_id)
    if db_rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return db_rubric

@router.put("/rubrics/{rubric_id}", response_model=schemas.Rubric)
def update_rubric_endpoint(rubric_id: int, rubric: schemas.RubricCreate, db: Session = Depends(get_db)):
    db_rubric = crud.update_rubric(db, rubric_id=rubric_id, rubric_update=rubric)
    if db_rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found to update")
    return db_rubric

@router.delete("/rubrics/{rubric_id}", response_model=schemas.Rubric)
def delete_rubric_endpoint(rubric_id: int, db: Session = Depends(get_db)):
    db_rubric = crud.delete_rubric(db, rubric_id=rubric_id)
    if db_rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found to delete")
    return db_rubric