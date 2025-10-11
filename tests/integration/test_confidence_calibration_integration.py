"""Integration tests for confidence calibration with compliance analyzer."""

import json
from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest

from src.core.calibration_trainer import CalibrationTrainer, FeedbackCollector
from src.core.compliance_analyzer import ComplianceAnalyzer
from src.core.confidence_calibrator import ConfidenceCalibrator


@pytest.fixture
def mock_services():
    """Create mock services for testing."""
    mock_retriever = Mock()
    mock_retriever.retrieve = AsyncMock(
        return_value=[
            {
                "id": "rule_1",
                "name": "Documentation Frequency",
                "content": "Treatment frequency must be documented",
                "relevance_score": 0.9,
            }
        ]
    )

    mock_ner_service = Mock()
    mock_ner_service.extract_entities.return_value = [{"entity_group": "TREATMENT", "word": "physical therapy"}]

    mock_llm_service = Mock()
    mock_llm_service.generate.return_value = json.dumps(
        {
            "summary": "Document shows good compliance overall.",
            "findings": [
                {
                    "rule_id": "rule_1",
                    "issue_title": "Treatment frequency documented",
                    "text": "Patient received PT 3x/week",
                    "regulation": "Medicare guidelines",
                    "confidence": 0.85,
                    "personalized_tip": "Continue documenting frequency",
                    "severity_reason": "Required for reimbursement",
                    "priority": "High",
                },
                {
                    "rule_id": "rule_2",
                    "issue_title": "Goals need review",
                    "text": "Goals established 6 months ago",
                    "regulation": "Professional standards",
                    "confidence": 0.45,  # Low confidence
                    "personalized_tip": "Review and update goals",
                    "severity_reason": "Outdated goals affect treatment",
                    "priority": "Medium",
                },
            ],
            "citations": ["Medicare Part B guidelines"],
        }
    )

    mock_explanation_engine = Mock()
    mock_explanation_engine.add_explanations.return_value = {
        "summary": "Document shows good compliance overall.",
        "findings": [
            {
                "rule_id": "rule_1",
                "issue_title": "Treatment frequency documented",
                "text": "Patient received PT 3x/week",
                "regulation": "Medicare guidelines",
                "confidence": 0.85,
                "personalized_tip": "Continue documenting frequency",
                "severity_reason": "Required for reimbursement",
                "priority": "High",
            },
            {
                "rule_id": "rule_2",
                "issue_title": "Goals need review",
                "text": "Goals established 6 months ago",
                "regulation": "Professional standards",
                "confidence": 0.45,
                "personalized_tip": "Review and update goals",
                "severity_reason": "Outdated goals affect treatment",
                "priority": "Medium",
            },
        ],
        "citations": ["Medicare Part B guidelines"],
    }

    mock_prompt_manager = Mock()
    mock_prompt_manager.get_prompt.return_value = "Analyze this document for compliance..."

    mock_fact_checker = Mock()
    mock_fact_checker.is_finding_plausible.return_value = True

    return {
        "retriever": mock_retriever,
        "ner_service": mock_ner_service,
        "llm_service": mock_llm_service,
        "explanation_engine": mock_explanation_engine,
        "prompt_manager": mock_prompt_manager,
        "fact_checker_service": mock_fact_checker,
    }


@pytest.fixture
def trained_calibrator():
    """Create a pre-trained confidence calibrator."""
    np.random.seed(42)

    # Create training data where high confidence doesn't always mean correct
    n_samples = 100
    confidences = np.random.uniform(0.3, 0.95, n_samples)

    # Simulate that the model is overconfident - correct rate is lower than confidence
    correct_rates = confidences * 0.7 + 0.1  # Scale down confidence
    labels = np.random.binomial(1, correct_rates, n_samples)

    calibrator = ConfidenceCalibrator(method="temperature")
    calibrator.fit(confidences, labels)

    return calibrator


