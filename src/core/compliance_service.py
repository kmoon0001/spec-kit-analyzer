import logging
from collections.abc import Iterable
from dataclasses import asdict
from typing import Any

from .domain_models import ComplianceFinding, ComplianceResult, ComplianceRule, TherapyDocument

logger = logging.getLogger(__name__)


class ComplianceService:
    """Keyword-driven compliance evaluation with injectable rule sets."""

    def __init__(
        self,
        rules: Iterable[ComplianceRule] | None = None,
        analysis_service: Any | None = None,
        **_unused: Any) -> None:
        """Initializes the ComplianceService.

        Args:
            rules: An optional iterable of ComplianceRule objects to use. If None, default rules are loaded.
            analysis_service: An optional analysis service instance to be used.
            **_unused: Unused keyword arguments.

        """
        provided_rules = list(rules or [])
        self.rules: list[ComplianceRule] = provided_rules or self._default_rules()
        self.analysis_service = analysis_service

    def get_available_rubrics(self) -> list[dict]:
        """Returns a list of available compliance rules/rubrics for UI consumption.

        Returns:
            A list of dictionaries, each representing a compliance rule.

        """
        """Return available rules/rubrics for UI consumption."""
        return [asdict(rule) for rule in self.rules]

    def get_analysis_service(self) -> Any | None:
        """Exposes the underlying analysis service when available.

        Returns:
            The analysis service instance, or None if not set.

        """
        """Expose the underlying analysis service when available."""
        return self.analysis_service

    def evaluate_document(self, document: TherapyDocument) -> ComplianceResult:
        """Evaluates a given document against the loaded compliance rules.

        Args:
            document: The TherapyDocument object to evaluate.

        Returns:
            A ComplianceResult object containing the document and any compliance findings.

        """
        logger.info("Evaluating compliance for document %s", document.id)
        findings: list[ComplianceFinding] = []
        normalized_text = document.text.lower()

        for rule in self.rules:
            if not self._rule_matches_context(rule, document):
                continue

            if self._violates_rule(rule, normalized_text):
                findings.append(
                    ComplianceFinding(
                        rule=rule,
                        text_snippet=self._build_snippet(rule),
                        risk_level=rule.severity))

        result = ComplianceResult(
            document=document,
            findings=findings,
            is_compliant=not findings)
        logger.info(
            "Compliance evaluation for %s finished with %d findings",
            document.id,
            len(findings))
        return result

    def _default_rules(self) -> list[ComplianceRule]:
        """Loads a set of default Medicare Benefits Policy Manual compliance rules.

        These rules serve as a baseline for compliance checking when no specific
        rule set is provided.

        Returns:
            A list of default ComplianceRule objects.

        """
        """Load default Medicare Benefits Policy Manual compliance rules."""
        return [
            # High-priority Medicare compliance rules
            ComplianceRule(
                uri="rule://medicare/signature",
                severity="high",
                strict_severity="high",
                issue_title="Provider signature/date missing or incomplete",
                issue_detail="All therapy services must be signed and dated by the treating therapist with professional credentials. Missing signatures can result in claim denials.",
                issue_category="documentation",
                discipline="all",
                document_type="all",
                suggestion="Ensure all notes are signed with full name, credentials (PT, OT, SLP, etc.), and date. Use electronic signatures if available.",
                financial_impact=75,
                positive_keywords=[],  # Apply to all documents
                negative_keywords=["signature", "signed", "date", "credentials"]),
            ComplianceRule(
                uri="rule://medicare/medical_necessity",
                severity="high",
                strict_severity="high",
                issue_title="Medical necessity not clearly documented",
                issue_detail="Services must be medically necessary and skilled in nature. Documentation must justify why professional therapy services are required.",
                issue_category="medical_necessity",
                discipline="all",
                document_type="all",
                suggestion="Document specific skilled interventions, link treatments to functional limitations, and explain why therapy expertise is required.",
                financial_impact=100,
                positive_keywords=["treatment", "therapy", "intervention"],
                negative_keywords=["skilled", "medical necessity", "professional", "expertise"]),
            ComplianceRule(
                uri="rule://medicare/goals",
                severity="medium",
                strict_severity="medium",
                issue_title="Goals not specific, measurable, or time-bound",
                issue_detail="Treatment goals must be SMART (Specific, Measurable, Achievable, Relevant, Time-bound) to demonstrate medical necessity and progress.",
                issue_category="goals",
                discipline="all",
                document_type="all",
                suggestion="Use objective measurements, functional outcomes, and specific timeframes. Example: 'Patient will increase right shoulder flexion from 90° to 120° within 3 weeks.'",
                financial_impact=50,
                positive_keywords=["goal", "objective", "outcome"],
                negative_keywords=["measurable", "specific", "timeframe", "weeks", "days"]),
            ComplianceRule(
                uri="rule://medicare/plan_of_care",
                severity="high",
                strict_severity="high",
                issue_title="Physician plan of care missing or incomplete",
                issue_detail="All therapy services require a physician's plan of care with specific frequency, duration, and treatment goals.",
                issue_category="plan_of_care",
                discipline="all",
                document_type="all",
                suggestion="Ensure physician plan of care includes specific frequency (e.g., 3x/week), duration (e.g., 4 weeks), and treatment focus areas.",
                financial_impact=100,
                positive_keywords=["therapy", "treatment"],
                negative_keywords=["physician", "plan of care", "frequency", "duration"]),
            ComplianceRule(
                uri="rule://medicare/progress_documentation",
                severity="medium",
                strict_severity="medium",
                issue_title="Progress documentation insufficient or missing",
                issue_detail="Progress notes must document objective improvements, response to treatment, and functional changes at least every 10 treatment days.",
                issue_category="progress",
                discipline="all",
                document_type="progress note",
                suggestion="Include objective measurements, functional improvements, patient response to treatment, and any barriers to progress.",
                financial_impact=40,
                positive_keywords=["progress", "improvement", "response"],
                negative_keywords=["objective", "measurement", "functional", "improvement"]),
            ComplianceRule(
                uri="rule://medicare/functional_outcomes",
                severity="medium",
                strict_severity="medium",
                issue_title="Functional outcomes not documented",
                issue_detail="Documentation must demonstrate how therapy services improve patient's functional abilities and quality of life.",
                issue_category="functional_outcomes",
                discipline="all",
                document_type="all",
                suggestion="Link all interventions to functional improvements in ADLs, mobility, communication, or work-related tasks.",
                financial_impact=60,
                positive_keywords=["intervention", "treatment"],
                negative_keywords=["functional", "ADL", "mobility", "independence"]),
        ]

    @staticmethod
    def _rule_matches_context(rule: ComplianceRule, document: TherapyDocument) -> bool:
        """Checks if a given rule is applicable to the document's discipline and type.

        Args:
            rule: The ComplianceRule to check.
            document: The TherapyDocument to check against.

        Returns:
            True if the rule applies to the document's context, False otherwise.

        """
        # Check if rule applies to this discipline
        discipline_ok = (
            rule.discipline.lower() in {"any", "*", "all"} or rule.discipline.lower() == document.discipline.lower()
        )

        # Check if rule applies to this document type
        doc_type_ok = (
            rule.document_type.lower() in {"any", "*", "all"}
            or rule.document_type.lower() == document.document_type.lower()
        )

        return discipline_ok and doc_type_ok

    @staticmethod
    def _contains_any(keywords: Iterable[str], text: str) -> bool:
        """Checks if the given text contains any of the specified keywords (case-insensitive).

        Args:
            keywords: An iterable of keywords to search for.
            text: The text to search within.

        Returns:
            True if any keyword is found in the text, False otherwise.

        """
        return any(keyword.lower() in text for keyword in keywords)

    def _violates_rule(self, rule: ComplianceRule, normalized_text: str) -> bool:
        """Determines if the document text violates a given compliance rule.

        A rule is violated if:
        - It has positive keywords and none of them are found in the text, OR
        - It has negative keywords and all of them are found in the text.

        Args:
            rule: The ComplianceRule to check.
            normalized_text: The document text, already normalized (e.g., lowercase).

        Returns:
            True if the rule is violated, False otherwise.

        """
        has_positive_context = True
        if rule.positive_keywords:
            has_positive_context = self._contains_any(
                rule.positive_keywords,
                normalized_text)

        if not has_positive_context:
            return False

        if not rule.negative_keywords:
            return True

        has_required_terms = self._contains_any(rule.negative_keywords, normalized_text)
        return not has_required_terms

    @staticmethod
    def _build_snippet(rule: ComplianceRule) -> str:
        """Constructs a text snippet explaining the rule violation.

        Args:
            rule: The ComplianceRule that was violated.

        Returns:
            A string snippet describing the violation.

        """
        if rule.negative_keywords:
            return "Required documentation terms were not detected: " + ", ".join(
                rule.negative_keywords)
        if rule.positive_keywords:
            return "Expected keywords were missing: " + ", ".join(
                rule.positive_keywords)
        return "Rule conditions not met by the document content."

    @staticmethod
    def to_dict(result: ComplianceResult) -> dict:
        """Converts a ComplianceResult object into a dictionary.

        Args:
            result: The ComplianceResult object to convert.

        Returns:
            A dictionary representation of the ComplianceResult.

        """
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
