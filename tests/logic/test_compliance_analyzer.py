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
        with patch('src.core.compliance_analyzer.AutoModelForCausalLM.from_pretrained'), \
             patch('src.core.compliance_analyzer.AutoTokenizer.from_pretrained'), \
             patch('src.core.compliance_analyzer.GuidelineService'), \
             patch('src.core.compliance_analyzer.load_config') as mock_load_config:

            mock_load_config.return_value = {
                'models': {
                    'generator': 'mock-generator-model'
                },
                'quantization': {
                    'load_in_4bit': False,
                }
            }

            instance = ComplianceAnalyzer()
            instance.generator_tokenizer = MagicMock()
            instance.generator_model = MagicMock()
            yield instance

