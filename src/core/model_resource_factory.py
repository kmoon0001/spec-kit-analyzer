"""
AI Model Resource Factory for Therapy Compliance Analyzer

This module provides resource factories for AI models, enabling efficient
pooling and lifecycle management of expensive AI resources.
"""

import logging
from typing import Dict, Optional
import torch
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer

from .resource_pool import ResourceFactory
from .llm_service import LLMService

logger = logging.getLogger(__name__)


class LLMResourceFactory(ResourceFactory[LLMService]):
    """Factory for creating and managing LLM service instances."""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium", 
                 device: str = "auto"):
        self.model_name = model_name
        self.device = self._determine_device(device)
        self._model_size_mb = 0
        
    def create_resource(self, resource_id: str) -> LLMService:
        """Create a new LLM service instance."""
        try:
            logger.info(f"Creating LLM resource {resource_id} with model {self.model_name}")
            
            # Create LLM service with specified model
            llm_service = LLMService()
            
            # Initialize the model (this will load it into memory)
            # The actual model loading is handled by LLMService internally
            
            # Estimate model size for resource tracking
            self._model_size_mb = self._estimate_model_size()
            
            logger.info(f"LLM resource {resource_id} created successfully")
            return llm_service
            
        except Exception as e:
            logger.error(f"Failed to create LLM resource {resource_id}: {e}")
            raise
    
    def validate_resource(self, resource: LLMService) -> bool:
        """Validate that an LLM service is still usable."""
        try:
            # Simple validation - check if we can generate a short response
            test_prompt = "Test"
            response = resource.generate_response(test_prompt, max_length=10)
            return response is not None and len(response.strip()) > 0
            
        except Exception as e:
            logger.warning(f"LLM resource validation failed: {e}")
            return False
    
    def dispose_resource(self, resource: LLMService) -> None:
        """Dispose of an LLM service properly."""
        try:
            # Clear any cached models or data
            if hasattr(resource, '_model') and resource._model is not None:
                del resource._model
            
            if hasattr(resource, '_tokenizer') and resource._tokenizer is not None:
                del resource._tokenizer
            
            # Force garbage collection for GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.debug("LLM resource disposed successfully")
            
        except Exception as e:
            logger.error(f"Error disposing LLM resource: {e}")
    
    def get_resource_size(self, resource: LLMService) -> int:
        """Get estimated memory size of LLM resource in bytes."""
        return self._model_size_mb * 1024 * 1024
    
    def _determine_device(self, device: str) -> str:
        """Determine the best device for model execution."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            else:
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
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "auto"):
        self.model_name = model_name
        self.device = self._determine_device(device)
        self._model_size_mb = 0
    
    def create_resource(self, resource_id: str) -> SentenceTransformer:
        """Create a new sentence transformer model."""
        try:
            logger.info(f"Creating embedding model resource {resource_id} with model {self.model_name}")
            
            model = SentenceTransformer(self.model_name, device=self.device)
            
            # Estimate model size
            self._model_size_mb = self._estimate_model_size()
            
            logger.info(f"Embedding model resource {resource_id} created successfully")
            return model
            
        except Exception as e:
            logger.error(f"Failed to create embedding model resource {resource_id}: {e}")
            raise
    
    def validate_resource(self, resource: SentenceTransformer) -> bool:
        """Validate that a sentence transformer model is still usable."""
        try:
            # Simple validation - encode a test sentence
            test_sentence = "This is a test sentence."
            embedding = resource.encode([test_sentence])
            return embedding is not None and len(embedding) > 0
            
        except Exception as e:
            logger.warning(f"Embedding model resource validation failed: {e}")
            return False
    
    def dispose_resource(self, resource: SentenceTransformer) -> None:
        """Dispose of a sentence transformer model properly."""
        try:
            # Clear model from memory
            if hasattr(resource, '_modules'):
                resource._modules.clear()
            
            # Force garbage collection for GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.debug("Embedding model resource disposed successfully")
            
        except Exception as e:
            logger.error(f"Error disposing embedding model resource: {e}")
    
    def get_resource_size(self, resource: SentenceTransformer) -> int:
        """Get estimated memory size of embedding model in bytes."""
        return self._model_size_mb * 1024 * 1024
    
    def _determine_device(self, device: str) -> str:
        """Determine the best device for model execution."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return device
    
    def _estimate_model_size(self) -> int:
        """Estimate model size in MB based on model name."""
        size_estimates = {
            "all-MiniLM-L6-v2": 90,
            "all-MiniLM-L12-v2": 120,
            "all-mpnet-base-v2": 420,
            "all-distilroberta-v1": 290,
            "paraphrase-MiniLM-L6-v2": 90,
            "paraphrase-mpnet-base-v2": 420,
        }
        
        return size_estimates.get(self.model_name, 200)  # Default 200MB


class TokenizerResourceFactory(ResourceFactory[AutoTokenizer]):
    """Factory for creating and managing tokenizer instances."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    def create_resource(self, resource_id: str) -> AutoTokenizer:
        """Create a new tokenizer instance."""
        try:
            logger.info(f"Creating tokenizer resource {resource_id} for model {self.model_name}")
            
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            logger.info(f"Tokenizer resource {resource_id} created successfully")
            return tokenizer
            
        except Exception as e:
            logger.error(f"Failed to create tokenizer resource {resource_id}: {e}")
            raise
    
    def validate_resource(self, resource: AutoTokenizer) -> bool:
        """Validate that a tokenizer is still usable."""
        try:
            # Simple validation - tokenize a test string
            test_text = "This is a test."
            tokens = resource.encode(test_text)
            return tokens is not None and len(tokens) > 0
            
        except Exception as e:
            logger.warning(f"Tokenizer resource validation failed: {e}")
            return False
    
    def dispose_resource(self, resource: AutoTokenizer) -> None:
        """Dispose of a tokenizer properly."""
        try:
            # Tokenizers are lightweight, just clear any cached data
            if hasattr(resource, '_tokenizer'):
                resource._tokenizer = None
            
            logger.debug("Tokenizer resource disposed successfully")
            
        except Exception as e:
            logger.error(f"Error disposing tokenizer resource: {e}")
    
    def get_resource_size(self, resource: AutoTokenizer) -> int:
        """Get estimated memory size of tokenizer in bytes."""
        return 50 * 1024 * 1024  # Estimate 50MB for tokenizers


class ModelResourceManager:
    """Manager for AI model resource pools."""
    
    def __init__(self):
        self._factories: Dict[str, ResourceFactory] = {}
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize model resource factories."""
        if self._initialized:
            return
        
        try:
            # Create factories for common models
            self._factories['llm'] = LLMResourceFactory()
            self._factories['embeddings'] = EmbeddingModelResourceFactory()
            self._factories['tokenizer'] = TokenizerResourceFactory("microsoft/DialoGPT-medium")
            
            self._initialized = True
            logger.info("Model resource manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize model resource manager: {e}")
            raise
    
    def get_factory(self, model_type: str) -> Optional[ResourceFactory]:
        """Get a resource factory by type."""
        if not self._initialized:
            self.initialize()
        
        return self._factories.get(model_type)
    
    def register_factory(self, model_type: str, factory: ResourceFactory) -> None:
        """Register a custom resource factory."""
        self._factories[model_type] = factory
        logger.info(f"Registered custom factory for model type: {model_type}")
    
    def get_available_types(self) -> list[str]:
        """Get list of available model types."""
        return list(self._factories.keys())


# Global model resource manager instance
model_resource_manager = ModelResourceManager()