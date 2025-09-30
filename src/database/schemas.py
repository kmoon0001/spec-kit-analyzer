from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
import datetime

# --- Schemas for Reports and Findings (Dashboard) ---


class FindingBase(BaseModel):
    rule_id: str
    risk: str
    personalized_tip: str
    problematic_text: str
    clinician_name: Optional[str] = None
    habit_name: Optional[str] = None


class Finding(FindingBase):
    id: int
    report_id: int

    model_config = ConfigDict(from_attributes=True)


class FindingCreate(FindingBase):
    pass


class ReportBase(BaseModel):
    document_name: str
    compliance_score: float
    analysis_result: Dict[str, Any]
    document_embedding: Optional[bytes] = None


class ReportCreate(ReportBase):
    pass


class Report(ReportBase):
    id: int
    analysis_date: datetime.datetime
    findings: List[Finding] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


# --- Schemas for Users and Auth ---


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True)


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


# --- Schemas for Director Dashboard ---


class TeamHabitAnalytics(BaseModel):
    habit_name: str
    count: int


class ClinicianHabitAnalytics(BaseModel):
    clinician_name: str
    habit_name: str
    count: int


class DirectorDashboardData(BaseModel):
    total_findings: int
    team_habit_summary: List[TeamHabitAnalytics]
    clinician_habit_breakdown: List[ClinicianHabitAnalytics]


class CoachingFocus(BaseModel):
    focus_title: str = Field(..., description="The title for the weekly coaching focus.")
    summary: str = Field(
        ..., description="A brief summary of the key issue identified."
    )
    root_cause: str = Field(
        ..., description="The AI's inferred root cause of the issue."
    )
    action_steps: List[str] = Field(
        ..., description="A list of concrete action steps for the team."
    )


class HabitTrendPoint(BaseModel):
    date: datetime.date
    habit_name: str
    count: int
