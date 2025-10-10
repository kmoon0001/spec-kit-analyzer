"""Confidence Calibration Service for AI Model Outputs.
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV

This module provides advanced confidence calibration techniques to improve
the accuracy of confidence scores from AI models, making them more reliable
for user decision-making.
"""

import logging
import pickle
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class TemperatureScaling:
    """Temperature scaling for confidence calibration.

    Temperature scaling is a simple and effective post-processing technique
    that applies a single scalar parameter to the logits before softmax.
    """

    def __init__(self):
        self.temperature = 1.0
        self.is_fitted = False

    def fit(self, logits: np.ndarray, true_labels: np.ndarray) -> "TemperatureScaling":
        """Fit the temperature parameter using validation data.

        Args:
            logits: Raw model outputs before softmax
            true_labels: Ground truth binary labels (0 or 1)

        Returns:
            Self for method chaining

        """
        from scipy.optimize import minimize_scalar

        def temperature_loss(temp: float) -> float:
            """Negative log likelihood loss for temperature scaling."""
            scaled_logits = logits / temp
            probabilities = self._sigmoid(scaled_logits)
            # Avoid log(0) by clipping probabilities
            probabilities = np.clip(probabilities, 1e-7, 1 - 1e-7)
            loss = -np.mean(
                true_labels * np.log(probabilities) + (1 - true_labels) * np.log(1 - probabilities))
            return loss

        # Find optimal temperature
        result = minimize_scalar(temperature_loss, bounds=(0.1, 10.0), method="bounded")
        self.temperature = result.x
        self.is_fitted = True

        logger.info("Temperature scaling fitted with temperature: %.3f", self.temperature)
        return self

    def calibrate(self, logits: np.ndarray) -> np.ndarray:
        """Apply temperature scaling to calibrate confidence scores.

        Args:
            logits: Raw model outputs

        Returns:
            Calibrated probabilities

        """
        if not self.is_fitted:
            logger.warning("Temperature scaling not fitted. Using temperature=1.0")
            return self._sigmoid(logits)

        scaled_logits = logits / self.temperature
        return self._sigmoid(scaled_logits)

    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        """Numerically stable sigmoid function."""
        result = np.empty_like(x, dtype=float)

        positive_indices = x >= 0
        result[positive_indices] = 1.0 / (1.0 + np.exp(-x[positive_indices]))

        negative_indices = x < 0
        result[negative_indices] = np.exp(x[negative_indices]) / (1.0 + np.exp(x[negative_indices]))

        return result


class PlattScaling:
    """Platt scaling for confidence calibration.

    Platt scaling fits a sigmoid function to the model outputs using
    logistic regression.
    """

    def _select_best_method(
        self, logits_or_scores: np.ndarray, true_labels: np.ndarray, validation_split: float
    ) -> TemperatureScaling | PlattScaling | IsotonicCalibration:
        """Select the best calibration method based on validation performance."""
        # Split data for method selection
        n_samples = len(logits_or_scores)
        n_val = int(n_samples * validation_split)

        # Random split
        indices = np.random.permutation(n_samples)
        train_idx, val_idx = indices[n_val:], indices[:n_val]

        train_scores = logits_or_scores[train_idx]
        train_labels = true_labels[train_idx]
        val_scores = logits_or_scores[val_idx]
        val_labels = true_labels[val_idx]

        best_method = None
        best_score = float("inf")

        for method_name, calibrator in self.calibrators.items():
            try:
                # Fit calibrator on training data
                calibrator.fit(train_scores, train_labels)

                # Evaluate on validation data
                calibrated_scores = calibrator.calibrate(val_scores)

                # Calculate calibration error (Expected Calibration Error)
                ece = self._calculate_ece(calibrated_scores, val_labels)

                self.calibration_metrics[method_name] = {
                    "ece": ece,
                    "brier_score": self._calculate_brier_score(calibrated_scores, val_labels),
                }

                logger.info("%s calibration - ECE: {ece:.4f}", method_name)

                if ece < best_score:
                    best_score = ece
                    best_method = calibrator
                    self.method = method_name

            except Exception:
                logger.warning("Failed to fit %s calibrator: {e}", method_name)
                continue

        if best_method is None:
            logger.warning("All calibration methods failed. Using temperature scaling as fallback.")
            best_method = TemperatureScaling()
            best_method.fit(train_scores, train_labels)
            self.method = "temperature"

        return best_method

    @staticmethod
    def _calculate_ece(probabilities: np.ndarray, true_labels: np.ndarray, n_bins: int = 10) -> float:
        """Calculate Expected Calibration Error."""
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]

        ece = 0
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers, strict=False):
            in_bin = (probabilities > bin_lower) & (probabilities <= bin_upper)

            # Check if there are any elements in the bin before calculating mean
            if np.any(in_bin):  # Only calculate mean if there are elements in the bin
                prop_in_bin = in_bin.mean()
                accuracy_in_bin = true_labels[in_bin].mean()
                avg_confidence_in_bin = probabilities[in_bin].mean()
                ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
        return ece

    @staticmethod
    def _calculate_brier_score(probabilities: np.ndarray, true_labels: np.ndarray) -> float:
        """Calculate Brier score for calibration quality."""
        return np.mean((probabilities - true_labels) ** 2)

    def save(self, filepath: str | Path) -> None:
        """Save the fitted calibrator to disk."""
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted calibrator")

        save_data = {
            "method": self.method,
            "calibrator": self.best_calibrator,
            "metrics": self.calibration_metrics,
        }

        with open(filepath, "wb") as f:
            pickle.dump(save_data, f)

        logger.info("Calibrator saved to %s", filepath)

    def load(self, filepath: str | Path):
        """Load a fitted calibrator from disk."""
        with open(filepath, "rb") as f:
            save_data = pickle.load(f)

        self.method = save_data["method"]
        self.best_calibrator = save_data["calibrator"]
        self.calibration_metrics = save_data.get("metrics", {})
        self.is_fitted = True

        logger.info("Calibrator loaded from %s", filepath)
        return self

    def get_calibration_metrics(self) -> dict[str, dict[str, float]]:
        """Get calibration quality metrics for all methods."""
        return self.calibration_metrics.copy()
