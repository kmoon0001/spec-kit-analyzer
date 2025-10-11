"""Tests for confidence calibration functionality."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from src.core.confidence_calibrator import ConfidenceCalibrator, IsotonicCalibration, PlattScaling, TemperatureScaling


class TestTemperatureScaling:
    """Test temperature scaling calibration method."""

    def test_temperature_scaling_initialization(self):
        """Test temperature scaling initializes correctly."""
        temp_scaling = TemperatureScaling()
        assert temp_scaling.temperature == 1.0
        assert not temp_scaling.is_fitted

    def test_temperature_scaling_fit_and_calibrate(self):
        """Test temperature scaling fitting and calibration."""
        # Create synthetic data where model is overconfident
        np.random.seed(42)
        n_samples = 100

        # Generate logits that are too confident (high magnitude)
        logits = np.random.normal(0, 2, n_samples)  # High variance = overconfident

        # Generate labels with some correlation to logits but not perfect
        probabilities = 1 / (1 + np.exp(-logits))
        labels = np.random.binomial(1, probabilities * 0.7 + 0.15, n_samples)  # Add noise

        temp_scaling = TemperatureScaling()
        temp_scaling.fit(logits, labels)

        assert temp_scaling.is_fitted
        assert temp_scaling.temperature != 1.0  # Should have learned something

        # Test calibration
        calibrated_probs = temp_scaling.calibrate(logits)
        assert len(calibrated_probs) == len(logits)
        assert np.all((calibrated_probs >= 0) & (calibrated_probs <= 1))

    def test_temperature_scaling_sigmoid_stability(self):
        """Test sigmoid function numerical stability."""
        # Test extreme values
        extreme_values = np.array([-1000, -100, -10, 0, 10, 100, 1000])
        result = TemperatureScaling._sigmoid(extreme_values)

        assert np.all(np.isfinite(result))
        assert np.all((result >= 0) & (result <= 1))
        assert result[0] < 0.001  # Very negative should be close to 0
        assert result[-1] > 0.999  # Very positive should be close to 1


class TestPlattScaling:
    """Test Platt scaling calibration method."""

    def test_platt_scaling_initialization(self):
        """Test Platt scaling initializes correctly."""
        platt_scaling = PlattScaling()
        assert not platt_scaling.is_fitted

    def test_platt_scaling_fit_and_calibrate(self):
        """Test Platt scaling fitting and calibration."""
        np.random.seed(42)
        n_samples = 100

        # Generate scores and labels
        scores = np.random.uniform(0, 1, n_samples)
        labels = np.random.binomial(1, scores * 0.8 + 0.1, n_samples)

        platt_scaling = PlattScaling()
        platt_scaling.fit(scores, labels)

        assert platt_scaling.is_fitted

        # Test calibration
        calibrated_probs = platt_scaling.calibrate(scores)
        assert len(calibrated_probs) == len(scores)
        assert np.all((calibrated_probs >= 0) & (calibrated_probs <= 1))


class TestIsotonicCalibration:
    """Test isotonic regression calibration method."""

    def test_isotonic_calibration_initialization(self):
        """Test isotonic calibration initializes correctly."""
        isotonic_cal = IsotonicCalibration()
        assert not isotonic_cal.is_fitted

    def test_isotonic_calibration_fit_and_calibrate(self):
        """Test isotonic calibration fitting and calibration."""
        np.random.seed(42)
        n_samples = 100

        # Generate scores and labels with non-linear relationship
        scores = np.random.uniform(0, 1, n_samples)
        # Non-linear relationship: sigmoid-like
        true_probs = 1 / (1 + np.exp(-5 * (scores - 0.5)))
        labels = np.random.binomial(1, true_probs, n_samples)

        isotonic_cal = IsotonicCalibration()
        isotonic_cal.fit(scores, labels)

        assert isotonic_cal.is_fitted

        # Test calibration
        calibrated_probs = isotonic_cal.calibrate(scores)
        assert len(calibrated_probs) == len(scores)
        assert np.all((calibrated_probs >= 0) & (calibrated_probs <= 1))


class TestConfidenceCalibrator:
    """Test main confidence calibrator class."""

    def test_confidence_calibrator_initialization(self):
        """Test confidence calibrator initializes correctly."""
        calibrator = ConfidenceCalibrator()
        assert calibrator.method == "auto"
        assert not calibrator.is_fitted
        assert calibrator.best_calibrator is None

    def test_confidence_calibrator_specific_method(self):
        """Test confidence calibrator with specific method."""
        calibrator = ConfidenceCalibrator(method="temperature")
        assert calibrator.method == "temperature"

    def test_confidence_calibrator_auto_selection(self):
        """Test automatic method selection."""
        np.random.seed(42)
        n_samples = 200  # Larger sample for method selection

        # Generate data where temperature scaling should work well
        logits = np.random.normal(0, 1.5, n_samples)
        probabilities = 1 / (1 + np.exp(-logits))
        labels = np.random.binomial(1, probabilities * 0.8 + 0.1, n_samples)

        calibrator = ConfidenceCalibrator(method="auto")
        calibrator.fit(logits, labels)

        assert calibrator.is_fitted
        assert calibrator.best_calibrator is not None
        assert calibrator.method in ["temperature", "platt", "isotonic"]

        # Test calibration
        calibrated_scores = calibrator.calibrate(logits)
        assert len(calibrated_scores) == len(logits)
        assert np.all((calibrated_scores >= 0) & (calibrated_scores <= 1))

    def test_confidence_calibrator_ece_calculation(self):
        """Test Expected Calibration Error calculation."""
        # Perfect calibration case
        perfect_probs = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
        perfect_labels = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1])  # Roughly matches probabilities

        ece = ConfidenceCalibrator._calculate_ece(perfect_probs, perfect_labels)
        assert ece >= 0  # ECE should be non-negative

        # Terrible calibration case
        terrible_probs = np.array([0.9, 0.9, 0.9, 0.9, 0.9])
        terrible_labels = np.array([0, 0, 0, 0, 0])  # All wrong despite high confidence

        terrible_ece = ConfidenceCalibrator._calculate_ece(terrible_probs, terrible_labels)
        assert terrible_ece > ece  # Should have higher ECE

    def test_confidence_calibrator_brier_score(self):
        """Test Brier score calculation."""
        # Perfect predictions
        perfect_probs = np.array([0.0, 0.0, 1.0, 1.0])
        perfect_labels = np.array([0, 0, 1, 1])

        perfect_brier = ConfidenceCalibrator._calculate_brier_score(perfect_probs, perfect_labels)
        assert perfect_brier == 0.0

        # Random predictions
        random_probs = np.array([0.5, 0.5, 0.5, 0.5])
        random_labels = np.array([0, 1, 0, 1])

        random_brier = ConfidenceCalibrator._calculate_brier_score(random_probs, random_labels)
        assert random_brier == 0.25  # Expected Brier score for random predictions

    def test_confidence_calibrator_save_load(self):
        """Test saving and loading calibrator."""
        np.random.seed(42)
        n_samples = 100

        scores = np.random.uniform(0, 1, n_samples)
        labels = np.random.binomial(1, scores, n_samples)

        # Train calibrator
        calibrator = ConfidenceCalibrator(method="temperature")
        calibrator.fit(scores, labels)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            calibrator.save(tmp_path)

            # Load new calibrator
            new_calibrator = ConfidenceCalibrator()
            new_calibrator.load(tmp_path)

            assert new_calibrator.is_fitted
            assert new_calibrator.method == calibrator.method

            # Test that calibration produces same results
            original_calibrated = calibrator.calibrate(scores[:10])
            loaded_calibrated = new_calibrator.calibrate(scores[:10])

            np.testing.assert_array_almost_equal(original_calibrated, loaded_calibrated)

        finally:
            tmp_path.unlink()  # Clean up

    @pytest.mark.filterwarnings("ignore:Mean of empty slice:RuntimeWarning")
    @pytest.mark.filterwarnings("ignore:invalid value encountered in scalar divide:RuntimeWarning")
    def test_confidence_calibrator_insufficient_data(self):
        """Test behavior with insufficient training data."""
        # Very small dataset
        scores = np.array([0.5, 0.7])
        labels = np.array([0, 1])

        calibrator = ConfidenceCalibrator(method="auto")
        calibrator.fit(scores, labels)

        # Should still work but may not be well-calibrated
        assert calibrator.is_fitted

        calibrated = calibrator.calibrate(scores)
        assert len(calibrated) == len(scores)

    def test_confidence_calibrator_edge_cases(self):
        """Test edge cases and error handling."""
        calibrator = ConfidenceCalibrator()

        # Test calibration without fitting
        scores = np.array([0.5, 0.7, 0.3])
        result = calibrator.calibrate(scores)
        np.testing.assert_array_equal(result, scores)  # Should return original scores

        # Test invalid method
        with pytest.raises(ValueError):
            invalid_calibrator = ConfidenceCalibrator(method="invalid_method")
            invalid_calibrator.fit(scores, np.array([0, 1, 0]))

    def test_get_calibration_metrics(self):
        """Test getting calibration metrics."""
        np.random.seed(42)
        n_samples = 100

        scores = np.random.uniform(0, 1, n_samples)
        labels = np.random.binomial(1, scores, n_samples)

        calibrator = ConfidenceCalibrator(method="auto")
        calibrator.fit(scores, labels)

        metrics = calibrator.get_calibration_metrics()
        assert isinstance(metrics, dict)

        # Should contain metrics for different methods
        for _method_name, method_metrics in metrics.items():
            assert "ece" in method_metrics
            assert "brier_score" in method_metrics
            assert isinstance(method_metrics["ece"], float)
            assert isinstance(method_metrics["brier_score"], float)


@pytest.mark.integration
class TestConfidenceCalibrationIntegration:
    """Integration tests for confidence calibration."""

    def test_realistic_compliance_scenario(self):
        """Test calibration with realistic compliance analysis scenario."""
        np.random.seed(42)

        # Simulate LLM confidence scores that are typically overconfident
        n_findings = 50

        # Generate overconfident scores (biased toward high confidence)
        raw_confidences = np.random.beta(5, 2, n_findings)  # Biased toward high values

        # Generate ground truth where high confidence doesn't always mean correct
        # Simulate that LLM is right about 70% of the time regardless of confidence
        true_labels = np.random.binomial(1, 0.7, n_findings)

        # Train calibrator
        calibrator = ConfidenceCalibrator(method="auto")
        calibrator.fit(raw_confidences, true_labels)

        # Test on new data
        test_confidences = np.random.beta(5, 2, 20)
        calibrated_confidences = calibrator.calibrate(test_confidences)

        # Calibrated scores should be more conservative (lower on average)
        assert np.mean(calibrated_confidences) <= np.mean(test_confidences)

        # All scores should be valid probabilities
        assert np.all((calibrated_confidences >= 0) & (calibrated_confidences <= 1))

        # Get metrics
        metrics = calibrator.get_calibration_metrics()
        assert len(metrics) > 0

        # ECE should be reasonable (< 0.5 for decent calibration)
        best_method_metrics = metrics[calibrator.method]
        assert best_method_metrics["ece"] < 0.5
