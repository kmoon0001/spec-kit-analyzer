import logging
import json
from typing import Dict, Any

from .llm_service import LLMService

logger = logging.getLogger(__name__)

class NLGService:
    """
    A service dedicated to generating Natural Language content, such as personalized tips,
    by formatting and sending requests to the core LLMService.
    """
    def __init__(self, llm_service: LLMService, prompt_template_path: str):
        """
        Initializes the NLGService.

        Args:
            llm_service: An instance of the core LLM service.
            prompt_template_path: The file path to the prompt template to use for generation.
        """
        self.llm_service = llm_service
        try:
            with open(prompt_template_path, 'r') as f:
                self.prompt_template = f.read()
            logger.info(f"NLG prompt template loaded successfully from {prompt_template_path}.")
        except FileNotFoundError:
            logger.error(f"FATAL: NLG prompt template not found at {prompt_template_path}.")
            raise
        except Exception as e:
            logger.error(f"FATAL: Failed to read NLG prompt template: {e}", exc_info=True)
            raise

    def generate_personalized_tip(self, finding: Dict[str, Any]) -> str:
        """
        Generates a personalized, actionable tip based on a single compliance finding.

        Args:
            finding: A dictionary representing a single compliance finding.

        Returns:
            A string containing the generated tip.
        """
        try:
            # Sanitize the finding dictionary for the prompt
            finding_json = json.dumps({
                "rule_id": finding.get("rule_id"),
                "severity": finding.get("severity"),
                "reason": finding.get("reason"),
                "quote": finding.get("quote")
            }, indent=2)

            prompt = self.prompt_template.format(finding_json=finding_json)

            logger.info("Generating personalized tip...")
            tip = self.llm_service.generate_analysis(prompt)

            # Clean up the output, removing potential conversational fluff from the LLM
            cleaned_tip = tip.strip().replace("Generated Tip:", "").strip()

            logger.info("Personalized tip generated successfully.")
            return cleaned_tip

        except Exception as e:
            logger.error(f"Failed to generate personalized tip: {e}", exc_info=True)
            return "Could not generate a tip due to an internal error."