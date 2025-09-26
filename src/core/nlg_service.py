from typing import Dict, Any

class NLGService:
    """
    A mock service for Natural Language Generation (NLG) to generate personalized tips.
    """
    def __init__(self, llm_service: Any, prompt_template_path: str):
        """Initializes the mock NLGService."""
        self.llm_service = llm_service
        self.prompt_template_path = prompt_template_path

    @staticmethod
    def generate_personalized_tip(finding: Dict[str, Any]) -> str:
        """Generates a mock personalized tip for a given compliance finding."""
        return f"This is a mock tip for rule: {finding.get('rule_id', 'N/A')}"
