import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Corrected imports
from core.compliance_analyzer import ComplianceAnalyzer
from document_classifier import DocumentClassifier, DocumentType
from parsing import parse_document_into_sections
from typing import Dict, List

class TestComplianceAnalyzer:

    # Note: The 'analyzer_instance' fixture is now function-scoped to ensure
    # that patches are applied correctly to each test function.
    @pytest.fixture(scope="function")
    def analyzer_instance(self):
        """
        Fixture to create a new ComplianceAnalyzer instance for each test function.
        """
        # We patch the heavy components to keep tests fast.
        with patch('core.compliance_analyzer.AutoModelForCausalLM.from_pretrained'), \
             patch('core.compliance_analyzer.AutoTokenizer.from_pretrained'), \
             patch('core.compliance_analyzer.pipeline'), \
             patch('core.compliance_analyzer.HybridRetriever'):
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

    def test_build_prompt(self, analyzer_instance):
        """Tests the building of the prompt."""
        document = "This is a test document."
        entity_list = "'test' (test_entity)"
        context = "- **Rule:** Test Rule\n  **Detail:** Test detail.\n  **Suggestion:** Test suggestion."
        prompt = analyzer_instance._build_prompt(document, entity_list, context)
        assert "This is a test document." in prompt
        assert "'test' (test_entity)" in prompt
        assert "Relevant Medicare Compliance Rules" in prompt
        assert "Test Rule" in prompt
        assert "You are an expert Medicare compliance officer" in prompt

    def test_analyze_document_integration(self, analyzer_instance):
        """
        A more integrated test for the analyze_document method.
        The HybridRetriever is already mocked in the fixture.
        """
        # Configure the mocked retriever instance that is part of the analyzer
        mock_retriever = analyzer_instance.retriever
        mock_rule = MagicMock()
        mock_rule.issue_title = "Test Rule"
        mock_rule.issue_detail = "This is a test rule detail."
        mock_rule.suggestion = "This is a test suggestion."
        mock_retriever.search.return_value = [mock_rule]

        # Mock the LLM's response
        mock_llm_output = """
        ```json
        {
          "findings": [
            {
              "text": "Gait training",
              "risk": "The test rule was violated.",
              "suggestion": "Follow the test suggestion."
            }
          ]
        }
        ```
        """
        analyzer_instance.generator_tokenizer.decode.return_value = mock_llm_output

        sample_document = "Gait training for 100 feet."

        analysis = analyzer_instance.analyze_document(sample_document, discipline="pt")

        # Assertions
        mock_retriever.search.assert_called_once()
        assert "findings" in analysis
        assert len(analysis["findings"]) == 1
        assert analysis["findings"][0]["risk"] == "The test rule was violated."
        print("\nSuccessfully tested analyze_document integration.")
