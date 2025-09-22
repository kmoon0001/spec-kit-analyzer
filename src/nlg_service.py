# src/nlg_service.py
import logging
# from transformers import T5ForConditionalGeneration, T5Tokenizer

logger = logging.getLogger(__name__)

class NLGService:
    def __init__(self, model_name="t5-small"):
        """
        Initializes the NLG service. This is a placeholder implementation.
        """
        self.model = None
        self.tokenizer = None
        logger.info("NLGService initialized with placeholder implementation. No models will be loaded.")

    def generate_tip(self, prompt: str) -> str:
        """
        Placeholder for generating a personalized tip.
        """
        logger.info("NLGService.generate_tip called, but service is a placeholder.")
        return "NLG service is currently disabled."
