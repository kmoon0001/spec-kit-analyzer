import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.compliance_analyzer import ComplianceAnalyzer
from src.document_classifier import DocumentClassifier, DocumentType
from src.parsing import parse_document_into_sections
from typing import Dict, List
from src.rubric_service import ComplianceRule

class TestComplianceAnalyzer:

    # Note: The 'analyzer_instance' fixture is now function-scoped to ensure
    # that patches are applied correctly to each test function.
    @pytest.fixture(scope="function")
    def analyzer_instance(self):
        """
        Fixture to create a new ComplianceAnalyzer instance for each test function.
        """
        with patch('src.core.compliance_analyzer.AutoModelForCausalLM.from_pretrained') as mock_model, \
             patch('src.core.compliance_analyzer.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('src.core.compliance_analyzer.pipeline') as mock_pipeline, \
             patch('src.core.compliance_analyzer.BitsAndBytesConfig') as mock_bitsandbytes:

            # Configure the mocks to return dummy objects
            mock_model.return_value = MagicMock()
            mock_tokenizer.return_value = MagicMock()
            mock_pipeline.return_value = MagicMock()
            mock_bitsandbytes.return_value = MagicMock()

            instance = ComplianceAnalyzer()
            yield instance

    def test_health_check(self, analyzer_instance):
        """Tests the AI system health check."""
        is_healthy, message = analyzer_instance.check_ai_systems_health()
        assert is_healthy
        assert message == "AI Systems: Online"

    def test_build_hybrid_prompt(self, analyzer_instance):
        """Tests the construction of the hybrid prompt."""
        document = "This is a test document."
        entity_list = "'test' (test_entity)"
        rules = [
            ComplianceRule(
                uri='test_rule_1',
                severity='High',