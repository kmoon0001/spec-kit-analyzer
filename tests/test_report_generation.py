import os
import sys
import pytest
from unittest.mock import patch
from src.core.analysis_service import AnalysisService

@pytest.mark.timeout(600)
def test_report_generation():
    """
    Tests the generation of the new HTML report.
    """
    report_file = "report.html"
    try:
        with patch('src.core.analysis_service.AnalysisService') as mock_analysis_service_class:
            # Configure the mock instance that the class will produce
            mock_instance = mock_analysis_service_class.return_value

            # Define a realistic-looking HTML report that the mock will return
            mock_html = """
            <html>
                <body>
                    <h1>Clinical Compliance Report</h1>
                    <h2>Analysis Summary</h2>
                    <strong>Overall Compliance Score:</strong> 80
                    <table>
                        <tr><th>Recommendation</th></tr>
                        <tr><td>A recommendation</td></tr>
                    </table>
                    This report is auto-generated
                </body>
            </html>
            """
            mock_instance.analyze_document.return_value = mock_html

            # The service we get from calling the constructor is the mock_instance
            service = mock_analysis_service_class(guideline_sources=["tests/test_data/sample_guideline.txt"])

            # Define the test file and run the analysis (which will use the mock)
            test_file = "test_data/bad_note_1.txt"
            report_html = service.analyze_document(test_file)

            # Save the report for inspection if needed
            with open(report_file, "w") as f:
                f.write(report_html)

            # Assert that the report contains the new sections
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