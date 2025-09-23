import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from compliance_analyzer import ComplianceAnalyzer
from document_classifier import DocumentClassifier, DocumentType
from enum import Enum

class TestComplianceAnalyzer:
    @pytest.mark.slow
    def test_build_prompt_integration(self):
        # Create an instance of the analyzer
        analyzer = ComplianceAnalyzer()

        # Define mock data
        document = "This is a test document."
        entities = [
            {'word': 'test', 'entity_group': 'test_entity'}
        ]
        context = "This is a test context."
        doc_type = DocumentType.EVALUATION
        rubric = "This is a test rubric."

        # Call the method
        prompt = analyzer._build_prompt(document, entities, context, doc_type, rubric)

        # Assert the prompt is constructed correctly
        assert "This is a test document." in prompt
        assert "'test' (test_entity)" in prompt
        assert "This is a test context." in prompt
        assert "You are an expert Medicare compliance officer" in prompt
        assert "Document Type: Evaluation" in prompt
        assert "Compliance Rubric for Evaluation:" in prompt
        assert "This is a test rubric." in prompt

    def test_document_classification(self):
        classifier = DocumentClassifier()

        # Test evaluation document
        eval_doc = "This is a patient evaluation."
        assert classifier.classify(eval_doc) == DocumentType.EVALUATION

        # Test progress note document
        pn_doc = "This is a progress note."
        assert classifier.classify(pn_doc) == DocumentType.PROGRESS_NOTE

        # Test unclassified document
        unclassified_doc = "This is a regular document."
        assert classifier.classify(unclassified_doc) is None

    @patch('compliance_analyzer.ComplianceAnalyzer.__init__', return_value=None)
    def test_rubric_loading(self, mock_init):
        analyzer = ComplianceAnalyzer()

        # Create dummy rubric files
        os.makedirs("resources/rubrics", exist_ok=True)
        with open("resources/rubrics/evaluation_rubric.txt", "w") as f:
            f.write("Evaluation Rubric")
        with open("resources/rubrics/progress_note_rubric.txt", "w") as f:
            f.write("Progress Note Rubric")

        # Test loading evaluation rubric
        rubric = analyzer._load_rubric(DocumentType.EVALUATION)
        assert rubric == "Evaluation Rubric"

        # Test loading progress note rubric
        rubric = analyzer._load_rubric(DocumentType.PROGRESS_NOTE)
        assert rubric == "Progress Note Rubric"

        # Test loading with no doc type
        rubric = analyzer._load_rubric(None)
        assert rubric is None

        # Clean up dummy files
        os.remove("resources/rubrics/evaluation_rubric.txt")
        os.remove("resources/rubrics/progress_note_rubric.txt")

    @pytest.mark.slow
    def test_analyze_document_integration(self):
        # This is a slow integration test that loads the actual models.
        analyzer = ComplianceAnalyzer()

        # Sample document from the main script
        sample_document = "Patient with post-stroke hemiparesis is receiving physical therapy 3 times per week to improve gait and balance. The goal is to increase independence with ambulation. The patient is motivated and shows slow but steady progress. The SNF stay is covered under Medicare Part A. This is an evaluation."

        # Analyze the document
        analysis = analyzer.analyze_document(sample_document)

        # Assert that the analysis is a non-empty string
        assert isinstance(analysis, str)
        assert len(analysis) > 0