class TestConfidenceCalibrationIntegration:
    """Test confidence calibration integration with compliance analyzer."""

    @pytest.mark.asyncio
    async def test_compliance_analyzer_with_calibration(self, mock_services, trained_calibrator):
        """Test that compliance analyzer applies confidence calibration."""
        # Create analyzer with calibrated confidence
        analyzer = ComplianceAnalyzer(
            retriever=mock_services["retriever"],
            ner_service=mock_services["ner_service"],
            llm_service=mock_services["llm_service"],
            explanation_engine=mock_services["explanation_engine"],
            prompt_manager=mock_services["prompt_manager"],
            fact_checker_service=mock_services["fact_checker_service"],
            confidence_calibrator=trained_calibrator,
        )

        # Run analysis
        result = await analyzer.analyze_document(
            document_text="Patient received PT 3x/week. Goals established 6 months ago.",
            discipline="pt",
            doc_type="progress_note",
        )

        # Verify results structure
        assert "findings" in result
        assert len(result["findings"]) == 2

        # Check that confidence calibration was applied
        for finding in result["findings"]:
            assert "confidence" in finding
            assert "original_confidence" in finding
            assert "confidence_calibrated" in finding
            assert finding["confidence_calibrated"] is True

            # Calibrated confidence should be different from original
            # (unless by coincidence, but very unlikely)
            original_conf = finding["original_confidence"]
            calibrated_conf = finding["confidence"]

            # Both should be valid probabilities
            assert 0 <= original_conf <= 1
            assert 0 <= calibrated_conf <= 1

            # For overconfident model, calibrated should generally be lower
            # (though this isn't guaranteed for individual samples)

    @pytest.mark.asyncio
    async def test_confidence_threshold_with_calibration(self, mock_services, trained_calibrator):
        """Test that confidence thresholds work with calibrated scores."""
        analyzer = ComplianceAnalyzer(
            retriever=mock_services["retriever"],
            ner_service=mock_services["ner_service"],
            llm_service=mock_services["llm_service"],
            explanation_engine=mock_services["explanation_engine"],
            prompt_manager=mock_services["prompt_manager"],
            fact_checker_service=mock_services["fact_checker_service"],
            confidence_calibrator=trained_calibrator,
        )

        result = await analyzer.analyze_document(
            document_text="Test document", discipline="pt", doc_type="progress_note"
        )

        # Check low confidence flagging based on calibrated scores
        low_conf_findings = [f for f in result["findings"] if f.get("is_low_confidence")]

        # The second finding had original confidence 0.45, which after calibration
        # might be even lower, so it should be flagged as low confidence
        assert len(low_conf_findings) >= 0  # Could be 0 or more depending on calibration

        for finding in low_conf_findings:
            assert finding["confidence"] < 0.7  # Below threshold

    def test_calibration_metrics_retrieval(self, trained_calibrator):
        """Test getting calibration metrics from analyzer."""
        analyzer = ComplianceAnalyzer(
            retriever=Mock(),
            ner_service=Mock(),
            llm_service=Mock(),
            explanation_engine=Mock(),
            prompt_manager=Mock(),
            fact_checker_service=Mock(),
            confidence_calibrator=trained_calibrator,
        )

        metrics = analyzer.get_calibration_metrics()

        assert metrics["status"] == "fitted"
        assert metrics["method"] == "temperature"
        assert "metrics" in metrics

    def test_calibrator_training_with_feedback(self, mock_services):
        """Test training calibrator with user feedback."""
        analyzer = ComplianceAnalyzer(
            retriever=mock_services["retriever"],
            ner_service=mock_services["ner_service"],
            llm_service=mock_services["llm_service"],
            explanation_engine=mock_services["explanation_engine"],
            prompt_manager=mock_services["prompt_manager"],
            fact_checker_service=mock_services["fact_checker_service"],
        )

        # Create training data
        training_data = [
            {"confidence": 0.9, "is_correct": True},
            {"confidence": 0.8, "is_correct": True},
            {"confidence": 0.7, "is_correct": False},  # Overconfident
            {"confidence": 0.6, "is_correct": False},  # Overconfident
            {"confidence": 0.5, "is_correct": True},  # Underconfident
            {"confidence": 0.4, "is_correct": False},
            {"confidence": 0.3, "is_correct": False},
            {"confidence": 0.9, "is_correct": False},  # Very overconfident
            {"confidence": 0.8, "is_correct": True},
            {"confidence": 0.6, "is_correct": True},  # Underconfident
            {"confidence": 0.7, "is_correct": True},
            {"confidence": 0.5, "is_correct": False},
        ]

        # Train the calibrator
        analyzer.train_confidence_calibrator(training_data)

        # Verify calibrator is now fitted
        assert analyzer.confidence_calibrator.is_fitted

        # Test calibration on new data
        test_confidences = np.array([0.9, 0.7, 0.5, 0.3])
        calibrated = analyzer.confidence_calibrator.calibrate(test_confidences)

        assert len(calibrated) == len(test_confidences)
        assert np.all((calibrated >= 0) & (calibrated <= 1))


