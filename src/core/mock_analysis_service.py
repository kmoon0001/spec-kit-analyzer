import asyncio
from typing import Any, Dict

class MockAnalysisService:
    """
    A mock implementation of the AnalysisService that returns hard-coded data
    for testing the application's data flow without real AI models.
    """

    async def analyze_document(
        self,
        file_path: str,
        discipline: str,
        analysis_mode: str | None = None,
    ) -> Dict[str, Any]:
        """
        Returns a mock analysis result after a short delay to simulate processing.
        """
        print("--- Using MockAnalysisService ---")
        await asyncio.sleep(2)  # Simulate the time it takes for analysis

        mock_findings = [
            {
                "rule_id": "MOCK-001",
                "risk": "High",
                "personalized_tip": "Ensure all patient identifiers are removed from documentation before sharing.",
                "problematic_text": "Patient John Smith was seen today.",
                "confidence": 0.95,
                "issue_title": "PHI Leakage Detected",
            },
            {
                "rule_id": "MOCK-002",
                "risk": "Medium",
                "personalized_tip": "Goals should be measurable and time-bound. For example, 'Patient will be able to walk 50 feet independently within 2 weeks.'",
                "problematic_text": "Patient will improve walking.",
                "confidence": 0.88,
                "issue_title": "Vague Goal Setting",
            },
        ]

        mock_report = {
            "analysis": {
                "findings": mock_findings,
                "compliance_score": 75.0,
                "summary": "This is a mock analysis summary.",
                "discipline": discipline,
                "document_type": "Progress Note (Mocked)",
                "deterministic_checks": [],
                "narrative_summary": "Mock narrative summary highlighting key issues.",
                "bullet_highlights": [
                    "PHI Leakage Detected: Ensure all patient identifiers are removed.",
                    "Vague Goal Setting: Make goals measurable and time-bound.",
                ],
                "overall_confidence": 0.91,
            },
            "summary": "This is the main summary of the mock report.",
        }

        return mock_report