"""
A mock implementation of the AnalysisService for testing and development purposes.
"""
from typing import Any, Dict, Optional


class MockAnalysisService:
    """A mock version of the AnalysisService that returns canned responses."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Accepts any arguments to match the real service's signature."""
        print("MockAnalysisService initialized")

    async def analyze_document(
        self,
        file_path: Optional[str] = None,
        discipline: str = "pt",
        analysis_mode: Optional[str] = None,
        document_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns a mock analysis result without performing any real analysis.
        """
        print(f"Mock analyze_document called for {file_path or 'text input'}")
        return {
            "analysis": {
                "findings": [
                    {
                        "issue_title": "Mock Issue",
                        "suggestion": "This is a mock suggestion.",
                        "confidence": 0.99,
                    }
                ]
            },
            "summary": "This is a mock summary.",
            "narrative_summary": "This is a mock narrative summary.",
            "bullet_highlights": ["Mock highlight 1", "Mock highlight 2"],
            "overall_confidence": 0.95,
            "discipline": discipline,
            "document_type": "Mock Note",
            "deterministic_checks": [],
        }
