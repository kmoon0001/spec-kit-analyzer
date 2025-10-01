from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...core.compliance_service import ComplianceService
from ...core.domain_models import TherapyDocument

router = APIRouter(prefix="/compliance", tags=["Compliance"])
service = ComplianceService()


class TherapyDocumentRequest(BaseModel):
    id: str
    text: str
    discipline: str
    document_type: str


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
    positive_keywords: List[str]
    negative_keywords: List[str]


class ComplianceFindingModel(BaseModel):
    rule: ComplianceRuleModel
    text_snippet: str
    risk_level: str


class ComplianceResultModel(BaseModel):
    document: TherapyDocumentRequest
    findings: List[ComplianceFindingModel]
    is_compliant: bool


@router.post("/evaluate", response_model=ComplianceResultModel)
async def evaluate_document(payload: TherapyDocumentRequest) -> ComplianceResultModel:
    if not payload.text or not payload.discipline or not payload.document_type:
        raise HTTPException(
            status_code=400,
            detail="Document text, discipline, and document_type are required.",
        )

    result = service.evaluate_document(
        TherapyDocument(
            id=payload.id,
            text=payload.text,
            discipline=payload.discipline,
            document_type=payload.document_type,
        )
    )
    return ComplianceResultModel(**ComplianceService.to_dict(result))
