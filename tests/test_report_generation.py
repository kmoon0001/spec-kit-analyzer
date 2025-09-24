import os
import sys
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.analysis_service import AnalysisService

from unittest.mock import patch

@pytest.mark.timeout(600)
def test_report_generation():
    """
    Tests the generation of the new HTML report.
    """
    report_file = "report.html"
    try:
        # Mock GuidelineService to avoid actual model loading
        with patch('src.core.analysis_service.GuidelineService') as mock_guideline_service:
            mock_guideline_service.return_value.search.return_value = []
            # 1. Initialize the AnalysisService
            service = AnalysisService()

            # 2. Define the test file
            test_file = "test_data/bad_note_1.txt"

        # 3. Run the analysis
        report_html = service.analyze_document(test_file)

        # 4. Save the report for inspection
        with open(report_file, "w") as f:
            f.write(report_html)

        # 5. Assert that the report contains the new sections
        assert "<h1>Clinical Compliance Report</h1>" in report_html
        assert "<h2>Analysis Summary</h2>" in report_html
        assert "<strong>Overall Compliance Score:</strong>" in report_html
        assert "<th>Recommendation</th>" in report_html
        assert "This report is auto-generated" in report_html

        print("\n--- Report Generation Test ---")
        print("Report generated successfully and contains all the new sections.")
        print("You can view the full report in `report.html`.")
        print("-----------------------------")
    finally:
        if os.path.exists(report_file):
            os.remove(report_file)
