from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any, Tuple
import datetime

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
    document_embedding: Optional[bytes] = None
    document_type: Optional[str] = None


class ReportCreate(ReportBase):
    pass


class Report(ReportBase):
    id: int
    analysis_date: datetime.datetime
    findings: List[Finding] = []

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


# --- Schemas for Users and Auth ---


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str
    is_admin: bool = False
    license_key: Optional[str] = None


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


# Habit Progression Schemas


class HabitGoalBase(BaseModel):
    """Base schema for habit goals."""

    title: str
    description: Optional[str] = None
    habit_number: Optional[int] = None
    target_value: Optional[float] = None
    target_date: Optional[datetime.datetime] = None


class HabitGoalCreate(HabitGoalBase):
    """Schema for creating habit goals."""

    pass


class HabitGoalUpdate(BaseModel):
    """Schema for updating habit goals."""

    title: Optional[str] = None
    description: Optional[str] = None
    progress: Optional[int] = None
    status: Optional[str] = None
    current_value: Optional[float] = None


class HabitGoal(HabitGoalBase):
    """Schema for habit goal responses."""

    id: int
    user_id: int
    current_value: Optional[float] = None
    progress: int
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None

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

    pass


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
    habit_breakdown: Dict[str, Any]
    focus_areas: List[Tuple[str, Dict[str, Any]]]
    mastered_habits: List[Tuple[str, Dict[str, Any]]]
    weekly_trends: List[Dict[str, Any]]
    improvement_rate: float
    current_streak: int
    consistency_score: float
    overall_progress: Dict[str, Any]
    achievements: List[Dict[str, Any]]
    current_goals: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]


class WeeklyHabitTrend(BaseModel):
    """Schema for weekly habit trend data."""

    week_start: str
    week_end: str
    total_findings: int
    habit_breakdown: Dict[str, int]
    avg_confidence: float


class HabitRecommendation(BaseModel):
    """Schema for habit recommendations."""

    type: str  # focus_area, improvement, consistency
    priority: str  # high, medium, low
    title: str
    description: str
    action_items: List[str]
    habit_number: Optional[int] = None


class UserProgressSummary(BaseModel):
    """Schema for user progress summary."""

    user_id: int
    overall_progress_percentage: float
    overall_status: str  # New, Developing, Intermediate, Advanced, Expert
    current_streak: int
    total_analyses: int
    mastered_habits_count: int
    active_goals_count: int
    recent_achievements: List[HabitAchievement]
    next_milestone: Optional[str] = None
