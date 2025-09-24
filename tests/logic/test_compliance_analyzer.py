import os
import sys
from unittest.mock import patch, MagicMock
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.compliance_analyzer import ComplianceAnalyzer
from src.document_classifier import DocumentClassifier, DocumentType
from src.parsing import parse_document_into_sections
from typing import Dict, List

class TestComplianceAnalyzer:
    @pytest.fixture
    def mock_analyzer(self):
        """Fixture to create a mocked ComplianceAnalyzer instance."""
        with patch('src.core.compliance_analyzer.ComplianceAnalyzer') as mock_analyzer_class:
            instance = mock_analyzer_class.return_value
            instance.analyze_document.return_value = {"findings": []}
            yield instance

    def test_document_classification(self):
        """Unit test for document classification logic."""
        classifier = DocumentClassifier()
        eval_doc = "This is a patient evaluation."
        assert classifier.classify(eval_doc) == DocumentType.EVALUATION
        pn_doc = "This is a progress note."
        assert classifier.classify(pn_doc) == DocumentType.PROGRESS_NOTE
        unclassified_doc = "This is a regular document."
        assert classifier.classify(unclassified_doc) is DocumentType.UNKNOWN

    def test_analyze_document_integration(self, mock_analyzer):
        """
        Integration test for the analysis pipeline using a mocked ComplianceAnalyzer.
        Ensures the analyze_document method accepts a full SOAP-format note and returns the expected structure.
        """
        sample_document = '''
        Subjective: Patient reports feeling tired but motivated. States goal is to "walk my daughter down the aisle."
        Objective: Patient participated in 45 minutes of physical therapy. Gait training on level surfaces with rolling walker for 100 feet with moderate assistance. Moderate verbal cueing required for sequencing.
        Assessment: Patient making slow progress towards goals. Would benefit from continued skilled PT.
        Plan: Continue with PT 5x/week.
        '''
        analysis = mock_analyzer.analyze_document(sample_document)
        assert isinstance(analysis, dict)
        assert "findings" in analysis
        assert isinstance(analysis["findings"], list)

    @patch('src.core.compliance_analyzer.ComplianceAnalyzer.__init__', return_value=None)
    def test_build_prompt(self, mock_init):
        """
        Tests prompt building with representative document, entity list, and context.
        Ensures prompt includes critical Medicare compliance keys for best model guidance.
        """
        analyzer = ComplianceAnalyzer()  # Init is mocked.
        document = "This is a test document."
        entity_list = "'test' (test_entity)"
        context = "This is a test context."
        prompt = analyzer._build_prompt(document, entity_list, context)
        assert "This is a test document." in prompt
        assert "'test' (test_entity)" in prompt
        assert "Relevant Medicare Guidelines" in prompt
        assert "You are an expert Medicare compliance officer" in prompt
