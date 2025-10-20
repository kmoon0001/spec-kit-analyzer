"""Unified ML System Interface for Clinical Compliance Analysis.

This module provides a comprehensive, dependency-injected interface that orchestrates
all ML components including confidence calibration, ensemble optimization, bias
detection, and caching using expert patterns and best practices.

Features:
- Dependency injection with proper interfaces
- Comprehensive ML orchestration
- Integrated caching and performance monitoring
- Type-safe operations with comprehensive error handling
- Async/await patterns throughout
- Circuit breaker pattern for resilience
- Comprehensive logging and metrics
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Generic, Union
import uuid
from contextlib import asynccontextmanager

from src.core.confidence_calibrator import ConfidenceCalibrator as StatisticalCalibrator
from src.core.confidence_optimizer import ConfidenceCalibrator as MultiSignalCalibrator, ConfidenceMetrics
from src.core.advanced_ensemble_optimizer import AdvancedEnsembleOptimizer, EnsembleMethod, EnsembleResult
from src.core.xai_ethical_system import BiasMitigationEngine, AccuracyEnhancer
from src.core.unified_explanation_engine import UnifiedExplanationEngine, ExplanationType
from src.core.multi_tier_cache import MultiTierCacheSystem, CacheTier
from src.core.advanced_security_system import AdvancedSecuritySystem

logger = logging.getLogger(__name__)

# Type definitions for better type safety
T = TypeVar('T')
AnalysisResult = Dict[str, Any]
MLContext = Dict[str, Any]


class CircuitBreakerState(Enum):
    """Circuit breaker states for resilience."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class MLMetrics:
    """Comprehensive ML system metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    confidence_calibration_accuracy: float = 0.0
    ensemble_agreement_score: float = 0.0
    bias_detection_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class MLRequest:
    """Standardized ML request with comprehensive metadata."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_text: str = ""
    entities: List[Dict[str, Any]] = field(default_factory=list)
    retrieved_rules: List[Dict[str, Any]] = field(default_factory=list)
    context: MLContext = field(default_factory=dict)
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    priority: str = "normal"  # low, normal, high, critical
    timeout_seconds: float = 30.0


@dataclass
class MLResponse:
    """Standardized ML response with comprehensive results."""
    request_id: str
    analysis_result: AnalysisResult
    confidence_metrics: Optional[ConfidenceMetrics] = None
    ensemble_result: Optional[EnsembleResult] = None
    bias_metrics: Optional[Dict[str, Any]] = None
    explanation_result: Optional[Dict[str, Any]] = None
    processing_time_ms: float = 0.0
    cache_hit: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


# Protocol definitions for dependency injection
class ConfidenceCalibratorProtocol(Protocol):
    """Protocol for confidence calibration components."""

    async def calibrate_confidence(
        self,
        analysis_result: AnalysisResult,
        entities: List[Dict[str, Any]],
        fact_check_results: List[bool],
        context_relevance: float
    ) -> ConfidenceMetrics:
        """Calibrate confidence using multiple signals."""
        ...


class EnsembleOptimizerProtocol(Protocol):
    """Protocol for ensemble optimization components."""

    async def predict_with_ensemble(
        self,
        input_data: Any,
        method: EnsembleMethod = EnsembleMethod.DYNAMIC_WEIGHTING,
        context: Optional[MLContext] = None
    ) -> EnsembleResult:
        """Make prediction using ensemble methods."""
        ...


class BiasDetectorProtocol(Protocol):
    """Protocol for bias detection components."""

    async def detect_bias(
        self,
        analysis_result: AnalysisResult,
        entities: List[Dict[str, Any]],
        document_text: str
    ) -> Dict[str, Any]:
        """Detect various types of bias."""
        ...


class CacheProtocol(Protocol):
    """Protocol for caching components."""

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        ...

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
        tags: Optional[List[str]] = None,
        tier: Optional[CacheTier] = None
    ) -> bool:
        """Set value in cache."""
        ...


