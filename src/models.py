from pydantic import BaseModel
from typing import List, Optional

class ComplianceRule(BaseModel):
    uri: str
    issue_title: str
    issue_detail: str
    severity: str
    strict_severity: str
    issue_category: str
    discipline: str
    document_type: Optional[str]
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
