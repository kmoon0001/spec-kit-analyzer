import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from compliance_analyzer import ComplianceAnalyzer
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from compliance_analyzer import ComplianceAnalyzer
from document_classifier import DocumentClassifier, DocumentType
from parsing import parse_document_into_sections
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
        assert classifier.classify(unclassified_doc) is None

    @patch('compliance_analyzer.ComplianceAnalyzer.__init__', return_value=None)
    def test_rubric_loading(self, mock_init):
        """Tests rubric loading logic in a fast unit test."""
        analyzer = ComplianceAnalyzer()
        os.makedirs("resources/rubrics", exist_ok=True)
        with open("resources/rubrics/evaluation_rubric.txt", "w") as f:
            f.write("Evaluation Rubric Content")
        rubric = analyzer._load_rubric(DocumentType.EVALUATION)
        assert rubric == "Evaluation Rubric Content"
        os.remove("resources/rubrics/evaluation_rubric.txt")

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

    @patch('compliance_analyzer.ComplianceAnalyzer.__init__', return_value=None)
    def test_build_section_prompt_fast(self, mock_init):
        """
        Tests the construction of the section-specific prompt in a fast unit test
        by mocking the analyzer's __init__ method.
        """
        analyzer = ComplianceAnalyzer()
        section_name = "Objective"
        section_text = "Patient walked 100 feet."
        entities = [{'word': 'patient', 'entity_group': 'person'}]
        context = "Guideline about walking."
        doc_type = DocumentType.PROGRESS_NOTE
        rubric = "Rubric about progress."
        prompt = analyzer._build_section_prompt(section_name, section_text, entities, context, doc_type, rubric)
        assert "**Section to Analyze:** Objective" in prompt
        assert "**Content of the 'Objective' section:**" in prompt
        assert "Patient walked 100 feet." in prompt
        assert "Guideline about walking." in prompt
        assert "**Section Compliance Analysis:**" in prompt
        assert "**Document Type:** Progress Note" in prompt
        assert "Rubric about progress." in prompt

        analysis = analyzer.analyze_document(sample_document)

        assert isinstance(analysis, dict)
        assert "Subjective" in analysis
        assert "Objective" in analysis
        assert "Assessment" in analysis
        assert "Plan" in analysis
        assert isinstance(analysis["Subjective"], str)
        assert len(analysis["Subjective"]) > 0
