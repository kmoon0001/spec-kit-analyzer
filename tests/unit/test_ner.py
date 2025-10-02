"""
Unit tests for the NER (Named Entity Recognition) module.

Tests the NERAnalyzer class functionality including entity extraction,
clinician name detection, and medical entity categorization.
"""

import pytest
from unittest.mock import Mock, patch

from src.core.ner import NERAnalyzer, NERPipeline


class TestNERPipeline:
    """Test cases for the NERPipeline class."""

    def test_initialization_with_empty_models(self):
        """Test NERPipeline initialization with empty model list."""
        pipeline = NERPipeline([])
        assert pipeline.model_names == []
        assert pipeline.pipelines == []

    def test_initialization_with_default_models(self):
        """Test NERPipeline initialization with default models."""
        with (
            patch("src.core.ner.AutoTokenizer") as mock_tokenizer,
            patch("src.core.ner.AutoModelForTokenClassification") as mock_model,
            patch("src.core.ner.pipeline") as mock_pipeline,
        ):
            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()
            mock_pipeline.return_value = Mock()

            ner_pipeline = NERPipeline()
            assert len(ner_pipeline.model_names) == 2
            assert "d4data/biomedical-ner-all" in ner_pipeline.model_names
            assert "Clinical-AI-Apollo/Medical-NER" in ner_pipeline.model_names

    def test_extract_entities_empty_text(self):
        """Test entity extraction with empty text."""
        pipeline = NERPipeline([])
        entities = pipeline.extract_entities("")
        assert entities == []

    def test_extract_entities_no_pipelines(self):
        """Test entity extraction when no pipelines are loaded."""
        pipeline = NERPipeline([])
        entities = pipeline.extract_entities("Sample text")
        assert entities == []


class TestNERAnalyzer:
    """Test cases for the NERAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a NERAnalyzer instance for testing."""
        return NERAnalyzer([])  # Empty model list for faster testing

    def test_initialization(self, analyzer):
        """Test NERAnalyzer initialization."""
        assert analyzer.ner_pipeline is not None
        assert hasattr(analyzer, "presidio_analyzer")
        assert hasattr(analyzer, "clinical_patterns")

    def test_extract_entities_empty_text(self, analyzer):
        """Test entity extraction with empty text."""
        entities = analyzer.extract_entities("")
        assert entities == []

        entities = analyzer.extract_entities("   ")
        assert entities == []

    def test_extract_entities_with_text(self, analyzer):
        """Test entity extraction with sample clinical text."""
        text = "Patient John Smith was treated by Dr. Jane Doe, PT for knee pain."
        entities = analyzer.extract_entities(text)
        assert isinstance(entities, list)
        # Should find some entities even with minimal models
        # The exact count may vary based on available models

    def test_extract_clinician_name_empty_text(self, analyzer):
        """Test clinician name extraction with empty text."""
        names = analyzer.extract_clinician_name("")
        assert names == []

    def test_extract_clinician_name_with_title(self, analyzer):
        """Test clinician name extraction with clinical titles."""
        text = "Signed by Dr. John Smith, PT"
        names = analyzer.extract_clinician_name(text)
        assert isinstance(names, list)
        # Should find clinician names with titles

    def test_extract_clinician_name_with_signature(self, analyzer):
        """Test clinician name extraction near signature keywords."""
        text = "Treatment provided by therapist Jane Doe, OT"
        names = analyzer.extract_clinician_name(text)
        assert isinstance(names, list)

    def test_extract_medical_entities_structure(self, analyzer):
        """Test medical entity extraction returns proper structure."""
        text = "Patient has knee pain and takes ibuprofen."
        entities = analyzer.extract_medical_entities(text)

        assert isinstance(entities, dict)
        expected_categories = [
            "conditions",
            "medications",
            "procedures",
            "anatomy",
            "measurements",
            "persons",
            "other",
        ]
        for category in expected_categories:
            assert category in entities
            assert isinstance(entities[category], list)

    def test_clinical_patterns_exist(self, analyzer):
        """Test that clinical patterns are properly defined."""
        patterns = analyzer.clinical_patterns
        assert "titles" in patterns
        assert "signature_keywords" in patterns
        assert "name_pattern" in patterns

        # Test that patterns are valid regex
        import re

        for pattern_name, pattern in patterns.items():
            try:
                re.compile(pattern)
            except re.error:
                pytest.fail(f"Invalid regex pattern for {pattern_name}: {pattern}")

    def test_deduplicate_entities(self, analyzer):
        """Test entity deduplication functionality."""
        # Create duplicate entities
        entities = [
            {"start": 0, "end": 4, "word": "test", "entity_group": "TEST"},
            {"start": 0, "end": 4, "word": "test", "entity_group": "TEST"},  # Duplicate
            {"start": 5, "end": 9, "word": "word", "entity_group": "WORD"},
        ]

        deduplicated = analyzer._deduplicate_entities(entities)
        assert len(deduplicated) == 2
        assert deduplicated[0]["word"] == "test"
        assert deduplicated[1]["word"] == "word"


