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

    # Note: The 'analyzer_instance' fixture is now function-scoped to ensure
    # that patches are applied correctly to each test function.
    @pytest.fixture(scope="function")
    def analyzer_instance(self):
        """
        Fixture to create a new ComplianceAnalyzer instance for each test function.
        """
        with patch('src.core.compliance_analyzer.HybridRetriever') as mock_hybrid_retriever:
            mock_retriever_instance = MagicMock()
            mock_rule = MagicMock()
            mock_rule.issue_title = "Test Rule"
            mock_retriever_instance.search.return_value = [mock_rule]
            mock_hybrid_retriever.return_value = mock_retriever_instance

            # We patch the heavy components to keep tests fast.
            with patch('src.core.compliance_analyzer.AutoModelForCausalLM.from_pretrained'), \
                 patch('src.core.compliance_analyzer.AutoTokenizer.from_pretrained'), \
                 patch('src.core.compliance_analyzer.pipeline'):
                instance = ComplianceAnalyzer()
                yield instance

    def test_document_classification(self, analyzer_instance):
        """Tests the document classifier with different inputs."""
        classifier = analyzer_instance.classifier
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
        assert "Relevant Medicare Guidelines" in prompt
        assert "Test Rule" in prompt
        assert "You are an expert Medicare compliance officer" in prompt