class CircuitBreaker:
    """Circuit breaker implementation for resilience."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitBreakerState.CLOSED

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if self.last_failure_time is None:
            return True

        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)

    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class UnifiedMLSystem:
    """Unified ML system with dependency injection and comprehensive orchestration.

    This class orchestrates all ML components using dependency injection,
    circuit breakers, comprehensive caching, and expert patterns.
    """

    def __init__(
        self,
        confidence_calibrator: Optional[ConfidenceCalibratorProtocol] = None,
        ensemble_optimizer: Optional[EnsembleOptimizerProtocol] = None,
        bias_detector: Optional[BiasDetectorProtocol] = None,
        explanation_engine: Optional[UnifiedExplanationEngine] = None,
        cache_system: Optional[CacheProtocol] = None,
        security_system: Optional[AdvancedSecuritySystem] = None,
        enable_circuit_breaker: bool = True,
        enable_caching: bool = True,
        enable_metrics: bool = True
    ):
        """Initialize the unified ML system with dependency injection."""

        # Core ML components with dependency injection
        self.confidence_calibrator = confidence_calibrator or MultiSignalCalibrator()
        self.ensemble_optimizer = ensemble_optimizer or AdvancedEnsembleOptimizer()
        self.bias_detector = bias_detector or BiasMitigationEngine()
        self.explanation_engine = explanation_engine or UnifiedExplanationEngine()
        self.cache_system = cache_system or MultiTierCacheSystem()
        self.security_system = security_system or AdvancedSecuritySystem()

        # System configuration
        self.enable_circuit_breaker = enable_circuit_breaker
        self.enable_caching = enable_caching
        self.enable_metrics = enable_metrics

        # Circuit breakers for resilience
        self.circuit_breakers = {
            'confidence_calibration': CircuitBreaker(),
            'ensemble_optimization': CircuitBreaker(),
            'bias_detection': CircuitBreaker(),
            'explanation_generation': CircuitBreaker(),
            'caching': CircuitBreaker()
        }

        # Metrics and monitoring
        self.metrics = MLMetrics()
        self.request_history: List[MLRequest] = []
        self.response_history: List[MLResponse] = []

        # Performance tracking
        self.performance_tracker: Dict[str, List[float]] = {
            'confidence_calibration': [],
            'ensemble_optimization': [],
            'bias_detection': [],
            'explanation_generation': [],
            'total_processing': []
        }

        logger.info("Unified ML system initialized with dependency injection")

    async def analyze_document(
        self,
        request: MLRequest,
        explanation_types: Optional[List[ExplanationType]] = None
    ) -> MLResponse:
        """Comprehensive document analysis with full ML pipeline.

        This is the main entry point that orchestrates all ML components
        using expert patterns including circuit breakers, caching, and metrics.
        """
        start_time = datetime.now()

        try:
            # Validate request
            await self._validate_request(request)

            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_result = None

            if self.enable_caching:
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    logger.info("Cache hit for request %s", request.request_id)
                    return self._create_response_from_cache(request, cached_result, start_time)

            # Generate analysis result (this would come from your existing analysis pipeline)
            analysis_result = await self._generate_analysis_result(request)

            # Apply ML enhancements with circuit breaker protection
            enhanced_result = await self._apply_ml_enhancements(
                request, analysis_result, explanation_types
            )

            # Cache the result
            if self.enable_caching:
                await self._cache_result(cache_key, enhanced_result)

            # Create comprehensive response
            response = self._create_comprehensive_response(
                request, enhanced_result, start_time
            )

            # Update metrics
            if self.enable_metrics:
                await self._update_metrics(request, response)

            logger.info("Document analysis completed for request %s in %.2fms",
                       request.request_id, response.processing_time_ms)

            return response

        except Exception as e:
            logger.exception("Document analysis failed for request %s: %s",
                           request.request_id, e)

            # Create error response
            error_response = MLResponse(
                request_id=request.request_id,
                analysis_result={},
                errors=[str(e)],
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

            # Update failure metrics
            if self.enable_metrics:
                self.metrics.failed_requests += 1

            return error_response

    async def _apply_ml_enhancements(
        self,
        request: MLRequest,
        analysis_result: AnalysisResult,
        explanation_types: Optional[List[ExplanationType]]
    ) -> Dict[str, Any]:
        """Apply all ML enhancements with circuit breaker protection."""

        enhanced_result = analysis_result.copy()

        # 1. Confidence Calibration
        try:
            if self.enable_circuit_breaker:
                confidence_metrics = await self.circuit_breakers['confidence_calibration'].call(
                    self._calibrate_confidence, request, enhanced_result
                )
            else:
                confidence_metrics = await self._calibrate_confidence(request, enhanced_result)

            enhanced_result['confidence_metrics'] = confidence_metrics

        except Exception as e:
            logger.warning("Confidence calibration failed: %s", e)
            enhanced_result['confidence_calibration_error'] = str(e)

        # 2. Ensemble Optimization
        try:
            if self.enable_circuit_breaker:
                ensemble_result = await self.circuit_breakers['ensemble_optimization'].call(
                    self._optimize_with_ensemble, request, enhanced_result
                )
            else:
                ensemble_result = await self._optimize_with_ensemble(request, enhanced_result)

            enhanced_result['ensemble_result'] = ensemble_result

        except Exception as e:
            logger.warning("Ensemble optimization failed: %s", e)
            enhanced_result['ensemble_optimization_error'] = str(e)

        # 3. Bias Detection and Mitigation
        try:
            if self.enable_circuit_breaker:
                bias_metrics = await self.circuit_breakers['bias_detection'].call(
                    self._detect_and_mitigate_bias, request, enhanced_result
                )
            else:
                bias_metrics = await self._detect_and_mitigate_bias(request, enhanced_result)

            enhanced_result['bias_metrics'] = bias_metrics

        except Exception as e:
            logger.warning("Bias detection failed: %s", e)
            enhanced_result['bias_detection_error'] = str(e)

        # 4. Explanation Generation
        try:
            if self.enable_circuit_breaker:
                explanation_result = await self.circuit_breakers['explanation_generation'].call(
                    self._generate_explanations, request, enhanced_result, explanation_types
                )
            else:
                explanation_result = await self._generate_explanations(
                    request, enhanced_result, explanation_types
                )

            enhanced_result.update(explanation_result)

        except Exception as e:
            logger.warning("Explanation generation failed: %s", e)
            enhanced_result['explanation_generation_error'] = str(e)

        return enhanced_result

    async def _calibrate_confidence(
        self,
        request: MLRequest,
        analysis_result: AnalysisResult
    ) -> ConfidenceMetrics:
        """Calibrate confidence using multiple signals."""
        start_time = datetime.now()

        try:
            # Extract fact check results (this would come from your fact checker)
            fact_check_results = analysis_result.get('fact_check_results', [])
            context_relevance = analysis_result.get('context_relevance', 0.5)

            # Use the multi-signal calibrator
            confidence_metrics = self.confidence_calibrator.calibrate_confidence(
                analysis_result=analysis_result,
                entities=request.entities,
                fact_check_results=fact_check_results,
                context_relevance=context_relevance
            )

            # Track performance
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.performance_tracker['confidence_calibration'].append(processing_time)

            return confidence_metrics

        except Exception as e:
            logger.exception("Confidence calibration failed: %s", e)
            raise

    async def _optimize_with_ensemble(
        self,
        request: MLRequest,
        analysis_result: AnalysisResult
    ) -> EnsembleResult:
        """Optimize analysis using ensemble methods."""
        start_time = datetime.now()

        try:
            # Prepare input data for ensemble
            input_data = {
                'analysis_result': analysis_result,
                'entities': request.entities,
                'retrieved_rules': request.retrieved_rules,
                'context': request.context
            }

            # Use ensemble optimization
            ensemble_result = await self.ensemble_optimizer.predict_with_ensemble(
                input_data=input_data,
                method=EnsembleMethod.DYNAMIC_WEIGHTING,
                context=request.context
            )

            # Track performance
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.performance_tracker['ensemble_optimization'].append(processing_time)

            return ensemble_result

        except Exception as e:
            logger.exception("Ensemble optimization failed: %s", e)
            raise

    async def _detect_and_mitigate_bias(
        self,
        request: MLRequest,
        analysis_result: AnalysisResult
    ) -> Dict[str, Any]:
        """Detect and mitigate bias in the analysis."""
        start_time = datetime.now()

        try:
            # Use bias detection engine
            bias_metrics = self.bias_detector.detect_bias(
                analysis_result=analysis_result,
                entities=request.entities,
                document_text=request.document_text
            )

            # Track performance
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.performance_tracker['bias_detection'].append(processing_time)

            return bias_metrics

        except Exception as e:
            logger.exception("Bias detection failed: %s", e)
            raise

    async def _generate_explanations(
        self,
        request: MLRequest,
        analysis_result: AnalysisResult,
        explanation_types: Optional[List[ExplanationType]]
    ) -> Dict[str, Any]:
        """Generate comprehensive explanations."""
        start_time = datetime.now()

        try:
            # Create explanation context
            from src.core.unified_explanation_engine import ExplanationContext

            context = ExplanationContext(
                document_type=request.context.get('document_type'),
                discipline=request.context.get('discipline'),
                entities=request.entities,
                retrieved_rules=request.retrieved_rules,
                user_id=request.user_id,
                session_id=request.session_id
            )

            # Generate explanations
            explanation_result = await self.explanation_engine.generate_comprehensive_explanation(
                analysis_result=analysis_result,
                context=context,
                explanation_types=explanation_types or [ExplanationType.REGULATORY, ExplanationType.CLINICAL]
            )

            # Track performance
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.performance_tracker['explanation_generation'].append(processing_time)

            return explanation_result

        except Exception as e:
            logger.exception("Explanation generation failed: %s", e)
            raise

    async def _validate_request(self, request: MLRequest) -> None:
        """Validate ML request with comprehensive checks."""
        if not request.document_text.strip():
            raise ValueError("Document text cannot be empty")

        if len(request.document_text) > 100000:  # 100KB limit
            raise ValueError("Document text too large")

        if request.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")

        # Security validation
        if self.security_system:
            threats = self.security_system.detect_threats({
                'document_text': request.document_text,
                'user_id': request.user_id
            })
            if threats:
                raise ValueError(f"Security threats detected: {[t.value for t in threats]}")

    def _generate_cache_key(self, request: MLRequest) -> str:
        """Generate cache key for request."""
        import hashlib
        import json

        key_data = {
            'document_hash': hashlib.md5(request.document_text.encode()).hexdigest(),
            'entities_count': len(request.entities),
            'rules_count': len(request.retrieved_rules),
            'user_id': request.user_id,
            'context_hash': hashlib.md5(json.dumps(request.context, sort_keys=True).encode()).hexdigest()
        }

        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get result from cache with circuit breaker protection."""
        if not self.enable_caching:
            return None

        try:
            if self.enable_circuit_breaker:
                return await self.circuit_breakers['caching'].call(
                    self.cache_system.get, cache_key
                )
            else:
                return await self.cache_system.get(cache_key)
        except Exception as e:
            logger.warning("Cache get failed: %s", e)
            return None

    async def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache result with circuit breaker protection."""
        if not self.enable_caching:
            return

        try:
            if self.enable_circuit_breaker:
                await self.circuit_breakers['caching'].call(
                    self.cache_system.set, cache_key, result,
                    ttl=timedelta(hours=1), tags=['ml_analysis']
                )
            else:
                await self.cache_system.set(
                    cache_key, result,
                    ttl=timedelta(hours=1), tags=['ml_analysis']
                )
        except Exception as e:
            logger.warning("Cache set failed: %s", e)

    def _create_response_from_cache(
        self,
        request: MLRequest,
        cached_result: Dict[str, Any],
        start_time: datetime
    ) -> MLResponse:
        """Create response from cached result."""
        return MLResponse(
            request_id=request.request_id,
            analysis_result=cached_result,
            processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
            cache_hit=True
        )

    def _create_comprehensive_response(
        self,
        request: MLRequest,
        enhanced_result: Dict[str, Any],
        start_time: datetime
    ) -> MLResponse:
        """Create comprehensive ML response."""
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Track total processing time
        self.performance_tracker['total_processing'].append(processing_time)

        return MLResponse(
            request_id=request.request_id,
            analysis_result=enhanced_result,
            confidence_metrics=enhanced_result.get('confidence_metrics'),
            ensemble_result=enhanced_result.get('ensemble_result'),
            bias_metrics=enhanced_result.get('bias_metrics'),
            explanation_result=enhanced_result,
            processing_time_ms=processing_time,
            cache_hit=False
        )

    async def _generate_analysis_result(self, request: MLRequest) -> AnalysisResult:
        """Generate base analysis result (placeholder - integrate with your existing pipeline)."""
        # This would integrate with your existing analysis pipeline
        return {
            'summary': f"Analysis of document with {len(request.document_text)} characters",
            'findings': [],
            'confidence': 0.5,
            'document_text': request.document_text,
            'entities': request.entities,
            'retrieved_rules': request.retrieved_rules
        }

    async def _update_metrics(self, request: MLRequest, response: MLResponse) -> None:
        """Update comprehensive metrics."""
        self.metrics.total_requests += 1

        if response.errors:
            self.metrics.failed_requests += 1
        else:
            self.metrics.successful_requests += 1

        # Update average response time
        total_requests = self.metrics.total_requests
        current_avg = self.metrics.average_response_time_ms
        self.metrics.average_response_time_ms = (
            (current_avg * (total_requests - 1) + response.processing_time_ms) / total_requests
        )

        # Update cache hit rate
        if response.cache_hit:
            cache_hits = sum(1 for r in self.response_history if r.cache_hit)
            self.metrics.cache_hit_rate = cache_hits / max(1, len(self.response_history))

        # Store request and response
        self.request_history.append(request)
        self.response_history.append(response)

        # Keep only recent history (last 1000 requests)
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-500:]
            self.response_history = self.response_history[-500:]

        self.metrics.last_updated = datetime.now()

    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status."""
        health_status = {
            'overall_status': 'healthy',
            'components': {},
            'metrics': {
                'total_requests': self.metrics.total_requests,
                'success_rate': (
                    self.metrics.successful_requests / max(1, self.metrics.total_requests)
                ),
                'average_response_time_ms': self.metrics.average_response_time_ms,
                'cache_hit_rate': self.metrics.cache_hit_rate
            },
            'circuit_breakers': {},
            'performance': {}
        }

        # Check circuit breaker states
        for name, cb in self.circuit_breakers.items():
            health_status['circuit_breakers'][name] = {
                'state': cb.state.value,
                'failure_count': cb.failure_count
            }

            if cb.state == CircuitBreakerState.OPEN:
                health_status['overall_status'] = 'degraded'

        # Check component performance
        for component, times in self.performance_tracker.items():
            if times:
                avg_time = sum(times) / len(times)
                health_status['performance'][component] = {
                    'average_time_ms': avg_time,
                    'request_count': len(times)
                }

        return health_status

    async def clear_cache(self) -> int:
        """Clear all cached results."""
        if hasattr(self.cache_system, 'clear_all'):
            return await self.cache_system.clear_all()
        return 0

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = MLMetrics()
        self.request_history.clear()
        self.response_history.clear()
        self.performance_tracker = {
            'confidence_calibration': [],
            'ensemble_optimization': [],
            'bias_detection': [],
            'explanation_generation': [],
            'total_processing': []
        }

        # Reset circuit breakers
        for cb in self.circuit_breakers.values():
            cb.failure_count = 0
            cb.state = CircuitBreakerState.CLOSED
            cb.last_failure_time = None


