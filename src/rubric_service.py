<<<<<<< HEAD
class ComplianceRule:
<<<<<<< HEAD
    def __init__(self, rule_id: str, description: str):
        self.rule_id = rule_id
        self.description = description
||||||| c46cdd8
    """
    A mock class to represent a compliance rule.
    """
    def __init__(self,
                 uri: str,
                 severity: str,
                 strict_severity: str,
                 issue_title: str,
                 issue_detail: str,
                 issue_category: str,
                 discipline: str,
                 document_type: str,
                 suggestion: str,
                 financial_impact: int,
                 positive_keywords: List[str],
                 negative_keywords: List[str]):
        self.uri = uri
        self.severity = severity
        self.strict_severity = strict_severity
        self.issue_title = issue_title
        self.issue_detail = issue_detail
        self.issue_category = issue_category
        self.discipline = discipline
        self.document_type = document_type
        self.suggestion = suggestion
        self.financial_impact = financial_impact
        self.positive_keywords = positive_keywords
        self.negative_keywords = negative_keywords
=======
    """A mock class to represent a compliance rule."""
    def __init__(self,
                 uri: str,
                 severity: str,
                 strict_severity: str,
                 issue_title: str,
                 issue_detail: str,
                 issue_category: str,
                 discipline: str,
                 document_type: str,
                 suggestion: str,
                 financial_impact: int,
                 positive_keywords: List[str],
                 negative_keywords: List[str]):
        self.uri = uri
        self.severity = severity
        self.strict_severity = strict_severity
        self.issue_title = issue_title
        self.issue_detail = issue_detail
        self.issue_category = issue_category
        self.discipline = discipline
        self.document_type = document_type
        self.suggestion = suggestion
        self.financial_impact = financial_impact
        self.positive_keywords = positive_keywords
        self.negative_keywords = negative_keywords
>>>>>>> origin/main
||||||| 278fb88
from typing import List

class ComplianceRule:
    """A mock class to represent a compliance rule."""
    def __init__(self,
                 uri: str,
                 severity: str,
                 strict_severity: str,
                 issue_title: str,
                 issue_detail: str,
                 issue_category: str,
                 discipline: str,
                 document_type: str,
                 suggestion: str,
                 financial_impact: int,
                 positive_keywords: List[str],
                 negative_keywords: List[str]):
        self.uri = uri
        self.severity = severity
        self.strict_severity = strict_severity
        self.issue_title = issue_title
        self.issue_detail = issue_detail
        self.issue_category = issue_category
        self.discipline = discipline
        self.document_type = document_type
        self.suggestion = suggestion
        self.financial_impact = financial_impact
        self.positive_keywords = positive_keywords
        self.negative_keywords = negative_keywords
=======
from typing import List

# The ComplianceRule class has been moved to src.core.models
# This file can be removed or repurposed. For now, it is left empty.
>>>>>>> origin/main
