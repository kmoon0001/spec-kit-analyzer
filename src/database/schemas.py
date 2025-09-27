from pydantic import BaseModel
from typing import Optional, List
import datetime

# --- Schemas for Reports and Findings (Dashboard) ---


class FindingBase(BaseModel):
    rule_id: str
    risk: str
    personalized_tip: str
    problematic_text: str


class Finding(FindingBase):
    id: int
    report_id: int

    class Config:
        from_attributes = True


class FindingCreate(FindingBase):
    pass



class ReportBase(BaseModel):
    document_name: str
    compliance_score: float
    analysis_result: dict
    document_embedding: Optional[bytes] = None


class ReportCreate(ReportBase):
    pass



class Report(ReportBase):
    id: int
    analysis_date: datetime.datetime
    findings: List[Finding] = []

    class Config:
        from_attributes = True



class FindingSummary(BaseModel):
    rule_id: str
    count: int


# --- Schemas for Rubrics ---


class RubricBase(BaseModel):
    name: str
    content: str
    category: str | None = None



class RubricCreate(RubricBase):
    pass


class Rubric(RubricBase):
    id: int

    class Config:
        from_attributes = True



# --- Schemas for Users and Auth ---


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool = False

    class Config:
        from_attributes = True



class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# --- Schemas for Analysis Tasks ---


class TaskStatus(BaseModel):
    task_id: str
    status: str
    error: str | None = None


class AnalysisResult(BaseModel):
    task_id: str
    status: str


# --- Schemas for Conversational Chat (New) ---


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    history: List[ChatMessage]


class ChatResponse(BaseModel):
    response: str