# Dependency injection container
class MLSystemContainer:
    """Dependency injection container for ML system components."""

    def __init__(self):
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}

    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton instance."""
        self._instances[name] = instance

    def register_factory(self, name: str, factory: callable) -> None:
        """Register a factory function."""
        self._factories[name] = factory

    def get(self, name: str) -> Any:
        """Get instance by name."""
        if name in self._instances:
            return self._instances[name]

        if name in self._factories:
            instance = self._factories[name]()
            self._instances[name] = instance
            return instance

        raise ValueError(f"Component '{name}' not found")

    def create_ml_system(self) -> UnifiedMLSystem:
        """Create ML system with all dependencies."""
        return UnifiedMLSystem(
            confidence_calibrator=self.get('confidence_calibrator'),
            ensemble_optimizer=self.get('ensemble_optimizer'),
            bias_detector=self.get('bias_detector'),
            explanation_engine=self.get('explanation_engine'),
            cache_system=self.get('cache_system'),
            security_system=self.get('security_system')
        )


# Global container instance
ml_container = MLSystemContainer()

# Register default components
ml_container.register_singleton('confidence_calibrator', MultiSignalCalibrator())
ml_container.register_singleton('ensemble_optimizer', AdvancedEnsembleOptimizer())
ml_container.register_singleton('bias_detector', BiasMitigationEngine())
ml_container.register_singleton('explanation_engine', UnifiedExplanationEngine())
ml_container.register_singleton('cache_system', MultiTierCacheSystem())
ml_container.register_singleton('security_system', AdvancedSecuritySystem())

# Global ML system instance
unified_ml_system = ml_container.create_ml_system()
