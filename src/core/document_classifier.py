import os
from src.core.llm_service import LLMService
from src.utils.prompt_manager import PromptManager

class DocumentClassifier:
    """
    Uses an LLM to classify the type of a clinical document.
    """
    def __init__(self):
        self.llm_service = LLMService()
        # The prompt manager will find the prompt in the /prompts directory
        self.prompt_manager = PromptManager('classify_document_prompt.txt')

    def classify_document(self, text: str) -> str:
        """
        Classifies the document by feeding its content to an LLM
        with a specialized prompt.
        """
        # Truncate the text to avoid sending too much data to the LLM
        truncated_text = text[:2000]

        prompt = self.prompt_manager.get_prompt(document_text=truncated_text)

        # Call the LLM to get the classification
        response = self.llm_service.make_request(prompt)

        # Clean up the response to get a single, clean classification
        # e.g., "Progress Note" from a response like "The document is a: Progress Note."
        classification = response.strip().split(':')[-1].strip().replace('.', '')

        return classification if classification else "Unknown"