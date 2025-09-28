from pydantic import BaseModel
from typing import Optional, List
import datetime

# --- Schemas for Findings and Reports (for the new dashboard) ---


class FindingBase(BaseModel):
    rule_id: str
    risk: str
    personalized_tip: str
    problematic_text: str


class Finding(FindingBase):
    id: int
    report_id: int

    class Config:
        orm_mode = True


class ReportBase(BaseModel):
    document_name: str
    compliance_score: int


class Report(ReportBase):
    id: int
    analysis_date: datetime.datetime
    findings: List[Finding] = []

    class Config:
        orm_mode = True


# --- Schemas for Rubrics ---


class RubricBase(BaseModel):
    name: str
    content: str


class RubricCreate(RubricBase):
    pass


class Rubric(RubricBase):
    id: int

    class Config:
        orm_mode = True


# --- Schemas for Users and Auth ---


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


# --- Schemas for Analysis Tasks (used by the frontend) ---


class TaskStatus(BaseModel):
    task_id: str
    status: str
    error: str | None = None


class AnalysisResult(BaseModel):
    task_id: str
    status: str
