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

class TestComplianceAnalyzer:

    @pytest.fixture(scope="class")
    def analyzer_instance(self):
        """Fixture to create a single ComplianceAnalyzer instance for the slow integration test."""
        return ComplianceAnalyzer()

    def test_document_classification(self):
        """Tests the document classifier with different inputs."""
        classifier = DocumentClassifier()
        eval_doc = "This is a patient evaluation."
        assert classifier.classify(eval_doc) == DocumentType.EVALUATION
        pn_doc = "This is a progress note."
        assert classifier.classify(pn_doc) == DocumentType.PROGRESS_NOTE
        unclassified_doc = "This is a regular document."
        assert classifier.classify(unclassified_doc) == DocumentType.UNKNOWN

    @patch('src.core.compliance_analyzer.ComplianceAnalyzer.__init__', return_value=None)
    def test_build_prompt(self, mock_init):
        # Create an instance of the analyzer (init is mocked)
        analyzer = ComplianceAnalyzer()
        # Define mock data
        document = "This is a test document."
        entity_list = "'test' (test_entity)"
        context = "This is a test context."
        # Call the method
        prompt = analyzer._build_prompt(document, entity_list, context)
        # Assert the prompt is constructed correctly
        assert "This is a test document." in prompt
        assert "'test' (test_entity)" in prompt
        assert "This is a test context." in prompt
        assert "You are an expert Medicare compliance officer" in prompt
