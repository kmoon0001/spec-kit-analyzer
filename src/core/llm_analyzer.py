import json
import logging
from typing import List, Dict

from src.core.llm_service import LLMService
from src.utils.prompt_manager import PromptManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """
    This class is responsible for the core analysis of a document
    using a Large Language Model.
    """
    def __init__(self):
        """
        Initializes the LLMAnalyzer with a reusable LLM service and a prompt manager.
        """
        self.llm_service = LLMService()
        self.prompt_manager = PromptManager('analysis_prompt.txt')

    def get_embedding(self, text: str) -> bytes:
        """
        Generates and returns the embedding for a given text.
        """
        return self.llm_service.get_embedding(text)

    def analyze(self, document_text: str, guidelines: List[str]) -> Dict:
        """
        Analyzes the document against a set of guidelines using the LLM.

        Args:
            document_text: The full text of the document to analyze.
            guidelines: A list of relevant guidelines retrieved from the RAG pipeline.

        Returns:
            A dictionary containing the structured analysis results from the LLM.
        """
        # Join the guidelines into a single string for the prompt
        guidelines_str = "\n- ".join(guidelines)

        # Get the formatted prompt from the manager
        prompt = self.prompt_manager.get_prompt(
            document_text=document_text,
            guidelines=guidelines_str
        )

        # Make the request to the LLM
        raw_response = self.llm_service.make_request(prompt)

        # Parse the JSON output from the LLM
        return self._parse_llm_response(raw_response)

    def _parse_llm_response(self, response: str) -> Dict:
        """
        Parses the raw JSON string from the LLM into a Python dictionary.
        Includes robust error handling for malformed JSON.
        """
        try:
            # Find the start and end of the JSON block
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                raise json.JSONDecodeError("No JSON object found in response.", response, 0)

            json_str = response[json_start:json_end]
            return json.loads(json_str)

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from LLM response: {e}")
            logger.error(f"Raw LLM Response:\n{response}")
            # Return a structured error message
            return {
                "error": "Failed to parse LLM response as JSON.",
                "raw_response": response
            }