
class User(UserBase):
    id: int
    created_at: datetime.datetime
    is_active: bool = True
    is_admin: bool = False

    class Config:
        orm_mode = True


# --- Finding Summary Schemas ---

class FindingSummary(BaseModel):
    issue_title: str
    count: int


# --- Chat Schemas ---

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    history: List[ChatMessage]

class ChatResponse(BaseModel):
    response: str

class UserInDB(User):
    hashed_password: str

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str


# --- Analysis Report Schemas ---

class AnalysisReportBase(BaseModel):
    document_name: str
    compliance_score: float
    summary: Optional[str] = None
    findings: Optional[dict] = None

class AnalysisReportCreate(AnalysisReportBase):
    pass

class AnalysisReport(AnalysisReportBase):
    id: int
    owner_id: int
    created_at: datetime.datetime

    class Config:
        orm_mode = True

# --- Compliance Rubric Schemas ---

class ComplianceRubricBase(BaseModel):
    name: str
    description: Optional[str] = None
    rules: Optional[dict] = None

class ComplianceRubricCreate(ComplianceRubricBase):
    pass

class ComplianceRubric(ComplianceRubricBase):
    id: int
    created_at: datetime.datetime

    class Config:
        orm_mode = True


# --- Dashboard Schemas ---

class TeamHabitSummary(BaseModel):
    habit_name: str
    count: int

class ClinicianHabitBreakdown(BaseModel):
    clinician_name: str
    habit_name: str
    count: int

class HabitTrendPoint(BaseModel):
    date: datetime.date
    habit_name: str
    count: int

class DirectorDashboardData(BaseModel):
    total_findings: int
    team_habit_summary: List[TeamHabitSummary]
    clinician_habit_breakdown: List[ClinicianHabitBreakdown]

class CoachingFocus(BaseModel):
    focus_title: str
    summary: str
    root_cause: str
    action_steps: List[str]