class RiskScoringService:
    """
    A service to calculate a compliance score based on the severity of findings.
    """
    @staticmethod
    def calculate_compliance_score(findings: list) -> int:
        """
        Calculates a compliance score from 1 to 100.
        A higher score means better compliance.
        """
        if not findings:
            return 100

        risk_weights = {"High": 10, "Medium": 5, "Low": 2}
        max_possible_risk = 50  # An arbitrary ceiling for risk score

        total_risk_score = sum(risk_weights.get(finding.get("risk", "Low"), 1) for finding in findings)

        # Normalize the risk score to a 0-1 scale and then map to 0-100
        normalized_risk = min(total_risk_score / max_possible_risk, 1.0)

        # Invert so that high risk -> low compliance score
        compliance_score = 100 - (normalized_risk * 100)

        return int(compliance_score)