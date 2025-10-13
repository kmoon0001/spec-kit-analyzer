import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

# --- Schemas for Human-in-the-Loop Feedback ---


class FeedbackAnnotationBase(BaseModel):
    finding_id: str  # Changed from int to str to match hash
    is_correct: bool
    user_comment: str | None = None
    correction: str | None = None
    feedback_type: str = "finding_accuracy"


class FeedbackAnnotationCreate(FeedbackAnnotationBase):
    pass


class FeedbackAnnotation(FeedbackAnnotationBase):
    id: int
    user_id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# --- Schemas for Reports and Findings (Dashboard) ---


class FindingBase(BaseModel):
    rule_id: str
    risk: str
    personalized_tip: str
    problematic_text: str
    confidence_score: float = 0.0


class Finding(FindingBase):
    id: int
    report_id: int

    model_config = ConfigDict(from_attributes=True)


class FindingCreate(FindingBase):
    pass


class ReportBase(BaseModel):
    document_name: str
    compliance_score: float
    analysis_result: dict
    document_embedding: bytes | None = None
    document_type: str | None = None


class ReportCreate(ReportBase):
    pass


class Report(ReportBase):
    id: int
    analysis_date: datetime.datetime
    findings: list[Finding] = []

    model_config = ConfigDict(from_attributes=True)


class FindingSummary(BaseModel):
    rule_id: str
    count: int


# --- Schemas for Rubrics ---


class RubricBase(BaseModel):
    name: str
    discipline: str
    regulation: str
    common_pitfalls: str
    best_practice: str
    category: str | None = None


class RubricCreate(RubricBase):
    pass


class Rubric(RubricBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RubricPublic(Rubric):
    value: int

    model_config = ConfigDict(from_attributes=True)


class RubricListResponse(BaseModel):
    rubrics: list[RubricPublic]


# --- Schemas for Users and Auth ---


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str
    is_admin: bool = False
    license_key: str | None = None


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
    username: str | None = None


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
    history: list[ChatMessage]


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
    team_habit_summary: list[HabitSummary]
    clinician_habit_breakdown: list[ClinicianHabitBreakdown]


class CoachingFocus(BaseModel):
    focus_title: str
    summary: str
    root_cause: str
    action_steps: list[str]


class HabitTrendPoint(BaseModel):
    date: datetime.date
    count: int


# Habit Progression Schemas


class HabitGoalBase(BaseModel):
    """Base schema for habit goals."""

    title: str
    description: str | None = None
    habit_number: int | None = None
    target_value: float | None = None
    target_date: datetime.datetime | None = None


class HabitGoalCreate(HabitGoalBase):
    """Schema for creating habit goals."""


class HabitGoalUpdate(BaseModel):
    """Schema for updating habit goals."""

    title: str | None = None
    description: str | None = None
    progress: int | None = None
    status: str | None = None
    current_value: float | None = None


class HabitGoal(HabitGoalBase):
    """Schema for habit goal responses."""

    id: int
    user_id: int
    current_value: float | None = None
    progress: int
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    completed_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class HabitAchievementBase(BaseModel):
    """Base schema for habit achievements."""

    achievement_id: str
    title: str
    description: str
    icon: str = "🏆"
    category: str


class HabitAchievementCreate(HabitAchievementBase):
    """Schema for creating habit achievements."""


class HabitAchievement(HabitAchievementBase):
    """Schema for habit achievement responses."""

    id: int
    user_id: int
    earned_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class HabitProgressData(BaseModel):
    """Schema for individual habit progression data."""

    total_findings: int
    analysis_period_days: int
    habit_breakdown: dict[str, Any]
    focus_areas: list[tuple[str, dict[str, Any]]]
    mastered_habits: list[tuple[str, dict[str, Any]]]
    weekly_trends: list[dict[str, Any]]
    improvement_rate: float
    current_streak: int
    consistency_score: float
    overall_progress: dict[str, Any]
    achievements: list[dict[str, Any]]
    current_goals: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]


class WeeklyHabitTrend(BaseModel):
    """Schema for weekly habit trend data."""

    week_start: str
    week_end: str
    total_findings: int
    habit_breakdown: dict[str, int]
    avg_confidence: float


class HabitRecommendation(BaseModel):
    """Schema for habit recommendations."""

    type: str  # focus_area, improvement, consistency
    priority: str  # high, medium, low
    title: str
    description: str
    action_items: list[str]
    habit_number: int | None = None


class UserProgressSummary(BaseModel):
    """Schema for user progress summary."""

    user_id: int
    overall_progress_percentage: float
    overall_status: str  # New, Developing, Intermediate, Advanced, Expert
    current_streak: int
    total_analyses: int
    mastered_habits_count: int
    active_goals_count: int
    recent_achievements: list[HabitAchievement]
    next_milestone: str | None = None