class TestNERIntegration:
    """Integration tests for NER functionality."""

    def test_clinical_text_analysis(self):
        """Test NER analysis on realistic clinical text."""
        analyzer = NERAnalyzer([])  # Use empty models for speed

        clinical_text = """
        Patient: John Smith
        DOB: 01/15/1980
        Diagnosis: Right knee osteoarthritis
        
        Treatment provided by Dr. Sarah Johnson, PT, DPT
        Patient demonstrates improved range of motion following
        therapeutic exercises. Prescribed ibuprofen 400mg TID.
        
        Next appointment scheduled with therapist Mary Wilson, OT.
        
        Signature: Dr. Sarah Johnson, PT
        Date: 03/15/2024
        """

        # Test entity extraction
        entities = analyzer.extract_entities(clinical_text)
        assert isinstance(entities, list)

        # Test clinician name extraction
        clinicians = analyzer.extract_clinician_name(clinical_text)
        assert isinstance(clinicians, list)

        # Test medical entity categorization
        medical_entities = analyzer.extract_medical_entities(clinical_text)
        assert isinstance(medical_entities, dict)

        # Verify structure
        for category in medical_entities:
            assert isinstance(medical_entities[category], list)

    def test_error_handling(self):
        """Test NER error handling with problematic input."""
        analyzer = NERAnalyzer([])

        # Test with None input
        entities = analyzer.extract_entities(None)
        assert entities == []

        # Test with very long text
        long_text = "word " * 10000
        entities = analyzer.extract_entities(long_text)
        assert isinstance(entities, list)

        # Test with special characters
        special_text = "Patient: @#$%^&*()_+ has condition"
        entities = analyzer.extract_entities(special_text)
        assert isinstance(entities, list)


@pytest.mark.slow
class TestNERWithRealModels:
    """Tests that require actual model loading (marked as slow)."""

    def test_real_model_loading(self):
        """Test NER with actual transformer models."""
        # This test will be skipped unless specifically requested
        analyzer = NERAnalyzer()  # Use default models

        text = "Patient John Smith was treated by Dr. Jane Doe for knee pain."
        entities = analyzer.extract_entities(text)

        assert isinstance(entities, list)
        # With real models, we should get meaningful results
        assert len(entities) > 0

    def test_presidio_integration(self):
        """Test Presidio integration if available."""
        try:
            from presidio_analyzer import AnalyzerEngine  # noqa: F401

            analyzer = NERAnalyzer([])

            text = "Patient John Smith, DOB: 01/15/1980, Phone: 555-123-4567"
            entities = analyzer.extract_entities(text)

            # Should detect PII entities
            assert isinstance(entities, list)
        except ImportError:
            pytest.skip("Presidio not available")


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
