"""AI Model Resource Factory for Therapy Compliance Analyzer

This module provides resource factories for AI models, enabling efficient
pooling and lifecycle management of expensive AI resources.
"""

import logging

import torch
from sentence_transformers import SentenceTransformer

from .llm_service import LLMService
from .resource_pool import ResourceFactory

logger = logging.getLogger(__name__)


class LLMResourceFactory(ResourceFactory[LLMService]):
    """Factory for creating and managing LLM service instances."""

    def __init__(self, model_name: str = "microsoft/DialoGPT-medium", device: str = "auto"):
        self.model_name = model_name
        self.device = self._determine_device(device)
        self._model_size_mb = 0

    def create_resource(self, resource_id: str) -> LLMService:
        """Create a new LLM service instance."""
        try:
            logger.info("Creating LLM resource %s with model {self.model_name}", resource_id)

            # Create LLM service with specified model
            llm_service = LLMService()

            # Initialize the model (this will load it into memory)
            # The actual model loading is handled by LLMService internally

            # Estimate model size for resource tracking
            self._model_size_mb = self._estimate_model_size()

            logger.info("LLM resource %s created successfully", resource_id)
            return llm_service

        except Exception:
            logger.exception("Failed to create LLM resource %s: {e}", resource_id)
            raise

    def validate_resource(self, resource: LLMService) -> bool:
        """Validate that an LLM service is still usable."""
        try:
            # Simple validation - check if we can generate a short response
            test_prompt = "Test"
            response = resource.generate_response(test_prompt, max_length=10)
            return response is not None and len(response.strip()) > 0

        except (ValueError, TypeError, AttributeError) as e:
            logger.warning("LLM resource validation failed: %s", e)
            return False

    def dispose_resource(self, resource: LLMService) -> None:
        """Dispose of an LLM service properly."""
        try:
            # Clear any cached models or data
            if hasattr(resource, "_model") and resource._model is not None:
                del resource._model

            if hasattr(resource, "_tokenizer") and resource._tokenizer is not None:
                del resource._tokenizer

            # Force garbage collection for GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.debug("LLM resource disposed successfully")

        except (ImportError, ModuleNotFoundError, AttributeError) as e:
            logger.exception("Error disposing LLM resource: %s", e)

    def get_resource_size(self, resource: LLMService) -> int:
        """Get estimated memory size of LLM resource in bytes."""
        return self._model_size_mb * 1024 * 1024

    def _determine_device(self, device: str) -> str:
        """Determine the best device for model execution."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
            return "cpu"
        return device

    def _estimate_model_size(self) -> int:
        """Estimate model size in MB based on model name."""
        # Rough estimates based on common model sizes
        size_estimates = {
            "microsoft/DialoGPT-small": 117,
            "microsoft/DialoGPT-medium": 345,
            "microsoft/DialoGPT-large": 762,
            "gpt2": 548,
            "gpt2-medium": 1558,
            "gpt2-large": 3200,
            "distilbert-base-uncased": 268,
            "bert-base-uncased": 440,
        }

        return size_estimates.get(self.model_name, 500)  # Default 500MB


class EmbeddingModelResourceFactory(ResourceFactory[SentenceTransformer]):
    """Factory for creating and managing sentence transformer models."""

    def initialize(self) -> None:
        """Initialize model resource factories."""
        if self._initialized:
            return

        try:
            # Create factories for common models
            self._factories["llm"] = LLMResourceFactory()
            self._factories["embeddings"] = EmbeddingModelResourceFactory()
            self._factories["tokenizer"] = TokenizerResourceFactory("microsoft/DialoGPT-medium")

            self._initialized = True
            logger.info("Model resource manager initialized")

        except (RuntimeError, AttributeError) as e:
            logger.exception("Failed to initialize model resource manager: %s", e)
            raise

    def get_factory(self, model_type: str) -> ResourceFactory | None:
        """Get a resource factory by type."""
        if not self._initialized:
            self.initialize()

        return self._factories.get(model_type)

    def register_factory(self, model_type: str, factory: ResourceFactory) -> None:
        """Register a custom resource factory."""
        self._factories[model_type] = factory
        logger.info("Registered custom factory for model type: %s", model_type)

    def get_available_types(self) -> list[str]:
        """Get list of available model types."""
        return list(self._factories.keys())


# Global model resource manager instance
# Global model resource manager instance
# Global model resource manager instance
model_resource_manager = ModelResourceManager()
