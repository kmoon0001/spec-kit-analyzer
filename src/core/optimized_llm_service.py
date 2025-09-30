import logging
from typing import Any, Dict, Optional

from .llm_service import LLMService

logger = logging.getLogger(__name__)


class OptimizedLLMService(LLMService):
    """An optimized LLM service that might use a different model or fine-tuning."""

    def __init__(
        self,
        model_repo_id: str,
        model_filename: str,
        llm_settings: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(model_repo_id, model_filename, llm_settings)
        logger.info("Initialized OptimizedLLMService.")

    def get_sentence_transformer_model(self):
        """Lazy-loads and returns a SentenceTransformer model."""
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer("all-MiniLM-L6-v2")

    def generate_embedding(self, text: str) -> Any:
        """Generates a document embedding using a sentence transformer."""
        model = self.get_sentence_transformer_model()
        return model.encode(text)
