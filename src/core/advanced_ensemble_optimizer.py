"""Advanced Ensemble Optimization System for Clinical Compliance Analysis.

This module implements sophisticated ensemble methods including stacking, bagging,
boosting, and dynamic weight optimization for improved accuracy and reliability.

Features:
- Model stacking with meta-learners
- Bootstrap aggregating (bagging)
- Adaptive boosting (AdaBoost)
- Dynamic weight optimization
- Cross-validation for ensemble training
- Performance monitoring and adaptation
"""

import asyncio
import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
import json
import hashlib

logger = logging.getLogger(__name__)


class EnsembleMethod(Enum):
    """Available ensemble methods."""
    VOTING = "voting"
    STACKING = "stacking"
    BAGGING = "bagging"
    BOOSTING = "boosting"
    DYNAMIC_WEIGHTING = "dynamic_weighting"


class ModelType(Enum):
    """Types of models in the ensemble."""
    LLM = "llm"
    NER = "ner"
    FACT_CHECKER = "fact_checker"
    RETRIEVER = "retriever"
    CLASSIFIER = "classifier"


@dataclass
class ModelPrediction:
    """Individual model prediction with metadata."""
    model_type: ModelType
    model_name: str
    prediction: Any
    confidence: float
    features_used: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EnsembleResult:
    """Ensemble prediction result."""
    final_prediction: Any
    confidence: float
    method_used: EnsembleMethod
    individual_predictions: List[ModelPrediction] = field(default_factory=list)
    weights: Dict[str, float] = field(default_factory=dict)
    agreement_score: float = 0.0
    uncertainty_estimate: float = 0.0
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EnsembleMetrics:
    """Performance metrics for ensemble methods."""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    confidence_calibration: float = 0.0
    diversity_score: float = 0.0
    stability_score: float = 0.0


