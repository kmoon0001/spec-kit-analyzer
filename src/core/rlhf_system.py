"""
Reinforcement Learning from Human Feedback (RLHF) System
Implements continuous learning from human feedback for accuracy improvement
"""

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
import json
import uuid
import numpy as np
from pathlib import Path

from src.core.centralized_logging import get_logger, performance_tracker
from src.core.type_safety import Result, ErrorHandler

logger = get_logger(__name__)


class FeedbackType(Enum):
    """Types of human feedback."""
    CORRECTION = "correction"
    VALIDATION = "validation"
    IMPROVEMENT = "improvement"
    CLARIFICATION = "clarification"
    DISAGREEMENT = "disagreement"
    RATING = "rating"
    COMPARISON = "comparison"


class FeedbackStatus(Enum):
    """Status of feedback processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    IGNORED = "ignored"


class LearningPhase(Enum):
    """Phases of RLHF learning."""
    COLLECTION = "collection"
    REWARD_MODELING = "reward_modeling"
    POLICY_OPTIMIZATION = "policy_optimization"
    EVALUATION = "evaluation"


@dataclass
class HumanFeedback:
    """Human feedback data."""
    feedback_id: str
    user_id: str
    session_id: str
    feedback_type: FeedbackType
    original_response: str
    feedback_text: str
    rating: Optional[float] = None
    comparison_data: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RewardModel:
    """Reward model for RLHF."""
    model_id: str
    model_type: str
    parameters: Dict[str, Any]
    accuracy: float
    last_updated: datetime
    training_samples: int
    validation_samples: int


@dataclass
class PolicyUpdate:
    """Policy update from RLHF."""
    update_id: str
    learning_phase: LearningPhase
    feedback_samples: List[HumanFeedback]
    reward_scores: List[float]
    policy_changes: Dict[str, Any]
    performance_improvement: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RLHFResult:
    """Result from RLHF processing."""
    feedback_id: str
    reward_score: float
    learning_applied: bool
    policy_updated: bool
    performance_impact: float
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class RLHFSystem:
    """
    Reinforcement Learning from Human Feedback system.

    Features:
    - Continuous feedback collection
    - Reward model training and updating
    - Policy optimization based on feedback
    - Performance monitoring and evaluation
    - Adaptive learning strategies
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the RLHF system."""
        self.config_path = config_path or "config/rlhf_system.yaml"
        self.feedback_buffer: List[HumanFeedback] = []
        self.reward_models: Dict[str, RewardModel] = {}
        self.policy_updates: List[PolicyUpdate] = []
        self.learning_history: List[Dict[str, Any]] = []

        # Performance tracking
        self.total_feedback = 0
        self.processed_feedback = 0
        self.average_reward_score = 0.0
        self.policy_update_count = 0
        self.performance_improvement = 0.0

        # Learning parameters
        self.learning_rate = 0.001
        self.batch_size = 32
        self.update_frequency = 100  # Update every 100 feedback samples
        self.min_feedback_for_update = 50

        # Initialize components
        self._initialize_reward_models()
        self._initialize_learning_strategies()

        logger.info("RLHFSystem initialized with %d reward models", len(self.reward_models))

    def _initialize_reward_models(self) -> None:
        """Initialize reward models for different feedback types."""
        try:
            # General reward model
            self.reward_models["general"] = RewardModel(
                model_id="general_reward_model",
                model_type="neural_network",
                parameters={
                    "layers": [128, 64, 32],
                    "activation": "relu",
                    "dropout": 0.2,
                    "learning_rate": self.learning_rate
                },
                accuracy=0.0,
                last_updated=datetime.now(timezone.utc),
                training_samples=0,
                validation_samples=0
            )

            # Accuracy-specific reward model
            self.reward_models["accuracy"] = RewardModel(
                model_id="accuracy_reward_model",
                model_type="gradient_boosting",
                parameters={
                    "n_estimators": 100,
                    "max_depth": 6,
                    "learning_rate": 0.1,
                    "subsample": 0.8
                },
                accuracy=0.0,
                last_updated=datetime.now(timezone.utc),
                training_samples=0,
                validation_samples=0
            )

            # Relevance-specific reward model
            self.reward_models["relevance"] = RewardModel(
                model_id="relevance_reward_model",
                model_type="random_forest",
                parameters={
                    "n_estimators": 200,
                    "max_depth": 8,
                    "min_samples_split": 5,
                    "min_samples_leaf": 2
                },
                accuracy=0.0,
                last_updated=datetime.now(timezone.utc),
                training_samples=0,
                validation_samples=0
            )

            # Completeness-specific reward model
            self.reward_models["completeness"] = RewardModel(
                model_id="completeness_reward_model",
                model_type="support_vector_machine",
                parameters={
                    "kernel": "rbf",
                    "C": 1.0,
                    "gamma": "scale",
                    "probability": True
                },
                accuracy=0.0,
                last_updated=datetime.now(timezone.utc),
                training_samples=0,
                validation_samples=0
            )

            logger.info("Initialized %d reward models", len(self.reward_models))

        except Exception as e:
            logger.error("Failed to initialize reward models: %s", e)
            raise

    def _initialize_learning_strategies(self) -> None:
        """Initialize learning strategies."""
        try:
            self.learning_strategies = {
                "online_learning": {
                    "type": "online",
                    "description": "Continuous learning from individual feedback",
                    "update_frequency": 1,
                    "learning_rate": 0.01,
                    "applicable_feedback_types": [FeedbackType.RATING, FeedbackType.CORRECTION]
                },
                "batch_learning": {
                    "type": "batch",
                    "description": "Batch learning from accumulated feedback",
                    "update_frequency": self.update_frequency,
                    "learning_rate": self.learning_rate,
                    "applicable_feedback_types": [FeedbackType.VALIDATION, FeedbackType.IMPROVEMENT]
                },
                "comparative_learning": {
                    "type": "comparative",
                    "description": "Learning from comparative feedback",
                    "update_frequency": 10,
                    "learning_rate": 0.005,
                    "applicable_feedback_types": [FeedbackType.COMPARISON, FeedbackType.DISAGREEMENT]
                },
                "adaptive_learning": {
                    "type": "adaptive",
                    "description": "Adaptive learning based on performance",
                    "update_frequency": "dynamic",
                    "learning_rate": "adaptive",
                    "applicable_feedback_types": [FeedbackType.CLARIFICATION, FeedbackType.IMPROVEMENT]
                }
            }

            logger.info("Initialized %d learning strategies", len(self.learning_strategies))

        except Exception as e:
            logger.error("Failed to initialize learning strategies: %s", e)
            raise

    async def submit_feedback(
        self,
        feedback: HumanFeedback,
        timeout_seconds: float = 30.0
    ) -> Result[RLHFResult, str]:
        """Submit human feedback for processing."""
        try:
            start_time = datetime.now()
            self.total_feedback += 1

            # Add feedback to buffer
            self.feedback_buffer.append(feedback)

            # Process feedback immediately for online learning
            if self._should_process_immediately(feedback):
                result = await self._process_feedback_immediately(feedback, timeout_seconds)
            else:
                result = await self._process_feedback_batch(feedback, timeout_seconds)

            # Check if batch update is needed
            if len(self.feedback_buffer) >= self.update_frequency:
                await self._perform_batch_update(timeout_seconds)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Create RLHF result
            rlhf_result = RLHFResult(
                feedback_id=feedback.feedback_id,
                reward_score=result["reward_score"],
                learning_applied=result["learning_applied"],
                policy_updated=result["policy_updated"],
                performance_impact=result["performance_impact"],
                processing_time_ms=processing_time,
                metadata={
                    "feedback_type": feedback.feedback_type.value,
                    "user_id": feedback.user_id,
                    "timestamp": datetime.now(timezone.utc)
                }
            )

            # Update performance metrics
            self._update_performance_metrics(rlhf_result)

            self.processed_feedback += 1
            return Result.success(rlhf_result)

        except Exception as e:
            logger.error("Feedback submission failed: %s", e)
            return Result.error(f"Feedback submission failed: {e}")

    def _should_process_immediately(self, feedback: HumanFeedback) -> bool:
        """Determine if feedback should be processed immediately."""
        immediate_types = [FeedbackType.RATING, FeedbackType.CORRECTION]
        return feedback.feedback_type in immediate_types

    async def _process_feedback_immediately(
        self,
        feedback: HumanFeedback,
        timeout_seconds: float
    ) -> Dict[str, Any]:
        """Process feedback immediately for online learning."""
        try:
            # Calculate reward score
            reward_score = await self._calculate_reward_score(feedback)

            # Apply online learning
            learning_applied = await self._apply_online_learning(feedback, reward_score)

            # Update reward models
            policy_updated = await self._update_reward_models(feedback, reward_score)

            # Calculate performance impact
            performance_impact = self._calculate_performance_impact(feedback, reward_score)

            return {
                "reward_score": reward_score,
                "learning_applied": learning_applied,
                "policy_updated": policy_updated,
                "performance_impact": performance_impact
            }

        except Exception as e:
            logger.error("Immediate feedback processing failed: %s", e)
            return {
                "reward_score": 0.0,
                "learning_applied": False,
                "policy_updated": False,
                "performance_impact": 0.0
            }

    async def _process_feedback_batch(
        self,
        feedback: HumanFeedback,
        timeout_seconds: float
    ) -> Dict[str, Any]:
        """Process feedback for batch learning."""
        try:
            # Calculate reward score
            reward_score = await self._calculate_reward_score(feedback)

            # Store for batch processing
            learning_applied = False
            policy_updated = False

            # Calculate performance impact
            performance_impact = self._calculate_performance_impact(feedback, reward_score)

            return {
                "reward_score": reward_score,
                "learning_applied": learning_applied,
                "policy_updated": policy_updated,
                "performance_impact": performance_impact
            }

        except Exception as e:
            logger.error("Batch feedback processing failed: %s", e)
            return {
                "reward_score": 0.0,
                "learning_applied": False,
                "policy_updated": False,
                "performance_impact": 0.0
            }

    async def _calculate_reward_score(self, feedback: HumanFeedback) -> float:
        """Calculate reward score for feedback."""
        try:
            base_score = 0.5

            # Adjust based on feedback type
            type_adjustments = {
                FeedbackType.CORRECTION: 0.3,
                FeedbackType.VALIDATION: 0.2,
                FeedbackType.IMPROVEMENT: 0.4,
                FeedbackType.CLARIFICATION: 0.1,
                FeedbackType.DISAGREEMENT: -0.2,
                FeedbackType.RATING: 0.0,
                FeedbackType.COMPARISON: 0.2
            }

            type_adjustment = type_adjustments.get(feedback.feedback_type, 0.0)

            # Adjust based on rating if available
            rating_adjustment = 0.0
            if feedback.rating is not None:
                rating_adjustment = (feedback.rating - 0.5) * 0.5

            # Adjust based on feedback text length (more detailed feedback = higher score)
            text_length_factor = min(1.0, len(feedback.feedback_text) / 200.0)

            # Calculate final reward score
            reward_score = base_score + type_adjustment + rating_adjustment + (text_length_factor * 0.1)

            return min(1.0, max(0.0, reward_score))

        except Exception as e:
            logger.error("Reward score calculation failed: %s", e)
            return 0.5

    async def _apply_online_learning(
        self,
        feedback: HumanFeedback,
        reward_score: float
    ) -> bool:
        """Apply online learning based on feedback."""
        try:
            # Determine appropriate reward model
            reward_model_id = self._select_reward_model(feedback)
            reward_model = self.reward_models[reward_model_id]

            # Simulate online learning update
            await asyncio.sleep(0.01)  # Simulate processing time

            # Update model parameters (simplified)
            if reward_model.model_type == "neural_network":
                # Update neural network parameters
                reward_model.parameters["learning_rate"] *= 0.999  # Decay learning rate
                reward_model.training_samples += 1

            elif reward_model.model_type == "gradient_boosting":
                # Update gradient boosting parameters
                reward_model.parameters["n_estimators"] = min(200, reward_model.parameters["n_estimators"] + 1)
                reward_model.training_samples += 1

            # Update accuracy (simplified)
            reward_model.accuracy = min(1.0, reward_model.accuracy + (reward_score * 0.01))
            reward_model.last_updated = datetime.now(timezone.utc)

            logger.info("Applied online learning to %s model", reward_model_id)
            return True

        except Exception as e:
            logger.error("Online learning application failed: %s", e)
            return False

    async def _update_reward_models(
        self,
        feedback: HumanFeedback,
        reward_score: float
    ) -> bool:
        """Update reward models based on feedback."""
        try:
            updated_models = 0

            for model_id, reward_model in self.reward_models.items():
                try:
                    # Update model based on feedback type
                    if self._should_update_model(model_id, feedback):
                        await self._update_specific_model(reward_model, feedback, reward_score)
                        updated_models += 1

                except Exception as e:
                    logger.warning("Failed to update model %s: %s", model_id, e)
                    continue

            logger.info("Updated %d reward models", updated_models)
            return updated_models > 0

        except Exception as e:
            logger.error("Reward model update failed: %s", e)
            return False

    def _select_reward_model(self, feedback: HumanFeedback) -> str:
        """Select appropriate reward model for feedback."""
        if feedback.feedback_type == FeedbackType.CORRECTION:
            return "accuracy"
        elif feedback.feedback_type == FeedbackType.VALIDATION:
            return "relevance"
        elif feedback.feedback_type == FeedbackType.IMPROVEMENT:
            return "completeness"
        else:
            return "general"

    def _should_update_model(self, model_id: str, feedback: HumanFeedback) -> bool:
        """Determine if a model should be updated based on feedback."""
        if model_id == "general":
            return True
        elif model_id == "accuracy" and feedback.feedback_type == FeedbackType.CORRECTION:
            return True
        elif model_id == "relevance" and feedback.feedback_type == FeedbackType.VALIDATION:
            return True
        elif model_id == "completeness" and feedback.feedback_type == FeedbackType.IMPROVEMENT:
            return True
        else:
            return False

    async def _update_specific_model(
        self,
        reward_model: RewardModel,
        feedback: HumanFeedback,
        reward_score: float
    ) -> None:
        """Update a specific reward model."""
        try:
            # Update training samples
            reward_model.training_samples += 1

            # Update accuracy based on reward score
            accuracy_update = reward_score * 0.01
            reward_model.accuracy = min(1.0, reward_model.accuracy + accuracy_update)

            # Update last updated timestamp
            reward_model.last_updated = datetime.now(timezone.utc)

            logger.debug("Updated model %s with accuracy %.3f",
                        reward_model.model_id, reward_model.accuracy)

        except Exception as e:
            logger.error("Specific model update failed: %s", e)
            raise

    def _calculate_performance_impact(
        self,
        feedback: HumanFeedback,
        reward_score: float
    ) -> float:
        """Calculate performance impact of feedback."""
        try:
            # Base impact
            base_impact = reward_score * 0.1

            # Adjust based on feedback type
            type_impacts = {
                FeedbackType.CORRECTION: 0.2,
                FeedbackType.VALIDATION: 0.1,
                FeedbackType.IMPROVEMENT: 0.15,
                FeedbackType.CLARIFICATION: 0.05,
                FeedbackType.DISAGREEMENT: -0.1,
                FeedbackType.RATING: 0.08,
                FeedbackType.COMPARISON: 0.12
            }

            type_impact = type_impacts.get(feedback.feedback_type, 0.0)

            # Calculate total impact
            total_impact = base_impact + type_impact

            return min(0.5, max(-0.2, total_impact))  # Cap between -20% and +50%

        except Exception as e:
            logger.error("Performance impact calculation failed: %s", e)
            return 0.0

    async def _perform_batch_update(self, timeout_seconds: float) -> None:
        """Perform batch update on accumulated feedback."""
        try:
            if len(self.feedback_buffer) < self.min_feedback_for_update:
                return

            logger.info("Performing batch update with %d feedback samples", len(self.feedback_buffer))

            # Create policy update
            policy_update = PolicyUpdate(
                update_id=str(uuid.uuid4()),
                learning_phase=LearningPhase.POLICY_OPTIMIZATION,
                feedback_samples=self.feedback_buffer.copy(),
                reward_scores=[await self._calculate_reward_score(f) for f in self.feedback_buffer],
                policy_changes=self._calculate_policy_changes(),
                performance_improvement=self._calculate_batch_improvement(),
                metadata={
                    "batch_size": len(self.feedback_buffer),
                    "update_timestamp": datetime.now(timezone.utc)
                }
            )

            # Apply batch learning
            await self._apply_batch_learning(policy_update)

            # Store policy update
            self.policy_updates.append(policy_update)
            self.policy_update_count += 1

            # Clear feedback buffer
            self.feedback_buffer.clear()

            logger.info("Batch update completed successfully")

        except Exception as e:
            logger.error("Batch update failed: %s", e)

    def _calculate_policy_changes(self) -> Dict[str, Any]:
        """Calculate policy changes from batch feedback."""
        try:
            # Analyze feedback patterns
            feedback_types = [f.feedback_type.value for f in self.feedback_buffer]
            type_counts = {t: feedback_types.count(t) for t in set(feedback_types)}

            # Calculate changes based on feedback patterns
            changes = {
                "accuracy_weight": type_counts.get("correction", 0) * 0.01,
                "relevance_weight": type_counts.get("validation", 0) * 0.01,
                "completeness_weight": type_counts.get("improvement", 0) * 0.01,
                "learning_rate_adjustment": len(self.feedback_buffer) * 0.001
            }

            return changes

        except Exception as e:
            logger.error("Policy changes calculation failed: %s", e)
            return {}

    def _calculate_batch_improvement(self) -> float:
        """Calculate improvement from batch feedback."""
        try:
            if not self.feedback_buffer:
                return 0.0

            # Calculate average reward score
            total_reward = sum(await self._calculate_reward_score(f) for f in self.feedback_buffer)
            avg_reward = total_reward / len(self.feedback_buffer)

            # Convert to improvement percentage
            improvement = (avg_reward - 0.5) * 0.2  # Scale to percentage

            return min(0.1, max(-0.05, improvement))  # Cap between -5% and +10%

        except Exception as e:
            logger.error("Batch improvement calculation failed: %s", e)
            return 0.0

    async def _apply_batch_learning(self, policy_update: PolicyUpdate) -> None:
        """Apply batch learning based on policy update."""
        try:
            # Update all reward models
            for model_id, reward_model in self.reward_models.items():
                try:
                    # Apply policy changes to model
                    await self._apply_policy_changes_to_model(reward_model, policy_update.policy_changes)

                except Exception as e:
                    logger.warning("Failed to apply policy changes to model %s: %s", model_id, e)
                    continue

            # Update learning parameters
            self.learning_rate = min(0.01, self.learning_rate + policy_update.policy_changes.get("learning_rate_adjustment", 0))

            logger.info("Applied batch learning with improvement %.3f", policy_update.performance_improvement)

        except Exception as e:
            logger.error("Batch learning application failed: %s", e)

    async def _apply_policy_changes_to_model(
        self,
        reward_model: RewardModel,
        policy_changes: Dict[str, Any]
    ) -> None:
        """Apply policy changes to a specific model."""
        try:
            # Update model parameters based on policy changes
            if "learning_rate_adjustment" in policy_changes:
                if "learning_rate" in reward_model.parameters:
                    reward_model.parameters["learning_rate"] *= (1 + policy_changes["learning_rate_adjustment"])

            # Update training samples
            reward_model.training_samples += len(self.feedback_buffer)

            # Update accuracy
            accuracy_improvement = policy_changes.get("accuracy_weight", 0) * 0.1
            reward_model.accuracy = min(1.0, reward_model.accuracy + accuracy_improvement)

            # Update last updated timestamp
            reward_model.last_updated = datetime.now(timezone.utc)

        except Exception as e:
            logger.error("Policy changes application to model failed: %s", e)
            raise

    def _update_performance_metrics(self, result: RLHFResult) -> None:
        """Update performance metrics."""
        try:
            # Update average reward score
            if self.total_feedback > 0:
                self.average_reward_score = (
                    (self.average_reward_score * (self.total_feedback - 1) + result.reward_score)
                    / self.total_feedback
                )

            # Update performance improvement
            if self.total_feedback > 0:
                self.performance_improvement = (
                    (self.performance_improvement * (self.total_feedback - 1) + result.performance_impact)
                    / self.total_feedback
                )

            # Store learning history
            self.learning_history.append({
                "timestamp": datetime.now(timezone.utc),
                "reward_score": result.reward_score,
                "performance_impact": result.performance_impact,
                "learning_applied": result.learning_applied,
                "policy_updated": result.policy_updated
            })

            # Keep only recent history
            if len(self.learning_history) > 1000:
                self.learning_history = self.learning_history[-500:]

        except Exception as e:
            logger.error("Performance metrics update failed: %s", e)

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "total_feedback": self.total_feedback,
            "processed_feedback": self.processed_feedback,
            "success_rate": self.processed_feedback / max(1, self.total_feedback),
            "average_reward_score": self.average_reward_score,
            "policy_update_count": self.policy_update_count,
            "performance_improvement": self.performance_improvement,
            "feedback_buffer_size": len(self.feedback_buffer),
            "total_reward_models": len(self.reward_models),
            "learning_history_size": len(self.learning_history),
            "reward_model_status": {
                model_id: {
                    "accuracy": model.accuracy,
                    "training_samples": model.training_samples,
                    "last_updated": model.last_updated.isoformat()
                }
                for model_id, model in self.reward_models.items()
            }
        }


# Global instance
rlhf_system = RLHFSystem()
