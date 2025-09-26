import logging
import os
from unittest.mock import MagicMock
from typing import Dict, Any

logger = logging.getLogger(__name__)

# We conditionally import ctransformers only when not testing
if os.environ.get("PYTEST_RUNNING") != "1":
    from ctransformers import AutoModelForCausalLM

class LLMService:
    """
    A service class for interacting with a local, GGUF-quantized Large Language Model.
    """
    def __init__(self, model_repo_id: str, model_filename: str, llm_settings: Dict[str, Any]):
        """
        Initializes the LLMService. If the 'PYTEST_RUNNING' environment variable is set,
        it will use a MagicMock instead of loading a real model.
        """
        self.llm = None
        self.generation_params = llm_settings.get('generation_params', {})

        # Check for pytest environment to mock the model loading
        if os.environ.get("PYTEST_RUNNING") == "1":
            self.llm = MagicMock()
            # Mock the __call__ method to return a default JSON string
            self.llm.return_value = '{"mock_analysis": "This is a mock analysis from a mocked LLM."}'
            logger.info("LLMService initialized with a mock model for testing.")
            return

        logger.info(f"Loading GGUF model: {model_repo_id}/{model_filename}...")
        try:
            self.llm = AutoModelForCausalLM.from_pretrained(
                model_repo_id,
                model_file=model_filename,
                model_type=llm_settings.get('model_type', 'llama'),
                gpu_layers=llm_settings.get('gpu_layers', 0),
                context_length=llm_settings.get('context_length', 2048)
            )
            logger.info("GGUF Model loaded successfully.")
        except Exception as e:
            logger.error(f"FATAL: Failed to load GGUF model: {e}", exc_info=True)
            raise RuntimeError(f"Could not load LLM model: {e}") from e

    def is_ready(self) -> bool:
        """Checks if the model was loaded successfully."""
        return self.llm is not None

    def generate_analysis(self, prompt: str) -> str:
        """Generates a response by running the prompt through the loaded LLM."""
        if not self.is_ready():
            logger.error("LLM is not available. Cannot generate analysis.")
            return '{"error": "LLM not available"}'

        logger.info("Generating response with the LLM...")
        try:
            # Pass the generation parameters directly to the model call
            raw_text = self.llm(prompt, **self.generation_params)
            logger.info("LLM response generated successfully.")
            return raw_text
        except Exception as e:
            logger.error(f"Error during LLM generation: {e}", exc_info=True)
            return f'{{"error": "Failed to generate analysis: {e}"}}'