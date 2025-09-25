from pydantic import BaseModel, Field
from typing import Optional, List

class ComplianceRule(BaseModel):
    uri: str
    issue_title: str
    issue_detail: str
    severity: str
    strict_severity: str
    issue_category: str
    discipline: str
    document_type: Optional[str] = None
    suggestion: str
    financial_impact: int
    positive_keywords: List[str]
    negative_keywords: List[str]

class RubricBase(BaseModel):
    name: str
    content: str

class RubricCreate(RubricBase):
    pass

class Rubric(RubricBase):
    id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
