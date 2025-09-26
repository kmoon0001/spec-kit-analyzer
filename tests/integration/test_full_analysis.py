import os
import sys
import pytest
import json

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import ComplianceAnalyzer
from src.guideline_service import GuidelineService
from src.report_generator import ReportGenerator
from src.utils import load_config

class MockRetriever:
    def __init__(self, guideline_service):
        self.guidelines = []
        # This mock retriever will directly load the content from the JSON source files
        # to ensure the analyzer gets the dictionary format it expects.
        for path in guideline_service.source_paths:
            if path.lower().endswith('.json'):
                with open(path, 'r') as f:
                    self.guidelines.extend(json.load(f))

    def retrieve(self, query):
        """Returns the list of guideline dictionaries."""
        return self.guidelines

@pytest.fixture(scope="module")
def config():
    """Loads the application configuration."""
    return load_config()

@pytest.fixture(scope="module")
def test_data_path():
    """Returns the path to the test data directory."""
    return os.path.join(os.path.dirname(__file__), "test_data")

@pytest.fixture(scope="module")
def setup_test_files(test_data_path):
    """Creates dummy test files for the analysis."""
    os.makedirs(test_data_path, exist_ok=True)

    # Create a dummy guideline file
    guideline_content = [{
        "id": "GH-001",
        "issue_title": "Lack of quantifiable progress",
        "issue_detail": "The patient's progress towards goals is not objectively measured or quantified.",
        "suggestion": "Use standardized tests or measurements to track progress."
    }]
    with open(os.path.join(test_data_path, "test_guidelines.json"), "w") as f:
        json.dump(guideline_content, f)

    # Create a dummy document
    document_content = "The patient reports feeling better. Progress towards goals is good."
    with open(os.path.join(test_data_path, "test_document.txt"), "w") as f:
        f.write(document_content)

@pytest.mark.timeout(600)
def test_full_analysis_pipeline(config, test_data_path, setup_test_files):
    """Tests the full analysis pipeline from document to HTML report."""
    # 1. Initialize services
    guideline_service = GuidelineService(sources=[os.path.join(test_data_path, "test_guidelines.json")])
    retriever = MockRetriever(guideline_service)
    analyzer = ComplianceAnalyzer(config, guideline_service, retriever)
    report_generator = ReportGenerator(template_path="src")

    # 2. Define parameters
    document_path = os.path.join(test_data_path, "test_document.txt")
    with open(document_path, "r") as f:
        document_text = f.read()

    # 3. Run analysis
    analysis_result = analyzer.analyze_document(
        document=document_text,
        discipline="PT",
        doc_type="progress_note"
    )

    # 4. Assert analysis results
    assert "findings" in analysis_result
    assert len(analysis_result["findings"]) > 0
    finding = analysis_result["findings"][0]
    assert "issue_title" in finding
    assert "reasoning" in finding
    assert "suggestion" in finding
    assert "confidence" in finding
    assert "explanation" in finding

    # 5. Generate report
    report_path = os.path.join(test_data_path, "test_report.html")
    report_generated = report_generator.generate_html_report(analysis_result, report_path)

    # 6. Assert report generation
    assert report_generated
    assert os.path.exists(report_path)
    with open(report_path, "r") as f:
        report_content = f.read()
    assert "Compliance Analysis Report" in report_content
    assert finding["issue_title"] in report_content
    assert finding["reasoning"] in report_content