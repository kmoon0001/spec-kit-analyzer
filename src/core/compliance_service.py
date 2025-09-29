import logging
from dataclasses import asdict
from typing import Any, Iterable, List, Optional

from .models import (
    ComplianceFinding,
    ComplianceResult,
    ComplianceRule,
    TherapyDocument,
)


logger = logging.getLogger(__name__)


class ComplianceService:
    """Keyword-driven compliance evaluation with injectable rule sets."""

    def __init__(
        self,
        rules: Optional[Iterable[ComplianceRule]] = None,
        analysis_service: Optional[Any] = None,
        **_unused: Any
    ) -> None:
        provided_rules = list(rules or [])
        self.rules: List[ComplianceRule] = provided_rules or self._default_rules()
        self.analysis_service = analysis_service

    def get_available_rubrics(self) -> List[dict]:
        """Return available rules/rubrics for UI consumption."""
        return [asdict(rule) for rule in self.rules]

    def get_analysis_service(self) -> Optional[Any]:
        """Expose the underlying analysis service when available."""
        return self.analysis_service

    def evaluate_document(self, document: TherapyDocument) -> ComplianceResult:
        logger.info("Evaluating compliance for document %s", document.id)
        findings: List[ComplianceFinding] = []
        normalized_text = document.text.lower()

        for rule in self.rules:
            if not self._rule_matches_context(rule, document):
                continue

            if self._violates_rule(rule, normalized_text):
                findings.append(
                    ComplianceFinding(
                        rule=rule,
                        text_snippet=self._build_snippet(rule),
                        risk_level=rule.severity,
                    )
                )

        result = ComplianceResult(
            document=document,
            findings=findings,
            is_compliant=not findings,
        )
        logger.info(
            "Compliance evaluation for %s finished with %d findings",
            document.id,
            len(findings),
        )
        return result

    def _default_rules(self) -> List[ComplianceRule]:
        return [
            ComplianceRule(
                uri="rule://documentation/signature",
                severity="finding",
                strict_severity="high",
                issue_title="Provider signature/date possibly missing",
                issue_detail="",
                issue_category="documentation",
                discipline="pt",
                document_type="evaluation",
                suggestion="Include therapist signature or attestation.",
                financial_impact=100,
                positive_keywords=[],
                negative_keywords=["signature", "signed"],
            ),
            ComplianceRule(
                uri="rule://goals/measurable",
                severity="finding",
                strict_severity="medium",
                issue_title="Goals may not be measurable/time-bound",
                issue_detail="",
                issue_category="goals",
                discipline="pt",
                document_type="progress note",
                suggestion="Add measurable, time-bound goals.",
                financial_impact=50,
                positive_keywords=["goal"],
                negative_keywords=["measurable", "specific"],
            ),
        ]

    @staticmethod
    def _rule_matches_context(rule: ComplianceRule, document: TherapyDocument) -> bool:
        discipline_ok = rule.discipline.lower() in {
            "any",
            "*",
            document.discipline.lower(),
        }

        document_type = document.document_type.lower()
        rule_doc_type = rule.document_type.lower()
        doc_type_ok = rule_doc_type in {"any", "*", document_type}

        return discipline_ok and doc_type_ok

    @staticmethod
    def _contains_any(keywords: Iterable[str], text: str) -> bool:
        return any(keyword.lower() in text for keyword in keywords)

    def _violates_rule(self, rule: ComplianceRule, normalized_text: str) -> bool:
        has_positive_context = True
        if rule.positive_keywords:
            has_positive_context = self._contains_any(
                rule.positive_keywords, normalized_text
            )

        if not has_positive_context:
            return False

        if not rule.negative_keywords:
            return True

        has_required_terms = self._contains_any(rule.negative_keywords, normalized_text)
        return not has_required_terms

    @staticmethod
    def _build_snippet(rule: ComplianceRule) -> str:
        if rule.negative_keywords:
            return "Required documentation terms were not detected: " + ", ".join(
                rule.negative_keywords
            )
        if rule.positive_keywords:
            return "Expected keywords were missing: " + ", ".join(
                rule.positive_keywords
            )
        return "Rule conditions not met by the document content."

    @staticmethod
    def to_dict(result: ComplianceResult) -> dict:
        document = asdict(result.document)
        findings = [
            {
                "rule": asdict(finding.rule),
                "text_snippet": finding.text_snippet,
                "risk_level": finding.risk_level,
            }
            for finding in result.findings
        ]
        return {
            "document": document,
            "findings": findings,
            "is_compliant": result.is_compliant,
        }
