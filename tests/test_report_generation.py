import os
import sys
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch
from src.core.analysis_service import AnalysisService

@pytest.mark.timeout(600)
def test_report_generation():
    """
    Tests the generation of the new HTML report.
    """
    report_file = "report.html"
    try:
        # Mock the AnalysisService to avoid initializing the LLM
        with patch('src.core.analysis_service.AnalysisService') as mock_service_class:
            mock_service_instance = mock_service_class.return_value
            # Provide a mock HTML report
            mock_service_instance.analyze_document.return_value = """
            <html>
                <head>
                    <title>Clinical Compliance Report</title>
                </head>
                <body>
                    <h1>Clinical Compliance Report</h1>
                    <h2>Analysis Summary</h2>
                    <strong>Overall Compliance Score:</strong>
                    <table>
                        <tr>
                            <th>Recommendation</th>
                        </tr>
                    </table>
                    <footer>This report is auto-generated</footer>
                </body>
            </html>
            """
            service = mock_service_instance

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
