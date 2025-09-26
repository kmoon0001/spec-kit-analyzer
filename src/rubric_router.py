from fastapi import APIRouter, HTTPException
from typing import List
import sqlite3

from src.models import Rubric, RubricCreate
from src.database import DATABASE_PATH

router = APIRouter()


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.post("/rubrics/", response_model=Rubric)
def create_rubric(rubric: RubricCreate):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO rubrics (name, content) VALUES (?, ?)",
                (rubric.name, rubric.content),
            )
            conn.commit()
            new_rubric_id = cur.lastrowid
            return Rubric(id=new_rubric_id, name=rubric.name, content=rubric.content)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400, detail="A rubric with this name already exists."
        )
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.get("/rubrics/", response_model=List[Rubric])
def get_rubrics():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, content FROM rubrics ORDER BY name ASC")
        rows = cur.fetchall()
        return [
            Rubric(id=row["id"], name=row["name"], content=row["content"])
            for row in rows
        ]


@router.get("/rubrics/{rubric_id}", response_model=Rubric)
def get_rubric(rubric_id: int):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, content FROM rubrics WHERE id = ?", (rubric_id,))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Rubric not found")
        return Rubric(id=row["id"], name=row["name"], content=row["content"])


@router.put("/rubrics/{rubric_id}", response_model=Rubric)
def update_rubric(rubric_id: int, rubric: RubricCreate):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE rubrics SET name = ?, content = ? WHERE id = ?",
            (rubric.name, rubric.content, rubric_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Rubric not found")
        return Rubric(id=rubric_id, name=rubric.name, content=rubric.content)


@router.delete("/rubrics/{rubric_id}", response_model=Rubric)
def delete_rubric(rubric_id: int):
    with get_db_connection() as conn:
        cur = conn.cursor()
        # First, get the rubric to return it after deletion
        cur.execute("SELECT id, name, content FROM rubrics WHERE id = ?", (rubric_id,))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Rubric not found")

        rubric_to_delete = Rubric(
            id=row["id"], name=row["name"], content=row["content"]
        )

        cur.execute("DELETE FROM rubrics WHERE id = ?", (rubric_id,))
        conn.commit()

        return rubric_to_delete
