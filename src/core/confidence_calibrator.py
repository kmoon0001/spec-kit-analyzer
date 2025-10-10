"""Confidence Calibration Service for AI Model Outputs.

This module provides advanced confidence calibration techniques to improve
the accuracy of confidence scores from AI models, making them more reliable
for user decision-making.
"""

import numpy as np
import logging
from typing import Dict, Union, Optional, Any
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


class TemperatureScaling:
    """Temperature scaling for confidence calibration.
    
    Temperature scaling is a simple and effective post-processing technique
    that applies a single scalar parameter to the logits before softmax.
    """
    
    def __init__(self):
        self.temperature = 1.0
        self.is_fitted = False
    
    def fit(self, logits: np.ndarray, true_labels: np.ndarray) -> 'TemperatureScaling':
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
                true_labels * np.log(probabilities) + 
                (1 - true_labels) * np.log(1 - probabilities)
            )
            return loss
        
        # Find optimal temperature
        result = minimize_scalar(temperature_loss, bounds=(0.1, 10.0), method='bounded')
        self.temperature = result.x
        self.is_fitted = True
        
        logger.info(f"Temperature scaling fitted with temperature: {self.temperature:.3f}")
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
    
    def __init__(self):
        self.platt_model = LogisticRegression()
        self.is_fitted = False
    
    def fit(self, scores: np.ndarray, true_labels: np.ndarray) -> 'PlattScaling':
        """Fit Platt scaling using validation data.
        
        Args:
            scores: Model confidence scores or logits
            true_labels: Ground truth binary labels (0 or 1)
            
        Returns:
            Self for method chaining
        """
        # Reshape for sklearn
        scores_reshaped = scores.reshape(-1, 1)
        
        # Fit logistic regression
        self.platt_model.fit(scores_reshaped, true_labels)
        self.is_fitted = True
        
        # Calculate cross-validation score for quality assessment
        cv_score = cross_val_score(self.platt_model, scores_reshaped, true_labels, cv=3)
        logger.info(f"Platt scaling fitted with CV accuracy: {cv_score.mean():.3f} ± {cv_score.std():.3f}")
        
        return self
    
    def calibrate(self, scores: np.ndarray) -> np.ndarray:
        """Apply Platt scaling to calibrate confidence scores.
        
        Args:
            scores: Model confidence scores or logits
            
        Returns:
            Calibrated probabilities
        """
        if not self.is_fitted:
            logger.warning("Platt scaling not fitted. Returning original scores.")
            return scores
        
        scores_reshaped = scores.reshape(-1, 1)
        return self.platt_model.predict_proba(scores_reshaped)[:, 1]


class IsotonicCalibration:
    """Isotonic regression for confidence calibration.
    
    Isotonic calibration is a non-parametric method that fits a
    monotonic function to the validation data.
    """
    
    def __init__(self):
        self.isotonic_model = IsotonicRegression(out_of_bounds='clip')
        self.is_fitted = False
    
    def fit(self, scores: np.ndarray, true_labels: np.ndarray) -> 'IsotonicCalibration':
        """Fit isotonic regression using validation data.
        
        Args:
            scores: Model confidence scores
            true_labels: Ground truth binary labels (0 or 1)
            
        Returns:
            Self for method chaining
        """
        self.isotonic_model.fit(scores, true_labels)
        self.is_fitted = True
        
        logger.info("Isotonic calibration fitted successfully")
        return self
    
    def calibrate(self, scores: np.ndarray) -> np.ndarray:
        """Apply isotonic calibration to confidence scores.
        
        Args:
            scores: Model confidence scores
            
        Returns:
            Calibrated probabilities
        """
        if not self.is_fitted:
            logger.warning("Isotonic calibration not fitted. Returning original scores.")
            return scores
        
        return self.isotonic_model.predict(scores)


