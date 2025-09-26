import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock all the modules that are either missing or we want to isolate.
# We will use a fixture to apply these mocks for just this test file.
@pytest.fixture(autouse=True)
def mock_core_dependencies():
    MOCK_MODULES = {
        'src.core.nlg_service': MagicMock(),
        'src.core.preprocessing_service': MagicMock(),
        'src.core.risk_scoring_service': MagicMock(),
        'src.parsing': MagicMock(),
        'src.core.compliance_analyzer': MagicMock(),
        'src.core.hybrid_retriever': MagicMock(),
        'src.core.report_generator': MagicMock(),
        'src.core.document_classifier': MagicMock(),
        'src.core.llm_service': MagicMock(),
        'src.core.ner': MagicMock(),
        'src.core.explanation': MagicMock(),
        'src.core.prompt_manager': MagicMock(),
        'src.core.fact_checker_service': MagicMock(),
    }
    with patch.dict(sys.modules, MOCK_MODULES):
        yield

# Now we can import the service
from src.core.analysis_service import AnalysisService

def test_analysis_service_orchestration():
    """
    Tests the AnalysisService's orchestration logic in isolation.
    """
    # 1. Arrange: Configure the mocks to simulate a successful analysis
    # Use a more targeted patch for yaml to avoid interfering with other tests.
    with patch('src.core.analysis_service.yaml.safe_load') as mock_safe_load:
        mock_safe_load.return_value = {'models': {
            'generator': 'mock_generator', 'fact_checker': 'mock_fact_checker',
            'ner_ensemble': ['mock_ner'], 'doc_classifier_prompt': 'mock_prompt',
            'nlg_prompt_template': 'mock_template', 'analysis_prompt_template': 'mock_template'
        }}

        # Mock the return value of the parsing function
        from src.parsing import parse_document_content
        parse_document_content.return_value = [{'sentence': 'This is a test.'}]

        # Get the mock instances that will be created inside AnalysisService
        from src.core.preprocessing_service import PreprocessingService
        from src.core.document_classifier import DocumentClassifier
        from src.core.compliance_analyzer import ComplianceAnalyzer

        mock_preprocessor = PreprocessingService.return_value
        mock_doc_classifier = DocumentClassifier.return_value
        mock_analyzer = ComplianceAnalyzer.return_value

        # Configure the behavior of the mocked instances
        mock_preprocessor.correct_text.return_value = "This is a corrected test."
        mock_doc_classifier.classify_document.return_value = "Test Note"
        mock_analyzer.analyze_document.return_value = {"status": "success", "findings": ["finding1"]}

        # Create a dummy file for the service to "read"
        test_file_path = "test_data/fake_note.txt"
        os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
        with open(test_file_path, "w") as f:
            f.write("This is a test document.")

        # 2. Act: Instantiate the AnalysisService and run the analysis
        service = AnalysisService()
        result = service.analyze_document(file_path=test_file_path, discipline="ot")

        # 3. Assert: Verify the orchestration flow
        parse_document_content.assert_called_once_with(test_file_path)
        mock_preprocessor.correct_text.assert_called_once_with("This is a test.")
        mock_doc_classifier.classify_document.assert_called_once_with("This is a corrected test.")
        mock_analyzer.analyze_document.assert_called_once_with(
            document_text="This is a corrected test.",
            discipline="ot",
            doc_type="Test Note"
        )
        assert result == {"status": "success", "findings": ["finding1"]}

        # Clean up the dummy file
        os.remove(test_file_path)