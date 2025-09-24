from typing import Dict, Any, List

class ExplanationEngine:
    def add_explanations(self, analysis: Dict[str, Any], rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enriches the analysis findings with detailed explanations from the retrieved rules.
        """
        rules_by_id = {rule.get('id'): rule for rule in rules}

        findings = analysis.get("findings", [])
        if not findings:
            return analysis

        for finding in findings:
            rule_id = finding.get("rule_id")
            if rule_id and rule_id in rules_by_id:
                rule = rules_by_id[rule_id]
                finding["explanation"] = {
                    "detail": f"This finding relates to the guideline: '{rule.get('issue_title', 'N/A')}'.",
                    "guideline_text": rule.get('issue_detail', 'No details available.'),
                    "suggestion": rule.get('suggestion', 'No suggestion available.')
                }
            else:
                finding["explanation"] = {
                    "detail": "This finding was identified by the AI model based on general compliance principles, but it does not directly correspond to a specific, retrieved guideline.",
                    "guideline_text": "N/A",
                    "suggestion": finding.get("suggestion", "No specific suggestion available.")
                }

        analysis["findings"] = findings
        return analysis