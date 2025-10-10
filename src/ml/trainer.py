"""Module for training and fine-tuning machine learning models.

This module implements the Human-in-the-Loop (HITL) learning process,
where user feedback is used to improve confidence calibration and other ML models.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.calibration_trainer import CalibrationTrainer
from src.core.confidence_calibrator import ConfidenceCalibrator

logger = logging.getLogger(__name__)


class MLTrainingPipeline:
    """Manages the complete machine learning training pipeline."""

    def __init__(self, calibration_trainer: CalibrationTrainer | None = None, models_dir: str = "models"):
        """Initialize the ML training pipeline.

        Args:
            calibration_trainer: CalibrationTrainer instance for feedback collection
            models_dir: Directory to store trained models

        """
        self.calibration_trainer = calibration_trainer or CalibrationTrainer()
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)

        # Training configuration
        self.min_samples_for_training = 50
        self.training_interval_days = 7
        self.performance_threshold = 0.05  # Minimum ECE improvement required

    async def fine_tune_model_with_feedback(
        self, db: AsyncSession | None = None, force_retrain: bool = False
    ) -> dict[str, Any]:
        """Orchestrates the model fine-tuning process using user feedback.

        This implementation focuses on confidence calibration improvement using
        the CalibrationTrainer system we built.

        Args:
            db: Database session (for future expansion)
            force_retrain: Force retraining even if not enough time has passed

        Returns:
            Dictionary with training results and metrics

        """
        logger.info("Starting ML model fine-tuning process based on user feedback...")

        try:
            # Step 1: Check if training is needed
            if not force_retrain and not self._should_retrain():
                return {
                    "status": "skipped",
                    "message": "Training not needed - insufficient time or data",
                    "next_training_due": self._get_next_training_time(),
                }

            # Step 2: Fetch and prepare training data
            training_data = self.calibration_trainer.get_training_data(
                min_samples=self.min_samples_for_training)

            if len(training_data) < self.min_samples_for_training:
                logger.warning(
                    "Insufficient training data: %s samples ",
                    len(training_data),
                    f"(need {self.min_samples_for_training})")
                return {
                    "status": "insufficient_data",
                    "message": f"Need {self.min_samples_for_training} samples, have {len(training_data)}",
                    "samples_collected": len(training_data),
                }

            logger.info("Preparing to train with %s feedback samples", len(training_data))

            # Step 3: Train new confidence calibrator
            results = await self._train_confidence_calibrator(training_data)

            # Step 4: Evaluate the new model
            evaluation_results = await self._evaluate_calibrator(results["calibrator"], training_data)

            # Step 5: Deploy if performance is acceptable
            deployment_results = await self._deploy_if_improved(
                results["calibrator"],
                evaluation_results)

            # Step 6: Update training metadata
            self._update_training_metadata(evaluation_results)

            final_results = {
                "status": "completed",
                "training_results": results,
                "evaluation_results": evaluation_results,
                "deployment_results": deployment_results,
                "samples_used": len(training_data),
                "timestamp": datetime.now().isoformat(),
            }

            logger.info("ML training pipeline completed successfully: %s", final_results["status"])
            return final_results

        except Exception as e:
            logger.error("ML training pipeline failed: %s", e, exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _train_confidence_calibrator(self, training_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Train a new confidence calibrator with the collected feedback data."""
        logger.info("Training new confidence calibrator...")

        # Create new calibrator
        new_calibrator = ConfidenceCalibrator(method="auto")

        # Prepare training arrays
        import numpy as np

        confidences = np.array([item["confidence"] for item in training_data])
        labels = np.array([item["is_correct"] for item in training_data])

        # Train the calibrator
        new_calibrator.fit(confidences, labels)

        # Get training metrics
        metrics = new_calibrator.get_calibration_metrics()

        logger.info("Calibrator trained using method: %s", new_calibrator.method)
        logger.info("Training metrics: %s", metrics)

        return {
            "calibrator": new_calibrator,
            "method_used": new_calibrator.method,
            "training_metrics": metrics,
            "samples_used": len(training_data),
        }

    async def _evaluate_calibrator(
        self, calibrator: ConfidenceCalibrator, training_data: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Evaluate the newly trained calibrator."""
        logger.info("Evaluating new confidence calibrator...")

        # Use a portion of data for evaluation (simple train/test split)
        split_idx = int(len(training_data) * 0.8)
        eval_data = training_data[split_idx:]

        if len(eval_data) < 10:
            logger.warning("Insufficient evaluation data, using training metrics")
            return calibrator.get_calibration_metrics()

        # Evaluate on held-out data
        eval_confidences = np.array([item["confidence"] for item in eval_data])
        eval_labels = np.array([item["is_correct"] for item in eval_data])

        # Get calibrated scores
        calibrated_confidences = calibrator.calibrate(eval_confidences)

        # Calculate evaluation metrics

        raw_ece = ConfidenceCalibrator._calculate_ece(eval_confidences, eval_labels)
        calibrated_ece = ConfidenceCalibrator._calculate_ece(calibrated_confidences, eval_labels)

        raw_brier = ConfidenceCalibrator._calculate_brier_score(eval_confidences, eval_labels)
        calibrated_brier = ConfidenceCalibrator._calculate_brier_score(calibrated_confidences, eval_labels)

        improvement_ece = (raw_ece - calibrated_ece) / raw_ece if raw_ece > 0 else 0
        improvement_brier = (raw_brier - calibrated_brier) / raw_brier if raw_brier > 0 else 0

        evaluation_results = {
            "evaluation_samples": len(eval_data),
            "raw_ece": float(raw_ece),
            "calibrated_ece": float(calibrated_ece),
            "ece_improvement": float(improvement_ece),
            "raw_brier": float(raw_brier),
            "calibrated_brier": float(calibrated_brier),
            "brier_improvement": float(improvement_brier),
            "method_used": calibrator.method,
        }

        logger.info(
            "Evaluation results: ECE improvement %.1%%, Brier improvement %.1%%",
            improvement_ece * 100,
            improvement_brier * 100)

        return evaluation_results

    async def _deploy_if_improved(
        self, calibrator: ConfidenceCalibrator, evaluation_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Deploy the new calibrator if it shows sufficient improvement."""

        ece_improvement = evaluation_results.get("ece_improvement", 0)

        if ece_improvement >= self.performance_threshold:
            # Save the new calibrator
            model_path = self.models_dir / f"confidence_calibrator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            calibrator.save(model_path)

            # Also save as the current production model
            production_path = self.models_dir / "confidence_calibrator.pkl"
            calibrator.save(production_path)

            logger.info("Deployed new calibrator with %.1%% ECE improvement", ece_improvement * 100)

            return {
                "deployed": True,
                "model_path": str(model_path),
                "production_path": str(production_path),
                "improvement": ece_improvement,
                "reason": f"ECE improvement {ece_improvement * 100} exceeds threshold {self.performance_threshold * 100}",
            }
        logger.info(
            "New calibrator not deployed - improvement %.1%% below threshold %.1%%",
            ece_improvement * 100,
            self.performance_threshold * 100)

        return {
            "deployed": False,
            "improvement": ece_improvement,
            "threshold": self.performance_threshold,
            "reason": f"Improvement {ece_improvement * 100} below threshold {self.performance_threshold * 100}",
        }

    def _should_retrain(self) -> bool:
        """Check if retraining is needed based on time and data availability."""
        # Check if enough time has passed since last training
        metadata_path = self.models_dir / "training_metadata.json"

        if metadata_path.exists():
            import json

            try:
                with open(metadata_path) as f:
                    metadata = json.load(f)

                last_training = datetime.fromisoformat(metadata.get("last_training", "2000-01-01"))
                time_since_training = datetime.now() - last_training

                if time_since_training.days < self.training_interval_days:
                    logger.info("Training not due for %s days", self.training_interval_days - time_since_training.days)
                    return False

            except (FileNotFoundError, PermissionError, OSError) as e:
                logger.warning("Could not read training metadata: %s", e)

        # Check if we have enough new data
        training_data = self.calibration_trainer.get_training_data(min_samples=1)

        if len(training_data) < self.min_samples_for_training:
            logger.info("Insufficient training data: %s/{self.min_samples_for_training}", len(training_data))
            return False

        return True

    def _get_next_training_time(self) -> str:
        """Get the next scheduled training time."""
        metadata_path = self.models_dir / "training_metadata.json"

        if metadata_path.exists():
            try:
                with open(metadata_path) as f:
                    metadata = json.load(f)

                last_training = datetime.fromisoformat(metadata.get("last_training", "2000-01-01"))
                next_training = last_training + timedelta(days=self.training_interval_days)
                return next_training.isoformat()

            except (json.JSONDecodeError, PermissionError, ValueError, FileNotFoundError, OSError):
                pass

        # Default to now if no metadata
        return datetime.now().isoformat()

    def _update_training_metadata(self, evaluation_results: dict[str, Any]) -> None:
        """Update training metadata with latest results."""
        metadata_path = self.models_dir / "training_metadata.json"

        metadata = {
            "last_training": datetime.now().isoformat(),
            "last_evaluation_results": evaluation_results,
            "training_count": 1,
        }

        # Load existing metadata if available
        if metadata_path.exists():
            try:
                with open(metadata_path) as f:
                    existing_metadata = json.load(f)
                metadata["training_count"] = existing_metadata.get("training_count", 0) + 1
            except (json.JSONDecodeError, PermissionError, ValueError, FileNotFoundError, OSError):
                pass

        # Save updated metadata
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info("Updated training metadata (training #%s)", metadata["training_count"])


# Backward compatibility function
# Backward compatibility function
# Backward compatibility function
async def fine_tune_model_with_feedback(db: AsyncSession | None = None) -> dict[str, Any]:
    """Legacy function for backward compatibility.

    This now uses the new MLTrainingPipeline implementation.
    """
    pipeline = MLTrainingPipeline()
    return await pipeline.fine_tune_model_with_feedback(db)
