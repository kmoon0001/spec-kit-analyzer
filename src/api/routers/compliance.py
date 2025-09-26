from fastapi import APIRouter, Depends, HTTPException
from typing import List

from src.core.compliance_service import ComplianceService
from src.core.models import TherapyDocument, ComplianceResult, ComplianceRule, ComplianceFinding

router = APIRouter()

# This is a placeholder for a dependency injection system.
# In a real application, this would be handled by a proper DI framework.
def get_compliance_service():
    # The rules_directory should point to where your .ttl files are.
    # Based on the project structure, they are in the 'src' directory.
    return ComplianceService(rules_directory="src")

@router.post("/evaluate", response_model=ComplianceResult)
async def evaluate_document(
    document: TherapyDocument,
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """
    Evaluates a therapy document for compliance against a set of rules.
    """
    if not document.text or not document.discipline or not document.document_type:
        raise HTTPException(status_code=400, detail="Document text, discipline, and type are required.")

    try:
        result = compliance_service.evaluate_document(document)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during evaluation: {str(e)}")

# Pydantic models for the response. `dataclasses` are not directly compatible with FastAPI's response models.
# We need to redefine them as Pydantic models for the API layer.
from pydantic import BaseModel, Field

class ComplianceRuleModel(BaseModel):
    uri: str
    severity: str
    strict_severity: str
    issue_title: str
    issue_detail: str
    issue_category: str
    discipline: str
    document_type: str
    suggestion: str
    financial_impact: int
    positive_keywords: List[str] = Field(default_factory=list)
    negative_keywords: List[str] = Field(default_factory=list)

class ComplianceFindingModel(BaseModel):
    rule: ComplianceRuleModel
    text_snippet: str
    risk_level: str

class TherapyDocumentModel(BaseModel):
    id: str
    text: str
    discipline: str
    document_type: str

class ComplianceResultModel(BaseModel):
    document: TherapyDocumentModel
    findings: List[ComplianceFindingModel]
    is_compliant: bool

# We need to override the response model for the endpoint to use the Pydantic model
router.post("/evaluate", response_model=ComplianceResultModel)(evaluate_document)