import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from compliance_analyzer import ComplianceAnalyzer

class TestComplianceAnalyzer:
    @patch('compliance_analyzer.ComplianceAnalyzer.__init__', return_value=None)
    def test_build_prompt(self, mock_init):
        # Create an instance of the analyzer (init is mocked)
        analyzer = ComplianceAnalyzer()

        # Define mock data
        document = "This is a test document."
        entities = [
            {'word': 'test', 'entity_group': 'test_entity'}
        ]
        context = "This is a test context."

        # Call the method
        prompt = analyzer._build_prompt(document, entities, context)

        # Assert the prompt is constructed correctly
        assert "This is a test document." in prompt
        assert "'test' (test_entity)" in prompt
        assert "This is a test context." in prompt
        assert "You are an expert Medicare compliance officer" in prompt

    @pytest.mark.slow
    def test_analyze_document_integration(self):
        # This is a slow integration test that loads the actual models.
        analyzer = ComplianceAnalyzer()

        # Sample document from the main script
        sample_document = "Patient with post-stroke hemiparesis is receiving physical therapy 3 times per week to improve gait and balance. The goal is to increase independence with ambulation. The patient is motivated and shows slow but steady progress. The SNF stay is covered under Medicare Part A."

        # Analyze the document
        analysis = analyzer.analyze_document(sample_document)

        # Assert that the analysis is a non-empty string
        assert isinstance(analysis, str)
        assert len(analysis) > 0
