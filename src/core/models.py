from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class ComplianceRule:
    """Represents a single compliance rule."""
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
    positive_keywords: List[str] = field(default_factory=list)
    negative_keywords: List[str] = field(default_factory=list)

@dataclass
class TherapyDocument:
    """Represents a therapy document to be analyzed."""
    id: str
    text: str
    discipline: str
    document_type: str

@dataclass
class ComplianceFinding:
    """Represents a single compliance finding in a document."""
    rule: ComplianceRule
    text_snippet: str
    risk_level: str

@dataclass
class ComplianceResult:
    """Represents the overall result of a compliance evaluation."""
    document: TherapyDocument
    findings: List[ComplianceFinding]
    is_compliant: bool