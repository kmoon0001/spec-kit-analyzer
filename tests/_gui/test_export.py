import pytest
from unittest.mock import MagicMock, patch
from src.gui.export import generate_pdf_report
import json


@patch("src.gui.export.QFileDialog.getSaveFileName")
@patch("src.gui.export.pisa")
def test_generate_pdf_report(mock_pisa, mock_get_save_file_name):
    """
    Tests the successful generation of a PDF report.
    """
    # Arrange
    mock_get_save_file_name.return_value = ("test_report.pdf", "PDF Files (*.pdf)")
    mock_pisa.CreatePDF.return_value = MagicMock(err=0)

    analysis_results = {
        "findings": [
            {
                "rule_id": "test_rule_1",
                "risk": "High",
                "suggestion": "Sign it",
                "text": "Something",
            }
        ],
        "guidelines": ["guideline 1", "guideline 2"],
    }
    analysis_results_str = json.dumps(analysis_results)

    # Act
    success, message = generate_pdf_report(analysis_results_str)

    # Assert
    assert success is True
    assert message == "test_report.pdf"
    mock_pisa.CreatePDF.assert_called_once()