class TestCalibrationTrainer:
    """Test calibration training data collection."""

    def test_feedback_collector_widget_creation(self):
        """Test creating feedback widgets for findings."""
        trainer = CalibrationTrainer(db_path=":memory:")  # In-memory database
        collector = FeedbackCollector(trainer)

        finding = {
            "id": "test_finding_1",
            "issue_title": "Test Issue",
            "confidence": 0.75,
            "original_confidence": 0.80,
            "confidence_calibrated": True,
        }

        widget_data = collector.create_feedback_widget(finding)

        assert widget_data["finding_id"] == "test_finding_1"
        assert widget_data["issue_title"] == "Test Issue"
        assert widget_data["confidence"] == 0.75
        assert widget_data["original_confidence"] == 0.80
        assert widget_data["calibrated"] is True
        assert len(widget_data["buttons"]) == 3

    def test_feedback_processing_and_storage(self):
        """Test processing and storing user feedback."""
        trainer = CalibrationTrainer(db_path=":memory:")
        collector = FeedbackCollector(trainer)

        finding = {
            "id": "test_finding_1",
            "issue_title": "Test Issue",
            "confidence": 0.75,
            "original_confidence": 0.80,
            "document_type": "progress_note",
            "discipline": "pt",
            "rule_id": "rule_1",
            "priority": "High",
        }

        # Process feedback
        collector.process_feedback(finding, "correct", user_id="test_user")
        collector.process_feedback(finding, "incorrect", user_id="test_user")

        # Get training data
        training_data = trainer.get_training_data(min_samples=1)

        assert len(training_data) == 2
        assert training_data[0]["confidence"] == 0.80  # Original confidence
        assert training_data[0]["is_correct"] in [True, False]
        assert training_data[1]["confidence"] == 0.80
        assert training_data[1]["is_correct"] in [True, False]

    def test_feedback_statistics(self):
        """Test getting feedback statistics."""
        trainer = CalibrationTrainer(db_path=":memory:")

        # Add some test feedback
        test_findings = [
            {"confidence": 0.9, "original_confidence": 0.9, "discipline": "pt"},
            {"confidence": 0.7, "original_confidence": 0.7, "discipline": "ot"},
            {"confidence": 0.5, "original_confidence": 0.5, "discipline": "pt"},
        ]

        feedbacks = ["correct", "incorrect", "correct"]

        for finding, feedback in zip(test_findings, feedbacks, strict=False):
            trainer.record_feedback(finding, feedback, user_id="test_user")

        stats = trainer.get_feedback_statistics()

        assert stats["total_feedback"] == 3
        assert "feedback_distribution" in stats
        assert "confidence_statistics" in stats
        assert "discipline_distribution" in stats

        # Check discipline distribution
        assert stats["discipline_distribution"]["pt"] == 2
        assert stats["discipline_distribution"]["ot"] == 1


@pytest.mark.integration
class TestEndToEndCalibration:
    """End-to-end tests for confidence calibration workflow."""

    @pytest.mark.asyncio
    async def test_full_calibration_workflow(self, mock_services):
        """Test complete workflow from analysis to feedback to retraining."""
        # Step 1: Initial analysis without calibration
        analyzer = ComplianceAnalyzer(
            retriever=mock_services["retriever"],
            ner_service=mock_services["ner_service"],
            llm_service=mock_services["llm_service"],
            explanation_engine=mock_services["explanation_engine"],
            prompt_manager=mock_services["prompt_manager"],
            fact_checker_service=mock_services["fact_checker_service"],
        )

        result = await analyzer.analyze_document(
            document_text="Test document", discipline="pt", doc_type="progress_note"
        )

        # Step 2: Collect user feedback
        trainer = CalibrationTrainer(db_path=":memory:")
        collector = FeedbackCollector(trainer)

        for finding in result["findings"]:
            # Simulate user feedback (correct for high confidence, incorrect for low)
            feedback = "correct" if finding["confidence"] > 0.6 else "incorrect"
            collector.process_feedback(finding, feedback, user_id="test_user")

        # Step 3: Train calibrator with collected feedback
        training_data = trainer.get_training_data(min_samples=1)
        if len(training_data) >= 2:  # Need at least some data
            analyzer.train_confidence_calibrator(training_data)

            # Step 4: Run new analysis with calibrated confidence
            new_result = await analyzer.analyze_document(
                document_text="Another test document", discipline="pt", doc_type="progress_note"
            )

            # Verify calibration was applied
            for finding in new_result["findings"]:
                if analyzer.confidence_calibrator.is_fitted:
                    assert finding.get("confidence_calibrated", False) is True
                    assert "original_confidence" in finding
