import logging
from typing import Any

import requests
from requests.exceptions import HTTPError

from .llm_service import LLMService
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class NLGService:
    """A service for generating Natural Language content, such as personalized tips."""

    def __init__(self, llm_service: LLMService, prompt_template_path: str):
        """Initializes the NLGService.

        Args:
            llm_service: An instance of the LLMService to use for generation.
            prompt_template_path: The path to the prompt template for generating tips.

        """
        self.llm_service = llm_service
        # Extract just the filename from the path for PromptManager
        import os

        template_name = os.path.basename(prompt_template_path)
        self.prompt_manager = PromptManager(template_name=template_name)

    def generate_personalized_tip(self, finding: dict[str, Any]) -> str:
        """Generates a personalized improvement tip for a given compliance finding.

        Args:
            finding: A dictionary representing a single compliance finding.

        Returns:
            A string containing the generated tip.

        """
        if not self.llm_service.is_ready():
            logger.warning("LLM not available, returning generic tip.")
            return finding.get("suggestion", "No tip available.")

        try:
            # Prepare variables with safe defaults
            issue_title = finding.get("issue_title") or finding.get("title") or "N/A"
            issue_detail = (
                finding.get("issue_detail") or finding.get("description") or "N/A"
            )
            text_snippet = (
                finding.get("text")
                or finding.get("text_snippet")
                or finding.get("problematic_text")
                or "N/A"
            )

            # First attempt: common variables
            try:
                prompt = self.prompt_manager.build_prompt(
                    issue_title=issue_title,
                    issue_detail=issue_detail,
                    text=text_snippet,
                )
            except KeyError:
                # Some templates expect a 'findings' variable; synthesize a compact string
                synthesized_findings = f"Title: {issue_title}\nDetail: {issue_detail}\nText: {text_snippet}"
                prompt = self.prompt_manager.build_prompt(
                    findings=synthesized_findings,
                    issue_title=issue_title,
                    issue_detail=issue_detail,
                    text=text_snippet,
                )

            # Generate the tip using the LLM
            generated_tip = self.llm_service.generate_analysis(prompt)
            return (
                generated_tip or finding.get("suggestion", "")
            ).strip() or finding.get("suggestion", "No tip available.")

        except (
            requests.RequestException,
            ConnectionError,
            TimeoutError,
            HTTPError,
        ) as e:
            logger.exception("Error generating personalized tip: %s", e)
            return finding.get("suggestion", "Error generating tip.")
        except (
            Exception
        ) as e:  # Defensive catch to prevent GUI/API failures on unexpected template fields
            logger.exception("NLG generation failed; falling back to suggestion: %s", e)
            return finding.get("suggestion", "No tip available.")