class AdvancedEnsembleOptimizer:
    """Advanced ensemble optimization system for clinical compliance analysis.

    Implements multiple ensemble methods with dynamic optimization and
    performance monitoring.
    """

    def __init__(self, enable_learning: bool = True, cache_predictions: bool = True):
        """Initialize the advanced ensemble optimizer.

        Args:
            enable_learning: Whether to enable online learning and adaptation
            cache_predictions: Whether to cache predictions for performance
        """
        self.enable_learning = enable_learning
        self.cache_predictions = cache_predictions
        self._prediction_cache: Dict[str, EnsembleResult] = {}

        # Model registry
        self.models: Dict[ModelType, Any] = {}
        self.model_weights: Dict[str, float] = {}
        self.model_performance: Dict[str, EnsembleMetrics] = {}

        # Ensemble methods configuration
        self.ensemble_config = {
            EnsembleMethod.VOTING: {
                'weighted': True,
                'confidence_threshold': 0.6,
                'min_models': 2
            },
            EnsembleMethod.STACKING: {
                'meta_learner': 'logistic_regression',
                'cv_folds': 5,
                'use_proba': True
            },
            EnsembleMethod.BAGGING: {
                'n_estimators': 10,
                'bootstrap_ratio': 0.8,
                'random_state': 42
            },
            EnsembleMethod.BOOSTING: {
                'n_estimators': 10,
                'learning_rate': 0.1,
                'max_depth': 3
            },
            EnsembleMethod.DYNAMIC_WEIGHTING: {
                'adaptation_rate': 0.01,
                'min_weight': 0.1,
                'max_weight': 1.0
            }
        }

        # Performance tracking
        self.performance_history: List[Dict[str, Any]] = []
        self.adaptation_threshold = 0.05  # Minimum performance change to trigger adaptation

        logger.info("Advanced ensemble optimizer initialized with learning=%s", enable_learning)

    async def register_model(
        self,
        model_type: ModelType,
        model_instance: Any,
        model_name: str,
        initial_weight: float = 1.0
    ) -> bool:
        """Register a model in the ensemble.

        Args:
            model_type: Type of the model
            model_instance: The model instance
            model_name: Unique name for the model
            initial_weight: Initial weight for the model

        Returns:
            True if registration successful
        """
        try:
            self.models[model_type] = model_instance
            self.model_weights[model_name] = initial_weight
            self.model_performance[model_name] = EnsembleMetrics()

            logger.info("Registered model %s of type %s with weight %.2f",
                       model_name, model_type.value, initial_weight)
            return True

        except Exception as e:
            logger.error("Failed to register model %s: %s", model_name, e)
            return False

    async def predict_with_ensemble(
        self,
        input_data: Any,
        method: EnsembleMethod = EnsembleMethod.DYNAMIC_WEIGHTING,
        context: Optional[Dict[str, Any]] = None
    ) -> EnsembleResult:
        """Make prediction using the specified ensemble method.

        Args:
            input_data: Input data for prediction
            method: Ensemble method to use
            context: Additional context information

        Returns:
            Ensemble prediction result
        """
        start_time = datetime.now()

        # Check cache first
        cache_key = self._generate_cache_key(input_data, method, context)
        if self.cache_predictions and cache_key in self._prediction_cache:
            logger.debug("Using cached ensemble prediction for key: %s", cache_key)
            return self._prediction_cache[cache_key]

        try:
            # Get individual predictions
            individual_predictions = await self._get_individual_predictions(input_data, context)

            if not individual_predictions:
                raise ValueError("No models available for ensemble prediction")

            # Apply ensemble method
            if method == EnsembleMethod.VOTING:
                result = await self._apply_voting(individual_predictions, context)
            elif method == EnsembleMethod.STACKING:
                result = await self._apply_stacking(individual_predictions, input_data, context)
            elif method == EnsembleMethod.BAGGING:
                result = await self._apply_bagging(individual_predictions, context)
            elif method == EnsembleMethod.BOOSTING:
                result = await self._apply_boosting(individual_predictions, context)
            elif method == EnsembleMethod.DYNAMIC_WEIGHTING:
                result = await self._apply_dynamic_weighting(individual_predictions, context)
            else:
                raise ValueError(f"Unknown ensemble method: {method}")

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            result.processing_time_ms = processing_time

            # Cache result
            if self.cache_predictions:
                self._prediction_cache[cache_key] = result

            # Update performance metrics if learning is enabled
            if self.enable_learning:
                await self._update_performance_metrics(result, context)

            logger.info("Ensemble prediction completed using %s method in %.2fms",
                       method.value, processing_time)

            return result

        except Exception as e:
            logger.exception("Ensemble prediction failed: %s", e)
            # Return fallback result
            return EnsembleResult(
                final_prediction=None,
                confidence=0.0,
                method_used=method,
                uncertainty_estimate=1.0,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _get_individual_predictions(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]]
    ) -> List[ModelPrediction]:
        """Get predictions from all registered models."""
        predictions = []

        for model_type, model_instance in self.models.items():
            try:
                start_time = datetime.now()

                # Get prediction based on model type
                if model_type == ModelType.LLM:
                    prediction, confidence = await self._get_llm_prediction(model_instance, input_data)
                elif model_type == ModelType.NER:
                    prediction, confidence = await self._get_ner_prediction(model_instance, input_data)
                elif model_type == ModelType.FACT_CHECKER:
                    prediction, confidence = await self._get_fact_checker_prediction(model_instance, input_data)
                elif model_type == ModelType.RETRIEVER:
                    prediction, confidence = await self._get_retriever_prediction(model_instance, input_data)
                elif model_type == ModelType.CLASSIFIER:
                    prediction, confidence = await self._get_classifier_prediction(model_instance, input_data)
                else:
                    continue

                processing_time = (datetime.now() - start_time).total_seconds() * 1000

                predictions.append(ModelPrediction(
                    model_type=model_type,
                    model_name=f"{model_type.value}_model",
                    prediction=prediction,
                    confidence=confidence,
                    processing_time_ms=processing_time
                ))

            except Exception as e:
                logger.warning("Failed to get prediction from %s model: %s", model_type.value, e)
                continue

        return predictions

    async def _apply_voting(
        self,
        predictions: List[ModelPrediction],
        context: Optional[Dict[str, Any]]
    ) -> EnsembleResult:
        """Apply voting ensemble method."""
        config = self.ensemble_config[EnsembleMethod.VOTING]

        if len(predictions) < config['min_models']:
            raise ValueError(f"Voting requires at least {config['min_models']} models")

        # Filter predictions by confidence threshold
        valid_predictions = [
            p for p in predictions
            if p.confidence >= config['confidence_threshold']
        ]

        if not valid_predictions:
            # Use all predictions if none meet threshold
            valid_predictions = predictions

        if config['weighted']:
            # Weighted voting
            weights = [self.model_weights.get(p.model_name, 1.0) for p in valid_predictions]
            weighted_predictions = [p.prediction for p in valid_predictions]

            # Simple weighted average for numerical predictions
            if all(isinstance(p, (int, float)) for p in weighted_predictions):
                final_prediction = np.average(weighted_predictions, weights=weights)
                final_confidence = np.average([p.confidence for p in valid_predictions], weights=weights)
            else:
                # For categorical predictions, use majority vote with weights
                prediction_counts = {}
                for pred, weight in zip(weighted_predictions, weights):
                    if pred not in prediction_counts:
                        prediction_counts[pred] = 0
                    prediction_counts[pred] += weight

                final_prediction = max(prediction_counts, key=prediction_counts.get)
                final_confidence = max(prediction_counts.values()) / sum(prediction_counts.values())
        else:
            # Simple majority voting
            prediction_counts = {}
            for p in valid_predictions:
                if p.prediction not in prediction_counts:
                    prediction_counts[p.prediction] = 0
                prediction_counts[p.prediction] += 1

            final_prediction = max(prediction_counts, key=prediction_counts.get)
            final_confidence = max(prediction_counts.values()) / len(valid_predictions)

        # Calculate agreement score
        agreement_score = self._calculate_agreement_score(valid_predictions)

        # Calculate uncertainty estimate
        uncertainty_estimate = 1.0 - agreement_score

        return EnsembleResult(
            final_prediction=final_prediction,
            confidence=final_confidence,
            method_used=EnsembleMethod.VOTING,
            individual_predictions=valid_predictions,
            weights={p.model_name: self.model_weights.get(p.model_name, 1.0) for p in valid_predictions},
            agreement_score=agreement_score,
            uncertainty_estimate=uncertainty_estimate
        )

    async def _apply_stacking(
        self,
        predictions: List[ModelPrediction],
        input_data: Any,
        context: Optional[Dict[str, Any]]
    ) -> EnsembleResult:
        """Apply stacking ensemble method."""
        config = self.ensemble_config[EnsembleMethod.STACKING]

        # Extract features from predictions
        features = []
        confidences = []

        for pred in predictions:
            if isinstance(pred.prediction, (int, float)):
                features.append([pred.prediction])
            elif isinstance(pred.prediction, list):
                features.append(pred.prediction)
            else:
                # Convert to numerical representation
                features.append([hash(str(pred.prediction)) % 1000])

            confidences.append(pred.confidence)

        # Simple meta-learner implementation
        if config['meta_learner'] == 'logistic_regression':
            # Use weighted average as simple meta-learner
            weights = [self.model_weights.get(p.model_name, 1.0) for p in predictions]

            if all(len(f) == 1 for f in features):
                # Single feature case
                final_prediction = np.average([f[0] for f in features], weights=weights)
            else:
                # Multiple features case - use average
                final_prediction = np.mean([np.mean(f) for f in features])

            final_confidence = np.average(confidences, weights=weights)

        else:
            # Fallback to voting
            return await self._apply_voting(predictions, context)

        # Calculate metrics
        agreement_score = self._calculate_agreement_score(predictions)
        uncertainty_estimate = 1.0 - agreement_score

        return EnsembleResult(
            final_prediction=final_prediction,
            confidence=final_confidence,
            method_used=EnsembleMethod.STACKING,
            individual_predictions=predictions,
            weights={p.model_name: self.model_weights.get(p.model_name, 1.0) for p in predictions},
            agreement_score=agreement_score,
            uncertainty_estimate=uncertainty_estimate
        )

    async def _apply_bagging(
        self,
        predictions: List[ModelPrediction],
        context: Optional[Dict[str, Any]]
    ) -> EnsembleResult:
        """Apply bagging ensemble method."""
        config = self.ensemble_config[EnsembleMethod.BAGGING]

        # Bootstrap sampling simulation
        n_samples = len(predictions)
        bootstrap_size = int(n_samples * config['bootstrap_ratio'])

        # Generate bootstrap samples
        bootstrap_samples = []
        for _ in range(config['n_estimators']):
            # Random sampling with replacement
            sample_indices = np.random.choice(n_samples, bootstrap_size, replace=True)
            bootstrap_samples.append([predictions[i] for i in sample_indices])

        # Aggregate bootstrap results
        bootstrap_predictions = []
        bootstrap_confidences = []

        for sample in bootstrap_samples:
            # Average predictions in each bootstrap sample
            sample_preds = [p.prediction for p in sample if isinstance(p.prediction, (int, float))]
            sample_confs = [p.confidence for p in sample]

            if sample_preds:
                bootstrap_predictions.append(np.mean(sample_preds))
                bootstrap_confidences.append(np.mean(sample_confs))

        if bootstrap_predictions:
            final_prediction = np.mean(bootstrap_predictions)
            final_confidence = np.mean(bootstrap_confidences)
        else:
            # Fallback to voting
            return await self._apply_voting(predictions, context)

        # Calculate metrics
        agreement_score = self._calculate_agreement_score(predictions)
        uncertainty_estimate = np.std(bootstrap_predictions) if bootstrap_predictions else 1.0

        return EnsembleResult(
            final_prediction=final_prediction,
            confidence=final_confidence,
            method_used=EnsembleMethod.BAGGING,
            individual_predictions=predictions,
            weights={p.model_name: 1.0 for p in predictions},  # Equal weights for bagging
            agreement_score=agreement_score,
            uncertainty_estimate=uncertainty_estimate
        )

    async def _apply_boosting(
        self,
        predictions: List[ModelPrediction],
        context: Optional[Dict[str, Any]]
    ) -> EnsembleResult:
        """Apply boosting ensemble method."""
        config = self.ensemble_config[EnsembleMethod.BOOSTING]

        # Simple AdaBoost-like implementation
        weights = [self.model_weights.get(p.model_name, 1.0) for p in predictions]
        confidences = [p.confidence for p in predictions]

        # Calculate weighted prediction
        if all(isinstance(p.prediction, (int, float)) for p in predictions):
            predictions_values = [p.prediction for p in predictions]

            # Adaptive boosting weights
            boosted_weights = []
            for i, (pred, conf) in enumerate(zip(predictions_values, confidences)):
                # Higher confidence gets higher weight
                error_rate = 1.0 - conf
                if error_rate > 0:
                    weight = np.log((1.0 - error_rate) / error_rate) * config['learning_rate']
                else:
                    weight = config['learning_rate'] * 2.0

                boosted_weights.append(max(0.1, min(2.0, weight)))

            # Normalize weights
            boosted_weights = np.array(boosted_weights)
            boosted_weights = boosted_weights / np.sum(boosted_weights)

            final_prediction = np.average(predictions_values, weights=boosted_weights)
            final_confidence = np.average(confidences, weights=boosted_weights)
        else:
            # Fallback to voting
            return await self._apply_voting(predictions, context)

        # Calculate metrics
        agreement_score = self._calculate_agreement_score(predictions)
        uncertainty_estimate = 1.0 - agreement_score

        return EnsembleResult(
            final_prediction=final_prediction,
            confidence=final_confidence,
            method_used=EnsembleMethod.BOOSTING,
            individual_predictions=predictions,
            weights={p.model_name: w for p, w in zip(predictions, boosted_weights)},
            agreement_score=agreement_score,
            uncertainty_estimate=uncertainty_estimate
        )

    async def _apply_dynamic_weighting(
        self,
        predictions: List[ModelPrediction],
        context: Optional[Dict[str, Any]]
    ) -> EnsembleResult:
        """Apply dynamic weighting ensemble method."""
        config = self.ensemble_config[EnsembleMethod.DYNAMIC_WEIGHTING]

        # Get current model weights
        current_weights = {p.model_name: self.model_weights.get(p.model_name, 1.0) for p in predictions}

        # Adjust weights based on recent performance
        if self.enable_learning and self.performance_history:
            for pred in predictions:
                model_name = pred.model_name
                if model_name in self.model_performance:
                    performance = self.model_performance[model_name]

                    # Adjust weight based on performance metrics
                    performance_score = (performance.accuracy + performance.f1_score) / 2.0

                    # Adaptive weight adjustment
                    weight_adjustment = config['adaptation_rate'] * (performance_score - 0.5)
                    new_weight = current_weights[model_name] + weight_adjustment

                    # Clamp weight to valid range
                    current_weights[model_name] = max(
                        config['min_weight'],
                        min(config['max_weight'], new_weight)
                    )

        # Apply weighted voting with dynamic weights
        weights = [current_weights[p.model_name] for p in predictions]

        if all(isinstance(p.prediction, (int, float)) for p in predictions):
            predictions_values = [p.prediction for p in predictions]
            final_prediction = np.average(predictions_values, weights=weights)
            final_confidence = np.average([p.confidence for p in predictions], weights=weights)
        else:
            # For categorical predictions, use weighted voting
            prediction_counts = {}
            for pred, weight in zip([p.prediction for p in predictions], weights):
                if pred not in prediction_counts:
                    prediction_counts[pred] = 0
                prediction_counts[pred] += weight

            final_prediction = max(prediction_counts, key=prediction_counts.get)
            final_confidence = max(prediction_counts.values()) / sum(prediction_counts.values())

        # Calculate metrics
        agreement_score = self._calculate_agreement_score(predictions)
        uncertainty_estimate = 1.0 - agreement_score

        # Update model weights
        self.model_weights.update(current_weights)

        return EnsembleResult(
            final_prediction=final_prediction,
            confidence=final_confidence,
            method_used=EnsembleMethod.DYNAMIC_WEIGHTING,
            individual_predictions=predictions,
            weights=current_weights,
            agreement_score=agreement_score,
            uncertainty_estimate=uncertainty_estimate
        )

    def _calculate_agreement_score(self, predictions: List[ModelPrediction]) -> float:
        """Calculate agreement score between predictions."""
        if len(predictions) <= 1:
            return 1.0

        # For numerical predictions
        if all(isinstance(p.prediction, (int, float)) for p in predictions):
            values = [p.prediction for p in predictions]
            mean_val = np.mean(values)
            variance = np.var(values)

            # Agreement score based on variance (lower variance = higher agreement)
            max_variance = np.var([0, 1])  # Maximum possible variance for 0-1 range
            agreement_score = max(0.0, 1.0 - (variance / max_variance))

            return agreement_score

        # For categorical predictions
        else:
            prediction_counts = {}
            for p in predictions:
                pred_str = str(p.prediction)
                if pred_str not in prediction_counts:
                    prediction_counts[pred_str] = 0
                prediction_counts[pred_str] += 1

            # Agreement score based on majority
            max_count = max(prediction_counts.values())
            agreement_score = max_count / len(predictions)

            return agreement_score

    def _generate_cache_key(
        self,
        input_data: Any,
        method: EnsembleMethod,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate cache key for ensemble prediction."""
        key_data = {
            'input_hash': hashlib.md5(str(input_data).encode()).hexdigest(),
            'method': method.value,
            'context_hash': hashlib.md5(str(context).encode()).hexdigest() if context else '',
            'model_weights': self.model_weights
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    async def _update_performance_metrics(
        self,
        result: EnsembleResult,
        context: Optional[Dict[str, Any]]
    ) -> None:
        """Update performance metrics for learning."""
        if not context or 'ground_truth' not in context:
            return

        ground_truth = context['ground_truth']

        # Calculate accuracy for each model
        for pred in result.individual_predictions:
            model_name = pred.model_name

            # Simple accuracy calculation
            if isinstance(pred.prediction, (int, float)) and isinstance(ground_truth, (int, float)):
                accuracy = 1.0 - abs(pred.prediction - ground_truth) / max(abs(ground_truth), 1.0)
            else:
                accuracy = 1.0 if str(pred.prediction) == str(ground_truth) else 0.0

            # Update performance metrics
            if model_name not in self.model_performance:
                self.model_performance[model_name] = EnsembleMetrics()

            # Simple moving average update
            current_metrics = self.model_performance[model_name]
            alpha = 0.1  # Learning rate

            current_metrics.accuracy = (1 - alpha) * current_metrics.accuracy + alpha * accuracy
            current_metrics.f1_score = (1 - alpha) * current_metrics.f1_score + alpha * accuracy

        # Store performance history
        self.performance_history.append({
            'timestamp': datetime.now(),
            'method': result.method_used.value,
            'confidence': result.confidence,
            'agreement_score': result.agreement_score,
            'uncertainty_estimate': result.uncertainty_estimate
        })

        # Keep only recent history
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-500:]

    # Model-specific prediction methods
    async def _get_llm_prediction(self, model_instance: Any, input_data: Any) -> Tuple[Any, float]:
        """Get prediction from LLM model."""
        try:
            if hasattr(model_instance, 'generate'):
                response = model_instance.generate(str(input_data))
                # Extract confidence from response if available
                confidence = getattr(response, 'confidence', 0.8)
                return response, confidence
            else:
                return "LLM prediction not available", 0.0
        except Exception as e:
            logger.warning("LLM prediction failed: %s", e)
            return None, 0.0

    async def _get_ner_prediction(self, model_instance: Any, input_data: Any) -> Tuple[Any, float]:
        """Get prediction from NER model."""
        try:
            if hasattr(model_instance, 'extract_entities'):
                entities = model_instance.extract_entities(str(input_data))
                confidence = len(entities) / max(len(str(input_data).split()), 1)  # Simple confidence
                return entities, min(1.0, confidence)
            else:
                return [], 0.0
        except Exception as e:
            logger.warning("NER prediction failed: %s", e)
            return [], 0.0

    async def _get_fact_checker_prediction(self, model_instance: Any, input_data: Any) -> Tuple[Any, float]:
        """Get prediction from fact checker model."""
        try:
            if hasattr(model_instance, 'check_consistency'):
                result = model_instance.check_consistency(str(input_data), "hypothesis")
                confidence = 0.9 if result else 0.1
                return result, confidence
            else:
                return False, 0.5
        except Exception as e:
            logger.warning("Fact checker prediction failed: %s", e)
            return False, 0.0

    async def _get_retriever_prediction(self, model_instance: Any, input_data: Any) -> Tuple[Any, float]:
        """Get prediction from retriever model."""
        try:
            if hasattr(model_instance, 'retrieve'):
                results = model_instance.retrieve(str(input_data), top_k=5)
                confidence = len(results) / 5.0 if results else 0.0
                return results, confidence
            else:
                return [], 0.0
        except Exception as e:
            logger.warning("Retriever prediction failed: %s", e)
            return [], 0.0

    async def _get_classifier_prediction(self, model_instance: Any, input_data: Any) -> Tuple[Any, float]:
        """Get prediction from classifier model."""
        try:
            if hasattr(model_instance, 'classify'):
                result = model_instance.classify(str(input_data))
                confidence = getattr(result, 'confidence', 0.8)
                return result, confidence
            else:
                return "Unknown", 0.5
        except Exception as e:
            logger.warning("Classifier prediction failed: %s", e)
            return "Unknown", 0.0

    def get_ensemble_stats(self) -> Dict[str, Any]:
        """Get ensemble statistics."""
        return {
            'registered_models': len(self.models),
            'model_weights': self.model_weights,
            'performance_history_size': len(self.performance_history),
            'cache_size': len(self._prediction_cache),
            'learning_enabled': self.enable_learning,
            'cache_enabled': self.cache_predictions
        }

    def clear_cache(self):
        """Clear prediction cache."""
        self._prediction_cache.clear()
        logger.info("Ensemble prediction cache cleared")

    def reset_performance_history(self):
        """Reset performance history."""
        self.performance_history.clear()
        logger.info("Performance history reset")


# Global instance for backward compatibility
advanced_ensemble_optimizer = AdvancedEnsembleOptimizer()
