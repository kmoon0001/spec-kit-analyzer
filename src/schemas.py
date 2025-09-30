from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime

# --- Token Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# --- User Schemas ---

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime.datetime
    is_active: bool = True

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