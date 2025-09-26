import logging
from typing import Dict, Any
from transformers import pipeline

logger = logging.getLogger(__name__)

class FactCheckerService:
    """
    A service to validate the plausibility of LLM findings using a smaller, specialized model.
    """
    def __init__(self, model_name: str, **kwargs):
        """
        Initializes the Fact-Checking Service.
        """
        self.model_name = model_name
        self.pipeline = None
        try:
            logger.info(f"Loading Fact-Checker model: {self.model_name}")
            self.pipeline = pipeline("text2text-generation", model=self.model_name)
            logger.info("Fact-Checker model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Fact-Checker model {self.model_name}: {e}", exc_info=True)

    def is_finding_plausible(self, finding: Dict, rule: Dict) -> bool:
        """
        Checks if a given compliance finding is plausible based on the rule it violated.
        """
        if not self.pipeline:
            logger.warning("Fact-Checker model not loaded. Skipping validation.")
            return True # Default to plausible if the checker is not available

        try:
            prompt = f"""
            Rule: {rule.get('name', '')} - {rule.get('content', '')}
            Problematic Text: "{finding.get('text', '')}"
            
            Question: Based on the rule, is it plausible that the problematic text represents a compliance issue? Answer only with 'Yes' or 'No'.
            
            Answer:
            """

            response = self.pipeline(prompt, max_length=10)[0]['generated_text']

            if 'yes' in response.lower():
                return True
            return False

        except Exception as e:
            logger.error(f"Error during fact-checking: {e}", exc_info=True)
            return True # Default to plausible in case of an error