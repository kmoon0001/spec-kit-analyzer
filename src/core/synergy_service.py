"""
Synergy Service - Powers the Synergy Session feature by combining AI phrase
generation with targeted guideline retrieval for complex clinical scenarios.
"""
import logging
from typing import Dict, Any, List

from .llm_service import LLMService
from .hybrid_retriever import HybridRetriever
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class SynergyService:
    """
    Orchestrates the process of generating documentation suggestions and
    retrieving relevant guidelines for a user-described clinical scenario.
    """

    def __init__(
        self,
        llm_service: LLMService,
        retriever: HybridRetriever,
        prompt_template_path: str,
    ):
        self.llm_service = llm_service
        self.retriever = retriever
        self.prompt_manager = PromptManager(template_path=prompt_template_path)
        logger.info("SynergyService initialized.")

    async def generate_synergy_data(self, scenario: str, discipline: str = "Physical Therapy") -> Dict[str, Any]:
        """
        Generates synergy data for a given scenario.

        Args:
            scenario: The user-described complex clinical scenario.
            discipline: The clinical discipline for context.

        Returns:
            A dictionary containing AI-generated suggestions and retrieved guidelines.
        """
        if not self.llm_service.is_ready():
            logger.warning("LLM service not ready for Synergy Session.")
            return {"error": "The AI model is not available. Please try again later."}

        try:
            # 1. Retrieve relevant guidelines
            # We use the scenario itself as the search query.
            retrieved_guidelines = await self.retriever.retrieve(
                scenario, category_filter=discipline, top_k=4
            )
            logger.info(f"Retrieved {len(retrieved_guidelines)} guidelines for synergy session.")

            # 2. Build the prompt for the AI
            formatted_guidelines = self._format_guidelines_for_prompt(retrieved_guidelines)
            prompt = self.prompt_manager.build_prompt(
                scenario=scenario, guidelines=formatted_guidelines
            )

            # 3. Generate suggestions from the AI
            raw_suggestions = self.llm_service.generate_analysis(prompt)
            suggestions_list = self._parse_suggestions(raw_suggestions)

            logger.info("Successfully generated synergy data.")
            return {
                "suggestions": suggestions_list,
                "guidelines": retrieved_guidelines,
            }

        except Exception as e:
            logger.error(f"Error during synergy session generation: {e}", exc_info=True)
            return {"error": f"An unexpected error occurred: {e}"}

    @staticmethod
    def _format_guidelines_for_prompt(guidelines: List[Dict[str, Any]]) -> str:
        """Formats a list of guideline documents into a string for the prompt."""
        if not guidelines:
            return "No specific guidelines were retrieved. Rely on general clinical best practices."

        formatted_list = []
        for rule in guidelines:
            text = f"- Rule: {rule.get('name', 'N/A')}\n  Detail: {rule.get('content', 'N/A')}"
            formatted_list.append(text)
        return "\n".join(formatted_list)

    @staticmethod
    def _parse_suggestions(raw_text: str) -> List[str]:
        """Parses the AI's raw text output into a clean list of suggestions."""
        if not raw_text:
            return []
        # Split by newlines and remove any leading/trailing whitespace or list markers
        suggestions = [
            line.strip().lstrip("-*• ").strip()
            for line in raw_text.strip().split("\n")
            if line.strip()
        ]
        return suggestions