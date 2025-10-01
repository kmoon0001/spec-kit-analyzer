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
    document_type: Optional[str] = None


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
    regulation: str
    common_pitfalls: str
    best_practice: str
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

# --- Schemas for Dashboard Analytics ---

class HabitSummary(BaseModel):
    habit_name: str
    count: int

class ClinicianHabitBreakdown(BaseModel):
    clinician_name: str
    habit_name: str
    count: int

class DirectorDashboardData(BaseModel):
    total_findings: int
    team_habit_summary: List[HabitSummary]
    clinician_habit_breakdown: List[ClinicianHabitBreakdown]

class CoachingFocus(BaseModel):
    focus_title: str
    summary: str
    root_cause: str
    action_steps: List[str]

class HabitTrendPoint(BaseModel):
    date: datetime.date
    count: int