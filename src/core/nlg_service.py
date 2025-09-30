import logging
from typing import Dict, Any

from .llm_service import LLMService
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class NLGService:
    """
    A service for generating Natural Language content, such as personalized tips.
    """

    def __init__(self, llm_service: LLMService, prompt_template_path: str):
        """
        Initializes the NLGService.

        Args:
            llm_service: An instance of the LLMService to use for generation.
            prompt_template_path: The path to the prompt template for generating tips.
        """
        self.llm_service = llm_service
        self.prompt_manager = PromptManager(template_path=prompt_template_path)

    def generate_personalized_tip(self, finding: Dict[str, Any]) -> str:
        """
        Generates a personalized improvement tip for a given compliance finding.

        Args:
            finding: A dictionary representing a single compliance finding.

        Returns:
            A string containing the generated tip.
        """
        if not self.llm_service.is_ready():
            logger.warning("LLM not available, returning generic tip.")
            return finding.get("suggestion", "No tip available.")

        try:
            # Build the prompt with the details of the finding
            prompt = self.prompt_manager.build_prompt(
                issue_title=finding.get("issue_title", "N/A"),
                issue_detail=finding.get("issue_detail", "N/A"),
                text=finding.get("text", "N/A"),
            )

            # Generate the tip using the LLM
            generated_tip = self.llm_service.generate_analysis(prompt)

            # Basic cleanup of the generated text can be done here if needed
            # For example, removing leading/trailing whitespace
            return generated_tip.strip()

        except Exception as e:
            logger.error(f"Error generating personalized tip: {e}")
            # Fallback to the original suggestion if generation fails
            return finding.get("suggestion", "Error generating tip.")
