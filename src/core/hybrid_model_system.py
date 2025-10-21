"""
Hybrid Multi-Model System for Maximum Accuracy
Implements multiple language models with intelligent ensemble voting
"""

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
import json
import uuid
from pathlib import Path

from src.core.centralized_logging import get_logger, performance_tracker
from src.core.type_safety import Result, ErrorHandler

logger = get_logger(__name__)


class ModelType(Enum):
    """Types of models in the hybrid system."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SPECIALIZED = "specialized"
    FACT_CHECKER = "fact_checker"
    REASONING = "reasoning"
    VALIDATION = "validation"


class ModelStatus(Enum):
    """Model status in the system."""
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class ModelConfig:
    """Configuration for a model in the hybrid system."""
    model_id: str
    model_type: ModelType
    model_path: str
    model_name: str
    context_length: int
    max_tokens: int
    temperature: float
    top_p: float
    repeat_penalty: float
    ram_requirement_gb: float
    gpu_required: bool = False
    priority: int = 1  # 1 = highest priority
    enabled: bool = True
    fallback_models: List[str] = field(default_factory=list)
    specialization_tags: List[str] = field(default_factory=list)


@dataclass
class ModelResponse:
    """Response from a single model."""
    model_id: str
    model_type: ModelType
    response_text: str
    confidence: float
    processing_time_ms: float
    tokens_generated: int
    tokens_per_second: float
    memory_used_mb: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnsembleResult:
    """Result from ensemble voting."""
    final_response: str
    confidence: float
    agreement_score: float
    uncertainty_estimate: float
    method_used: str
    individual_responses: List[ModelResponse]
    weights_used: Dict[str, float]
    processing_time_ms: float
    consensus_reached: bool
    disagreement_details: List[Dict[str, Any]] = field(default_factory=list)


class HybridModelSystem:
    """
    Multi-model ensemble system for maximum accuracy.

    Supports multiple language models with intelligent ensemble voting,
    fallback mechanisms, and adaptive weighting based on performance.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the hybrid model system."""
        self.config_path = config_path or "config/hybrid_models.yaml"
        self.models: Dict[str, Any] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.model_status: Dict[str, ModelStatus] = {}
        self.performance_history: List[Dict[str, Any]] = []
        self.ensemble_weights: Dict[str, float] = {}
        self.fallback_chains: Dict[str, List[str]] = {}

        # Performance tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0.0
        self.memory_usage_mb = 0.0

        # Load configurations
        self._load_model_configurations()

        logger.info("HybridModelSystem initialized with %d models", len(self.model_configs))

    def _load_model_configurations(self) -> None:
        """Load model configurations from file."""
        try:
            # Default configurations for different model types
            default_configs = {
                "llama32_3b": ModelConfig(
                    model_id="llama32_3b",
                    model_type=ModelType.PRIMARY,
                    model_path="models/llama32-3b-instruct",
                    model_name="meta-llama/Llama-3.2-3B-Instruct",
                    context_length=128000,
                    max_tokens=2048,
                    temperature=0.1,
                    top_p=0.9,
                    repeat_penalty=1.1,
                    ram_requirement_gb=4.0,
                    gpu_required=False,
                    priority=1,
                    enabled=True,
                    specialization_tags=["general", "medical", "reasoning"]
                ),
                "qwen25_3b": ModelConfig(
                    model_id="qwen25_3b",
                    model_type=ModelType.SECONDARY,
                    model_path="models/qwen25-3b-instruct",
                    model_name="Qwen/Qwen2.5-3B-Instruct",
                    context_length=32000,
                    max_tokens=2048,
                    temperature=0.1,
                    top_p=0.9,
                    repeat_penalty=1.1,
                    ram_requirement_gb=4.0,
                    gpu_required=False,
                    priority=2,
                    enabled=True,
                    specialization_tags=["medical", "clinical", "reasoning"]
                ),
                "phi35_mini": ModelConfig(
                    model_id="phi35_mini",
                    model_type=ModelType.SPECIALIZED,
                    model_path="models/phi35-mini",
                    model_name="microsoft/Phi-3.5-mini-instruct",
                    context_length=128000,
                    max_tokens=2048,
                    temperature=0.1,
                    top_p=0.9,
                    repeat_penalty=1.1,
                    ram_requirement_gb=4.5,
                    gpu_required=False,
                    priority=3,
                    enabled=True,
                    specialization_tags=["reasoning", "logic", "analysis"]
                ),
                "mistral_7b": ModelConfig(
                    model_id="mistral_7b",
                    model_type=ModelType.FACT_CHECKER,
                    model_path="models/mistral-7b-instruct",
                    model_name="mistralai/Mistral-7B-Instruct-v0.3",
                    context_length=32000,
                    max_tokens=1024,
                    temperature=0.05,
                    top_p=0.95,
                    repeat_penalty=1.05,
                    ram_requirement_gb=8.0,
                    gpu_required=False,
                    priority=4,
                    enabled=True,
                    specialization_tags=["fact_checking", "verification", "accuracy"]
                )
            }

            # Initialize configurations
            for model_id, config in default_configs.items():
                self.model_configs[model_id] = config
                self.model_status[model_id] = ModelStatus.DISABLED
                self.ensemble_weights[model_id] = 1.0 / len(default_configs)

            # Set up fallback chains
            self.fallback_chains = {
                "llama32_3b": ["qwen25_3b", "phi35_mini"],
                "qwen25_3b": ["llama32_3b", "phi35_mini"],
                "phi35_mini": ["llama32_3b", "qwen25_3b"],
                "mistral_7b": ["llama32_3b", "qwen25_3b"]
            }

            logger.info("Loaded %d model configurations", len(self.model_configs))

        except Exception as e:
            logger.error("Failed to load model configurations: %s", e)
            raise

    async def initialize_models(self, available_ram_gb: float = 16.0) -> Result[bool, str]:
        """Initialize models based on available RAM."""
        try:
            # Calculate which models can be loaded
            loadable_models = self._calculate_loadable_models(available_ram_gb)

            if not loadable_models:
                return Result.error("No models can be loaded with available RAM")

            # Load models in priority order
            loaded_count = 0
            for model_id in loadable_models:
                try:
                    await self._load_model(model_id)
                    loaded_count += 1
                    logger.info("Successfully loaded model: %s", model_id)
                except Exception as e:
                    logger.warning("Failed to load model %s: %s", model_id, e)
                    self.model_status[model_id] = ModelStatus.ERROR

            # Update ensemble weights based on loaded models
            self._update_ensemble_weights()

            logger.info("Initialized %d/%d models successfully", loaded_count, len(loadable_models))
            return Result.success(loaded_count > 0)

        except Exception as e:
            logger.error("Failed to initialize models: %s", e)
            return Result.error(f"Model initialization failed: {e}")

    def _calculate_loadable_models(self, available_ram_gb: float) -> List[str]:
        """Calculate which models can be loaded with available RAM."""
        loadable_models = []
        total_ram_used = 0.0

        # Sort by priority (lower number = higher priority)
        sorted_models = sorted(
            self.model_configs.items(),
            key=lambda x: (x[1].priority, x[1].ram_requirement_gb)
        )

        for model_id, config in sorted_models:
            if not config.enabled:
                continue

            if total_ram_used + config.ram_requirement_gb <= available_ram_gb:
                loadable_models.append(model_id)
                total_ram_used += config.ram_requirement_gb
            else:
                logger.info("Skipping model %s due to RAM constraints", model_id)

        logger.info("Can load %d models with %.1fGB RAM (%.1fGB total)",
                   len(loadable_models), available_ram_gb, total_ram_used)

        return loadable_models

    async def _load_model(self, model_id: str) -> None:
        """Load a specific model."""
        config = self.model_configs[model_id]
        self.model_status[model_id] = ModelStatus.LOADING

        try:
            # Simulate model loading (in real implementation, this would load the actual model)
            await asyncio.sleep(0.1)  # Simulate loading time

            # Check if model file exists
            model_path = Path(config.model_path)
            if not model_path.exists():
                logger.warning("Model file not found: %s", config.model_path)
                self.model_status[model_id] = ModelStatus.ERROR
                return

            # Initialize model instance (placeholder)
            self.models[model_id] = {
                "config": config,
                "loaded_at": datetime.now(timezone.utc),
                "status": ModelStatus.READY
            }

            self.model_status[model_id] = ModelStatus.READY
            logger.info("Model %s loaded successfully", model_id)

        except Exception as e:
            logger.error("Failed to load model %s: %s", model_id, e)
            self.model_status[model_id] = ModelStatus.ERROR
            raise

    def _update_ensemble_weights(self) -> None:
        """Update ensemble weights based on loaded models."""
        loaded_models = [
            model_id for model_id, status in self.model_status.items()
            if status == ModelStatus.READY
        ]

        if not loaded_models:
            return

        # Equal weights for now (can be made adaptive based on performance)
        weight = 1.0 / len(loaded_models)

        for model_id in loaded_models:
            self.ensemble_weights[model_id] = weight

        logger.info("Updated ensemble weights for %d models", len(loaded_models))

    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        use_ensemble: bool = True,
        max_models: int = 3,
        timeout_seconds: float = 30.0
    ) -> Result[EnsembleResult, str]:
        """Generate response using ensemble of models."""
        try:
            start_time = datetime.now()
            self.total_requests += 1

            # Get available models
            available_models = [
                model_id for model_id, status in self.model_status.items()
                if status == ModelStatus.READY
            ]

            if not available_models:
                return Result.error("No models available for generation")

            # Limit number of models used
            models_to_use = available_models[:max_models]

            if use_ensemble and len(models_to_use) > 1:
                # Use ensemble voting
                result = await self._ensemble_generation(
                    prompt, context, models_to_use, timeout_seconds
                )
            else:
                # Use single model (primary)
                primary_model = models_to_use[0]
                result = await self._single_model_generation(
                    prompt, context, primary_model, timeout_seconds
                )

            # Update performance metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_performance_metrics(result, processing_time)

            if result.error:
                self.failed_requests += 1
            else:
                self.successful_requests += 1

            return Result.success(result)

        except Exception as e:
            logger.error("Failed to generate response: %s", e)
            self.failed_requests += 1
            return Result.error(f"Response generation failed: {e}")

    async def _ensemble_generation(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]],
        models: List[str],
        timeout_seconds: float
    ) -> EnsembleResult:
        """Generate response using ensemble voting."""
        start_time = datetime.now()

        # Generate responses from all models in parallel
        tasks = []
        for model_id in models:
            task = self._generate_single_response(prompt, context, model_id, timeout_seconds)
            tasks.append(task)

        # Wait for all responses
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process responses
        valid_responses = []
        errors = []

        for i, response in enumerate(responses):
            model_id = models[i]
            if isinstance(response, Exception):
                errors.append(f"Model {model_id}: {response}")
                logger.warning("Model %s failed: %s", model_id, response)
            elif response.error:
                errors.append(f"Model {model_id}: {response.error}")
            else:
                valid_responses.append(response)

        if not valid_responses:
            return EnsembleResult(
                final_response="All models failed to generate responses",
                confidence=0.0,
                agreement_score=0.0,
                uncertainty_estimate=1.0,
                method_used="ensemble_failed",
                individual_responses=[],
                weights_used={},
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                consensus_reached=False,
                disagreement_details=[{"error": error} for error in errors]
            )

        # Perform ensemble voting
        ensemble_result = self._perform_ensemble_voting(valid_responses)

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return EnsembleResult(
            final_response=ensemble_result["final_response"],
            confidence=ensemble_result["confidence"],
            agreement_score=ensemble_result["agreement_score"],
            uncertainty_estimate=ensemble_result["uncertainty_estimate"],
            method_used="ensemble_voting",
            individual_responses=valid_responses,
            weights_used=ensemble_result["weights"],
            processing_time_ms=processing_time,
            consensus_reached=ensemble_result["consensus_reached"],
            disagreement_details=ensemble_result["disagreement_details"]
        )

    async def _single_model_generation(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]],
        model_id: str,
        timeout_seconds: float
    ) -> EnsembleResult:
        """Generate response using single model."""
        start_time = datetime.now()

        response = await self._generate_single_response(prompt, context, model_id, timeout_seconds)

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        if response.error:
            return EnsembleResult(
                final_response=f"Model {model_id} failed: {response.error}",
                confidence=0.0,
                agreement_score=0.0,
                uncertainty_estimate=1.0,
                method_used="single_model_failed",
                individual_responses=[response],
                weights_used={model_id: 1.0},
                processing_time_ms=processing_time,
                consensus_reached=False
            )

        return EnsembleResult(
            final_response=response.response_text,
            confidence=response.confidence,
            agreement_score=1.0,  # Single model, perfect agreement
            uncertainty_estimate=1.0 - response.confidence,
            method_used="single_model",
            individual_responses=[response],
            weights_used={model_id: 1.0},
            processing_time_ms=processing_time,
            consensus_reached=True
        )

    async def _generate_single_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]],
        model_id: str,
        timeout_seconds: float
    ) -> ModelResponse:
        """Generate response from a single model."""
        start_time = datetime.now()

        try:
            config = self.model_configs[model_id]

            # Simulate model inference (in real implementation, this would call the actual model)
            await asyncio.sleep(0.1)  # Simulate inference time

            # Generate mock response based on model type
            response_text = self._generate_mock_response(prompt, config.model_type)

            # Calculate metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            tokens_generated = len(response_text.split())
            tokens_per_second = tokens_generated / (processing_time / 1000) if processing_time > 0 else 0

            return ModelResponse(
                model_id=model_id,
                model_type=config.model_type,
                response_text=response_text,
                confidence=0.85 + (hash(model_id) % 15) / 100,  # Mock confidence
                processing_time_ms=processing_time,
                tokens_generated=tokens_generated,
                tokens_per_second=tokens_per_second,
                memory_used_mb=config.ram_requirement_gb * 1024,
                metadata={"model_version": "1.0", "context_length": config.context_length}
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return ModelResponse(
                model_id=model_id,
                model_type=self.model_configs[model_id].model_type,
                response_text="",
                confidence=0.0,
                processing_time_ms=processing_time,
                tokens_generated=0,
                tokens_per_second=0.0,
                memory_used_mb=0.0,
                error=str(e)
            )

    def _generate_mock_response(self, prompt: str, model_type: ModelType) -> str:
        """Generate mock response based on model type."""
        if model_type == ModelType.PRIMARY:
            return f"Primary model analysis: {prompt[:100]}... [Compliance analysis with high confidence]"
        elif model_type == ModelType.SECONDARY:
            return f"Secondary model analysis: {prompt[:100]}... [Clinical reasoning with medical focus]"
        elif model_type == ModelType.SPECIALIZED:
            return f"Specialized model analysis: {prompt[:100]}... [Logical reasoning and analysis]"
        elif model_type == ModelType.FACT_CHECKER:
            return f"Fact-checker analysis: {prompt[:100]}... [Verification and accuracy assessment]"
        else:
            return f"Model analysis: {prompt[:100]}... [General analysis]"

    def _perform_ensemble_voting(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        """Perform ensemble voting on multiple responses."""
        if len(responses) == 1:
            response = responses[0]
            return {
                "final_response": response.response_text,
                "confidence": response.confidence,
                "agreement_score": 1.0,
                "uncertainty_estimate": 1.0 - response.confidence,
                "weights": {response.model_id: 1.0},
                "consensus_reached": True,
                "disagreement_details": []
            }

        # Calculate weighted average confidence
        total_weight = 0.0
        weighted_confidence = 0.0

        for response in responses:
            weight = self.ensemble_weights.get(response.model_id, 1.0)
            weighted_confidence += response.confidence * weight
            total_weight += weight

        avg_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.0

        # Calculate agreement score (simplified)
        confidences = [r.confidence for r in responses]
        confidence_variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)
        agreement_score = max(0.0, 1.0 - confidence_variance)

        # Select best response (highest confidence)
        best_response = max(responses, key=lambda r: r.confidence)

        return {
            "final_response": best_response.response_text,
            "confidence": avg_confidence,
            "agreement_score": agreement_score,
            "uncertainty_estimate": 1.0 - avg_confidence,
            "weights": {r.model_id: self.ensemble_weights.get(r.model_id, 1.0) for r in responses},
            "consensus_reached": agreement_score > 0.7,
            "disagreement_details": [
                {
                    "model_id": r.model_id,
                    "confidence": r.confidence,
                    "deviation": abs(r.confidence - avg_confidence)
                }
                for r in responses
            ]
        }

    def _update_performance_metrics(self, result: EnsembleResult, processing_time_ms: float) -> None:
        """Update performance metrics."""
        # Update average response time
        if self.total_requests > 0:
            self.average_response_time = (
                (self.average_response_time * (self.total_requests - 1) + processing_time_ms)
                / self.total_requests
            )

        # Store performance history
        self.performance_history.append({
            "timestamp": datetime.now(timezone.utc),
            "processing_time_ms": processing_time_ms,
            "confidence": result.confidence,
            "agreement_score": result.agreement_score,
            "models_used": len(result.individual_responses),
            "method_used": result.method_used
        })

        # Keep only recent history
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-500:]

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        loaded_models = [
            model_id for model_id, status in self.model_status.items()
            if status == ModelStatus.READY
        ]

        total_ram_required = sum(
            config.ram_requirement_gb for model_id, config in self.model_configs.items()
            if model_id in loaded_models
        )

        return {
            "total_models_configured": len(self.model_configs),
            "models_loaded": len(loaded_models),
            "loaded_model_ids": loaded_models,
            "total_ram_required_gb": total_ram_required,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.successful_requests / max(1, self.total_requests),
            "average_response_time_ms": self.average_response_time,
            "model_status": {model_id: status.value for model_id, status in self.model_status.items()},
            "ensemble_weights": self.ensemble_weights
        }

    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            # Unload all models
            for model_id in list(self.models.keys()):
                await self._unload_model(model_id)

            logger.info("HybridModelSystem cleanup completed")

        except Exception as e:
            logger.error("Error during cleanup: %s", e)

    async def _unload_model(self, model_id: str) -> None:
        """Unload a specific model."""
        try:
            if model_id in self.models:
                del self.models[model_id]
                self.model_status[model_id] = ModelStatus.DISABLED
                logger.info("Unloaded model: %s", model_id)
        except Exception as e:
            logger.error("Failed to unload model %s: %s", model_id, e)


# Global instance
hybrid_model_system = HybridModelSystem()
