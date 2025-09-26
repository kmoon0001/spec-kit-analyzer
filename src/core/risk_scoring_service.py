from typing import List, Dict, Any

class RiskScoringService:
    """
    Calculates a compliance score based on a list of findings.
    """
    def __init__(self):
        self.risk_weights = {
            "High": 15,
            "Medium": 5,
            "Low": 1,
        }
        self.base_score = 100

    def calculate_compliance_score(self, findings: List[Dict[str, Any]]) -> int:
        """
        Calculates a compliance score by subtracting points for each finding
        based on its risk level.
        """
        if not findings:
            return self.base_score

        total_deduction = 0
        for finding in findings:
            risk_level = finding.get("risk", "Low")
            total_deduction += self.risk_weights.get(risk_level, 1)

        final_score = self.base_score - total_deduction
        return max(0, final_score)