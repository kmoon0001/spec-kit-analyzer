import logging
from typing import Dict, Any, Optional

# Move import to top level for patching
from ctransformers import AutoModelForCausalLM

logger = logging.getLogger(__name__)

class LLMService:
    """Service wrapper around a local GGUF model loaded via ctransformers."""

    def __init__(
        self,
        model_repo_id: str,
        model_filename: str,
        llm_settings: Optional[Dict[str, Any]] = None,
    ):
        """Initializes the LLM Service and lazy-loads the model."""
        self.model_repo_id = model_repo_id
        self.model_filename = model_filename
        self.settings = llm_settings or {}
        self.generation_params = self.settings.get("generation_params", {}).copy()
        self.llm = None
        self._load_model()

    def _load_model(self):
        """Loads the GGUF model from the specified path."""
        try:
            logger.info(f"Loading LLM: {self.model_repo_id}/{self.model_filename}")
            self.llm = AutoModelForCausalLM.from_pretrained(
                self.model_repo_id,
                model_file=self.model_filename,
                model_type=self.settings.get("model_type", "llama"),
                context_length=self.settings.get("context_length", 2048),
            )
            logger.info("LLM loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load LLM: {e}")
            self.llm = None

    def is_ready(self) -> bool:
        """Check if the LLM is loaded and ready."""
        return self.llm is not None

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using the loaded LLM."""
        if not self.is_ready():
            return "LLM not available."

        try:
            gen_params = self.settings.get("generation_params", {}).copy()
            gen_params.update(kwargs)

            response = self.llm(prompt, **gen_params)
            return response
        except Exception as e:
            logger.error(f"Error during text generation: {e}")
            return "An error occurred during text generation."