class ConfidenceCalibrator:
    """Main confidence calibration service.
    
    This class provides a unified interface for different calibration methods
    and handles the selection of the best method based on validation data.
    """
    
    def __init__(self, method: str = 'auto'):
        """
        Initialize the confidence calibrator.
        
        Args:
            method: Calibration method ('temperature', 'platt', 'isotonic', 'auto')
        """
        self.method = method
        self.calibrators = {
            'temperature': TemperatureScaling(),
            'platt': PlattScaling(),
            'isotonic': IsotonicCalibration()
        }
        self.best_calibrator: Optional[Union[TemperatureScaling, PlattScaling, IsotonicCalibration]] = None
        self.is_fitted = False
        self.calibration_metrics: Dict[str, Any] = {}
    
    def fit(self, 
            logits_or_scores: np.ndarray, 
            true_labels: np.ndarray,
            validation_split: float = 0.2) -> 'ConfidenceCalibrator':
        """Fit the confidence calibrator.
        
        Args:
            logits_or_scores: Raw model outputs or confidence scores
            true_labels: Ground truth binary labels
            validation_split: Fraction of data to use for method selection
            
        Returns:
            Self for method chaining
        """
        if self.method == 'auto':
            self.best_calibrator = self._select_best_method(
                logits_or_scores, true_labels, validation_split
            )
        else:
            if self.method not in self.calibrators:
                raise ValueError(f"Unknown calibration method: {self.method}")
            
            self.best_calibrator = self.calibrators[self.method]
            self.best_calibrator.fit(logits_or_scores, true_labels)
        
        self.is_fitted = True
        logger.info(f"Confidence calibrator fitted using method: {self.method}")
        return self
    
    def calibrate(self, logits_or_scores: np.ndarray) -> np.ndarray:
        """Calibrate confidence scores.
        
        Args:
            logits_or_scores: Raw model outputs or confidence scores
            
        Returns:
            Calibrated confidence scores
        """
        if not self.is_fitted:
            logger.warning("Calibrator not fitted. Returning original scores.")
            return logits_or_scores
        
        return self.best_calibrator.calibrate(logits_or_scores)
    
    def _select_best_method(self, 
                           logits_or_scores: np.ndarray, 
                           true_labels: np.ndarray,
                           validation_split: float) -> Union[TemperatureScaling, PlattScaling, IsotonicCalibration]:
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
        best_score = float('inf')
        
        for method_name, calibrator in self.calibrators.items():
            try:
                # Fit calibrator on training data
                calibrator.fit(train_scores, train_labels)
                
                # Evaluate on validation data
                calibrated_scores = calibrator.calibrate(val_scores)
                
                # Calculate calibration error (Expected Calibration Error)
                ece = self._calculate_ece(calibrated_scores, val_labels)
                
                self.calibration_metrics[method_name] = {
                    'ece': ece,
                    'brier_score': self._calculate_brier_score(calibrated_scores, val_labels)
                }
                
                logger.info(f"{method_name} calibration - ECE: {ece:.4f}")
                
                if ece < best_score:
                    best_score = ece
                    best_method = calibrator
                    self.method = method_name
                    
            except Exception as e:
                logger.warning(f"Failed to fit {method_name} calibrator: {e}")
                continue
        
        if best_method is None:
            logger.warning("All calibration methods failed. Using temperature scaling as fallback.")
            best_method = TemperatureScaling()
            best_method.fit(train_scores, train_labels)
            self.method = 'temperature'
        
        return best_method
    
    @staticmethod
    def _calculate_ece(probabilities: np.ndarray, 
                       true_labels: np.ndarray, 
                       n_bins: int = 10) -> float:
        """Calculate Expected Calibration Error."""
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        ece = 0
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
                        in_bin = (probabilities > bin_lower) & (probabilities <= bin_upper)
                        
                        # Check if there are any elements in the bin before calculating mean
                        if np.any(in_bin): # Only calculate mean if there are elements in the bin
                            prop_in_bin = in_bin.mean()
                            accuracy_in_bin = true_labels[in_bin].mean()
                            avg_confidence_in_bin = probabilities[in_bin].mean()
                            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin        
        return ece
    
    @staticmethod
    def _calculate_brier_score(probabilities: np.ndarray, 
                              true_labels: np.ndarray) -> float:
        """Calculate Brier score for calibration quality."""
        return np.mean((probabilities - true_labels) ** 2)
    
    def save(self, filepath: Union[str, Path]) -> None:
        """Save the fitted calibrator to disk."""
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted calibrator")
        
        save_data = {
            'method': self.method,
            'calibrator': self.best_calibrator,
            'metrics': self.calibration_metrics
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(save_data, f)
        
        logger.info(f"Calibrator saved to {filepath}")
    
    def load(self, filepath: Union[str, Path]) -> 'ConfidenceCalibrator':
        """Load a fitted calibrator from disk."""
        with open(filepath, 'rb') as f:
            save_data = pickle.load(f)
        
        self.method = save_data['method']
        self.best_calibrator = save_data['calibrator']
        self.calibration_metrics = save_data.get('metrics', {})
        self.is_fitted = True
        
        logger.info(f"Calibrator loaded from {filepath}")
        return self
    
    def get_calibration_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get calibration quality metrics for all methods."""
        return self.calibration_metrics.copy()