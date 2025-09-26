import logging
import json
from typing import Dict, Any

from .llm_service import LLMService
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class LLMComplianceAnalyzer:
    """
    A service that orchestrates the core compliance analysis of a document
    using a Large Language Model.
    """

    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def analyze_document(self, document_text: str, context: str) -> Dict[str, Any]:
        """
        Analyzes a document against a given context (e.g., retrieved compliance rules).
        """
        prompt = self.prompt_manager.build_prompt(context=context, document_text=document_text)
        if not prompt:
            logger.error("Prompt generation failed, aborting analysis.")
            return {"error": "Failed to generate a valid prompt for analysis."}

        raw_analysis = self._generate_analysis(prompt)
        return raw_analysis

    def _generate_analysis(self, prompt: str) -> Dict[str, Any]:
        """
        Calls the LLM service and robustly parses the JSON output.
        It handles cases where the JSON is embedded in markdown code blocks.
        """
        raw_output = self.llm_service.generate_analysis(prompt)
        json_str = ""
        try:
            # First, try to find a JSON block enclosed in markdown backticks
            if '```json' in raw_output:
                # Find the start of the JSON content after ```json
                start = raw_output.find('```json') + len('```json')
                # Find the end of the JSON block
                end = raw_output.rfind('```')
                # Extract the string in between
                json_str = raw_output[start:end].strip()
            else:
                # If no markdown block is found, fall back to finding the first '{' and last '}'
                start = raw_output.find('{')
                end = raw_output.rfind('}')
                if start != -1 and end != -1:
                    json_str = raw_output[start:end + 1]
                else:
                    # If no JSON object can be found at all, raise an error
                    logger.error("No JSON object found in LLM output.")
                    raise json.JSONDecodeError("No JSON object found in the output.", raw_output, 0)

            # Attempt to load the extracted string as JSON
            return json.loads(json_str)

        except json.JSONDecodeError:
            logger.error(f"Failed to decode LLM output into JSON. Raw output:\n{raw_output}", exc_info=True)
            return {"error": "Invalid JSON output from LLM", "raw_output": raw_output}