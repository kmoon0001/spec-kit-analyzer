
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
    positive_keywords: list[str]
    negative_keywords: list[str]


class ComplianceFindingModel(BaseModel):
    rule: ComplianceRuleModel
    text_snippet: str
    risk_level: str


class ComplianceResultModel(BaseModel):
    document: TherapyDocumentRequest
    findings: list[ComplianceFindingModel]
    is_compliant: bool


@router.get("/rubrics")
async def get_rubrics():
    """Get available compliance rubrics"""
    return {
        "rubrics": [
            {
                "id": "pt_compliance",
                "name": "PT Compliance Rubric",
                "discipline": "pt",
                "description": "Physical Therapy compliance guidelines"
            },
            {
                "id": "ot_compliance",
                "name": "OT Compliance Rubric",
                "discipline": "ot",
                "description": "Occupational Therapy compliance guidelines"
            },
            {
                "id": "slp_compliance",
                "name": "SLP Compliance Rubric",
                "discipline": "slp",
                "description": "Speech-Language Pathology compliance guidelines"
            }
        ]
    }


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
