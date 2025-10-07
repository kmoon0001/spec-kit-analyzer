"""Tests for the ML training pipeline."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from src.ml.trainer import MLTrainingPipeline
from src.core.calibration_trainer import CalibrationTrainer
from src.core.confidence_calibrator import ConfidenceCalibrator


@pytest.fixture
def temp_models_dir():
    """Create a temporary directory for model storage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_calibration_trainer():
    """Create a mock calibration trainer."""
    trainer = Mock(spec=CalibrationTrainer)
    
    # Mock training data
    training_data = [
        {"confidence": 0.9, "is_correct": True},
        {"confidence": 0.8, "is_correct": True},
        {"confidence": 0.7, "is_correct": False},
        {"confidence": 0.6, "is_correct": False},
        {"confidence": 0.5, "is_correct": True},
    ] * 12  # 60 samples total
    
    trainer.get_training_data.return_value = training_data
    return trainer


@pytest.fixture
def ml_pipeline(temp_models_dir, mock_calibration_trainer):
    """Create an ML training pipeline for testing."""
    return MLTrainingPipeline(
        calibration_trainer=mock_calibration_trainer,
        models_dir=temp_models_dir
    )


class TestMLTrainingPipeline:
    """Test the ML training pipeline functionality."""
    
    def test_initialization(self, temp_models_dir):
        """Test pipeline initialization."""
        pipeline = MLTrainingPipeline(models_dir=temp_models_dir)
        
        assert pipeline.models_dir == Path(temp_models_dir)
        assert pipeline.models_dir.exists()
        assert pipeline.min_samples_for_training == 50
        assert pipeline.training_interval_days == 7
        assert pipeline.performance_threshold == 0.05
    
    @pytest.mark.asyncio
    async def test_insufficient_training_data(self, ml_pipeline, mock_calibration_trainer):
        """Test behavior when there's insufficient training data."""
        # Mock insufficient data
        mock_calibration_trainer.get_training_data.return_value = [
            {"confidence": 0.8, "is_correct": True}
        ] * 10  # Only 10 samples
        
        # Force retraining to bypass time checks
        result = await ml_pipeline.fine_tune_model_with_feedback(force_retrain=True)
        
        assert result["status"] == "insufficient_data"
        assert result["samples_collected"] == 10
        assert "Need 50 samples" in result["message"]
    
    @pytest.mark.asyncio
    async def test_successful_training_and_deployment(self, ml_pipeline, mock_calibration_trainer):
        """Test successful training and deployment of a new calibrator."""
        # Force retraining to bypass time checks
        result = await ml_pipeline.fine_tune_model_with_feedback(force_retrain=True)
        
        assert result["status"] == "completed"
        assert "training_results" in result
        assert "evaluation_results" in result
        assert "deployment_results" in result
        assert result["samples_used"] == 60
        
        # Check that training results contain expected fields
        training_results = result["training_results"]
        assert "calibrator" in training_results
        assert "method_used" in training_results
        assert "training_metrics" in training_results
        
        # Check evaluation results
        eval_results = result["evaluation_results"]
        assert "raw_ece" in eval_results
        assert "calibrated_ece" in eval_results
        assert "ece_improvement" in eval_results
    
    @pytest.mark.asyncio
    async def test_training_with_insufficient_improvement(self, ml_pipeline, mock_calibration_trainer):
        """Test that models with insufficient improvement are not deployed."""
        # Create training data that won't show much improvement
        uniform_data = [
            {"confidence": 0.5, "is_correct": True},
            {"confidence": 0.5, "is_correct": False},
        ] * 30  # 60 samples, all with same confidence
        
        mock_calibration_trainer.get_training_data.return_value = uniform_data
        
        result = await ml_pipeline.fine_tune_model_with_feedback(force_retrain=True)
        
        assert result["status"] == "completed"
        
        # Check that deployment was skipped due to insufficient improvement
        deployment_results = result["deployment_results"]
        assert deployment_results["deployed"] is False
        assert "below threshold" in deployment_results["reason"]
    
    def test_should_retrain_time_based(self, ml_pipeline):
        """Test time-based retraining logic."""
        # No metadata file exists, should retrain
        assert ml_pipeline._should_retrain() is True
        
        # Create recent training metadata
        metadata_path = ml_pipeline.models_dir / "training_metadata.json"
        recent_training = {
            "last_training": datetime.now().isoformat(),
            "training_count": 1
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(recent_training, f)
        
        # Should not retrain if recent training occurred
        assert ml_pipeline._should_retrain() is False
        
        # Create old training metadata
        old_training = {
            "last_training": (datetime.now() - timedelta(days=10)).isoformat(),
            "training_count": 1
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(old_training, f)
        
        # Should retrain if training is old enough
        assert ml_pipeline._should_retrain() is True
    
    def test_get_next_training_time(self, ml_pipeline):
        """Test getting next training time."""
        # No metadata file
        next_time = ml_pipeline._get_next_training_time()
        next_datetime = datetime.fromisoformat(next_time)
        assert abs((next_datetime - datetime.now()).total_seconds()) < 60  # Within 1 minute
        
        # With metadata file
        metadata_path = ml_pipeline.models_dir / "training_metadata.json"
        last_training = datetime.now() - timedelta(days=3)
        metadata = {
            "last_training": last_training.isoformat(),
            "training_count": 1
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        next_time = ml_pipeline._get_next_training_time()
        next_datetime = datetime.fromisoformat(next_time)
        expected_next = last_training + timedelta(days=7)
        
        assert abs((next_datetime - expected_next).total_seconds()) < 60
    
    def test_update_training_metadata(self, ml_pipeline):
        """Test updating training metadata."""
        evaluation_results = {
            "ece_improvement": 0.15,
            "brier_improvement": 0.05,
            "method_used": "temperature"
        }
        
        ml_pipeline._update_training_metadata(evaluation_results)
        
        metadata_path = ml_pipeline.models_dir / "training_metadata.json"
        assert metadata_path.exists()
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert "last_training" in metadata
        assert metadata["last_evaluation_results"] == evaluation_results
        assert metadata["training_count"] == 1
        
        # Test incrementing training count
        ml_pipeline._update_training_metadata(evaluation_results)
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert metadata["training_count"] == 2
    
    @pytest.mark.asyncio
    async def test_training_error_handling(self, ml_pipeline, mock_calibration_trainer):
        """Test error handling in the training pipeline."""
        # Mock an error in get_training_data
        mock_calibration_trainer.get_training_data.side_effect = Exception("Database error")
        
        result = await ml_pipeline.fine_tune_model_with_feedback(force_retrain=True)
        
        assert result["status"] == "error"
        assert "Database error" in result["message"]
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_skipped_training_due_to_time(self, ml_pipeline):
        """Test that training is skipped when not enough time has passed."""
        # Create recent training metadata
        metadata_path = ml_pipeline.models_dir / "training_metadata.json"
        recent_training = {
            "last_training": datetime.now().isoformat(),
            "training_count": 1
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(recent_training, f)
        
        result = await ml_pipeline.fine_tune_model_with_feedback()
        
        assert result["status"] == "skipped"
        assert "Training not needed" in result["message"]
        assert "next_training_due" in result


@pytest.mark.asyncio
async def test_legacy_function_compatibility():
    """Test that the legacy function still works."""
    from src.ml.trainer import fine_tune_model_with_feedback
    
    # Should not crash and should return a result
    result = await fine_tune_model_with_feedback()
    
    assert isinstance(result, dict)
    assert "status" in result


@pytest.mark.integration
class TestMLTrainingIntegration:
    """Integration tests for the ML training pipeline."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_training_pipeline(self, temp_models_dir):
        """Test the complete training pipeline end-to-end."""
        # Create a real calibration trainer with in-memory database
        trainer = CalibrationTrainer(db_path=":memory:")
        
        # Add some synthetic feedback data
        synthetic_findings = [
            {"confidence": 0.9, "is_correct": True, "discipline": "pt"},
            {"confidence": 0.8, "is_correct": True, "discipline": "pt"},
            {"confidence": 0.7, "is_correct": False, "discipline": "pt"},
            {"confidence": 0.6, "is_correct": False, "discipline": "pt"},
            {"confidence": 0.5, "is_correct": True, "discipline": "pt"},
        ]
        
        for i, finding_data in enumerate(synthetic_findings * 12):  # 60 samples
            finding = {
                "id": f"finding_{i}",
                "confidence": finding_data["confidence"],
                "original_confidence": finding_data["confidence"],
                "discipline": finding_data["discipline"]
            }
            feedback = "correct" if finding_data["is_correct"] else "incorrect"
            trainer.record_feedback(finding, feedback, user_id="test_user")
        
        # Create pipeline with real trainer
        pipeline = MLTrainingPipeline(
            calibration_trainer=trainer,
            models_dir=temp_models_dir
        )
        
        # Run training
        result = await pipeline.fine_tune_model_with_feedback(force_retrain=True)
        
        # Verify results
        assert result["status"] == "completed"
        assert result["samples_used"] == 60
        
        # Check that model files were created
        models_dir = Path(temp_models_dir)
        assert (models_dir / "confidence_calibrator.pkl").exists()
        assert (models_dir / "training_metadata.json").exists()
        
        # Verify metadata
        with open(models_dir / "training_metadata.json", 'r') as f:
            metadata = json.load(f)
        
        assert metadata["training_count"] == 1
        assert "last_evaluation_results" in metadata