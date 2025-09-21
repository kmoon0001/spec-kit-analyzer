import pytest
from src import reporting

def test_generate_report_paths():
    """
    Tests that the generate_report_paths function in the reporting module runs without errors.
    """
    # This is a simple test to ensure the function can be called.
    # A more comprehensive test would involve checking the format of the returned paths.
    pdf_path, csv_path = reporting.generate_report_paths()
    assert pdf_path.endswith(".pdf")
    assert csv_path.endswith(".csv")
