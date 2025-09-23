from pydantic import BaseModel

class RubricBase(BaseModel):
    name: str
    content: str

class RubricCreate(RubricBase):
    pass

class Rubric(RubricBase):
    id: int

    class Config:
        orm_mode = True
