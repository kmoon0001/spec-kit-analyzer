import logging
from typing import Any, Optional
from threading import Lock

from sentence_transformers import SentenceTransformer

from src.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    A thread-safe, lazy-loading service for generating sentence embeddings.

    This service manages a SentenceTransformer model, ensuring it is only loaded
    into memory when first needed. This is crucial for optimizing memory usage,
    especially in environments where embedding generation is not always required.
    """

    _model = None
    _lock = Lock()

    def __init__(self, model_name: Optional[str] = None):
        """
        Initializes the EmbeddingService configuration.

        Args:
            model_name (str | None): The name of the SentenceTransformer model to use.
        """
        settings = get_settings()
        default_model = getattr(settings.retrieval, "dense_model_name", None)
        if not default_model:
            default_model = getattr(settings.models, "retriever", "sentence-transformers/all-MiniLM-L6-v2")
        self.model_name = model_name or default_model
        self.is_loading = False

    def _load_model(self):
        """Loads the SentenceTransformer model."""
        if self._model:
            return

        self.is_loading = True
        try:
            logger.info("Loading sentence transformer model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
            logger.info("Sentence transformer model loaded successfully.")
        except Exception as e:
            logger.critical(
                "Fatal error: Failed to load sentence transformer model. %s",
                e,
                exc_info=True,
            )
            self._model = None
        finally:
            self.is_loading = False

    def _ensure_model_loaded(self):
        """Ensures the model is loaded before use in a thread-safe manner."""
        if self._model or self.is_loading:
            return
        with self._lock:
            # Double-check locking to prevent multiple threads from loading the model.
            if not self._model:
                self._load_model()

    def generate_embedding(self, text: str) -> Any:
        """
        Generates an embedding for the given text.

        The model is loaded on the first call to this method.

        Args:
            text (str): The input text to embed.

        Returns:
            The embedding vector, or None if the model failed to load.
        """
        self._ensure_model_loaded()
        if not self._model:
            logger.error(
                "Sentence transformer model is not available. Cannot generate embedding."
            )
            return None

        try:
            return self._model.encode(text)
        except Exception as e:
            logger.error(
                "An error occurred during embedding generation: %s", e, exc_info=True
            )
            return None
