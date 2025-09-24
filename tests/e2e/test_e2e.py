from unittest.mock import patch
import pytest
from src.compliance_analyzer import ComplianceAnalyzer


@pytest.fixture
def mock_analyzer_compliant():
    """Fixture for a compliant document scenario."""
    with patch('src.compliance_analyzer.ComplianceAnalyzer', spec=ComplianceAnalyzer) as mock_analyzer_class:
        instance = mock_analyzer_class.return_value
        instance.analyze_document.return_value = {"findings": []}
        yield instance

@pytest.fixture
def mock_analyzer_non_compliant():
    """Fixture for a non-compliant document scenario."""
    with patch('src.compliance_analyzer.ComplianceAnalyzer', spec=ComplianceAnalyzer) as mock_analyzer_class:
        instance = mock_analyzer_class.return_value
        instance.analyze_document.return_value = {
            "findings": [
                {
                    "text": "Gait training on level surfaces with rolling walker for 100 feet with moderate assistance.",
                    "risk": "Lack of specific details on assistance provided.",
                    "suggestion": "Specify the type of assistance provided (e.g., verbal cues, physical support)."
                }
            ]
        }
        yield instance

def test_compliant_document(mock_analyzer_compliant):
    """Test a compliant document to ensure it passes with no findings."""
    with open("test_data/good_note_1.txt", "r") as f:
        document_text = f.read()

    analysis_results = mock_analyzer_compliant.analyze_document(document_text, discipline="pt")

    assert len(analysis_results['findings']) == 0


def test_non_compliant_document(mock_analyzer_non_compliant):
    """Test a non-compliant document to ensure it has findings."""
    with open("test_data/bad_note_1.txt", "r") as f:
        document_text = f.read()

    analysis_results = mock_analyzer_non_compliant.analyze_document(document_text, discipline="pt")

    assert len(analysis_results['findings']) > 0
    finding = analysis_results['findings'][0]
    assert "text" in finding
    assert "risk" in finding
    assert "suggestion" in finding
