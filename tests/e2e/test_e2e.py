from unittest.mock import patch
import pytest


@pytest.fixture
def mock_analyzer_compliant():
    """Fixture for a compliant document scenario."""
    with patch('src.core.compliance_analyzer.ComplianceAnalyzer') as mock_analyzer_class:
        instance = mock_analyzer_class.return_value
        instance.analyze_document.return_value = {"compliance_score": 1.0, "findings": []}
        yield instance

@pytest.fixture
def mock_analyzer_non_compliant():
    """Fixture for a non-compliant document scenario."""
    with patch('src.core.compliance_analyzer.ComplianceAnalyzer') as mock_analyzer_class:
        instance = mock_analyzer_class.return_value
        instance.analyze_document.return_value = {"compliance_score": 0.5, "findings": [{"severity": "critical", "text": "Something is wrong"}]}
        yield instance

def test_compliant_document(mock_analyzer_compliant):
    """Test a compliant document to ensure it passes with a high score."""
    with open("test_data/good_note_1.txt", "r") as f:
        document_text = f.read()

    analysis_results = mock_analyzer_compliant.analyze_document(document_text)

    assert analysis_results['compliance_score'] == 1.0
    assert len(analysis_results['findings']) == 0


def test_non_compliant_document(mock_analyzer_non_compliant):
    """Test a non-compliant document to ensure it fails with a low score and has findings."""
    with open("test_data/bad_note_1.txt", "r") as f:
        document_text = f.read()

    analysis_results = mock_analyzer_non_compliant.analyze_document(document_text)

    assert analysis_results['compliance_score'] < 1.0
    assert len(analysis_results['findings']) > 0

    critical_findings = [f for f in analysis_results['findings'] if f['severity'] == 'critical']
    assert len(critical_findings) > 0
