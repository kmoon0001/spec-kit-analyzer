import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class RiskScoringService:
    """
    Calculates a risk-based compliance score based on a list of findings.
    """

    def __init__(self):
        """
        Initializes the RiskScoringService with predefined weights.
        """
        self.severity_weights = {
            "high": 15,
            "medium": 7,
            "low": 2,
            "default": 5 # A default penalty for findings with no severity
        }

    def calculate_compliance_score(self, findings: List[Dict[str, Any]]) -> int:
        """
        Calculates a compliance score based on severity and financial impact.

        Args:
            findings: A list of finding dictionaries from the analysis.

        Returns:
            An integer compliance score between 0 and 100.
        """
        total_penalty = 0
        
        if not findings:
            return 100

        for finding in findings:
            penalty = 0
            
            # 1. Calculate penalty from severity
            severity = finding.get("severity", "default").lower()
            penalty += self.severity_weights.get(severity, self.severity_weights["default"])
            
            # 2. Add a penalty based on financial impact
            # This is a simple model; it can be made more complex.
            # For example, adding 1 point for every $100 of impact.
            financial_impact = finding.get("financial_impact", 0)
            if isinstance(financial_impact, (int, float)):
                penalty += financial_impact / 100.0

            total_penalty += penalty

        # The final score is 100 minus the total penalty, with a floor of 0.
        final_score = max(0, 100 - int(total_penalty))
        
        logger.info(f"Calculated compliance score: {final_score} based on {len(findings)} findings.")
        return final_score
