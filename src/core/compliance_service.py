from typing import List, Dict, Optional
from src.core.models import TherapyDocument, ComplianceRule, ComplianceFinding, ComplianceResult
from src.core.rule_loader import RuleLoader

class ComplianceService:
    """
    A service to evaluate therapy documents against a set of compliance rules.
    """

    def __init__(self, rules: Optional[List[ComplianceRule]] = None, rules_directory: str = "src"):
        """
        Initializes the ComplianceService.
        If a list of rules is provided, it uses them directly.
        Otherwise, it loads them from the specified directory.
        """
        loaded_rules: List[ComplianceRule] = []
        if rules is not None:
            loaded_rules = rules
        else:
            loader = RuleLoader(rules_directory)
            loaded_rules = loader.load_rules()
        self._rules = self._organize_rules_by_discipline(loaded_rules)

    def _organize_rules_by_discipline(self, rules: List[ComplianceRule]) -> Dict[str, List[ComplianceRule]]:
        """
        Organizes rules by discipline for efficient retrieval.
        """
        organized_rules = {}
        for rule in rules:
            if rule.discipline not in organized_rules:
                organized_rules[rule.discipline] = []
            organized_rules[rule.discipline].append(rule)
        return organized_rules

    def evaluate_document(self, document: TherapyDocument) -> ComplianceResult:
        """
        Evaluates a therapy document for compliance.
        """
        findings = []
        rules_for_discipline = self._rules.get(document.discipline, [])

        for rule in rules_for_discipline:
            if self._is_rule_applicable(rule, document):
                findings.extend(self._check_rule(rule, document))

        is_compliant = not bool(findings)
        return ComplianceResult(document=document, findings=findings, is_compliant=is_compliant)

    def _is_rule_applicable(self, rule: ComplianceRule, document: TherapyDocument) -> bool:
        """
        Checks if a rule is applicable to the given document.
        """
        # For now, we assume a rule is applicable if the document type matches.
        # This can be extended with more complex logic.
        return rule.document_type.lower() == 'any' or rule.document_type.lower() == document.document_type.lower()

    def _check_rule(self, rule: ComplianceRule, document: TherapyDocument) -> List[ComplianceFinding]:
        """
        Checks a single rule against the document based on its keyword configuration.
        """
        doc_text_lower = document.text.lower()
        findings = []

        # Check for presence of positive keywords
        found_positive = False
        if rule.positive_keywords:
            for keyword in rule.positive_keywords:
                if keyword.lower() in doc_text_lower:
                    found_positive = True
                    break
        else:
            # If no positive keywords, we treat this condition as met.
            found_positive = True

        if not found_positive:
            return []  # Rule requires positive keywords, and none were found.

        # Check for presence of negative keywords
        found_negative = False
        if rule.negative_keywords:
            for keyword in rule.negative_keywords:
                if keyword.lower() in doc_text_lower:
                    found_negative = True
                    break

        # Determine if a finding should be created based on the logic.
        # Case 1: Rule has positive keywords. Finding if positive found AND negative NOT found.
        if rule.positive_keywords:
            if not found_negative:
                keyword_for_snippet = next((k for k in rule.positive_keywords if k.lower() in doc_text_lower), "")
                findings.append(ComplianceFinding(
                    rule=rule,
                    text_snippet=self._find_snippet(document.text, keyword_for_snippet),
                    risk_level=rule.severity
                ))
        # Case 2: Rule has ONLY negative keywords. These are "required" keywords.
        # Finding if NONE of them are found.
        elif rule.negative_keywords and not rule.positive_keywords:
            if not found_negative:
                findings.append(ComplianceFinding(
                    rule=rule,
                    text_snippet="Document-wide: Required content may be missing.",
                    risk_level=rule.severity
                ))

        return findings

    def _find_snippet(self, text: str, keyword: str, window: int = 50) -> str:
        """
        Finds a snippet of text around a keyword.
        """
        pos = text.lower().find(keyword.lower())
        if pos == -1:
            return ""
        start = max(0, pos - window)
        end = min(len(text), pos + len(keyword) + window)
        return text[start:end]