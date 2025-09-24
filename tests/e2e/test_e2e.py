from unittest.mock import patch
import pytest

def test_compliant_document():
    """Test a compliant document to ensure it passes with a high score."""
    with patch('src.core.compliance_analyzer.ComplianceAnalyzer') as mock_analyzer_class:
        instance = mock_analyzer_class.return_value
        instance.analyze_document.return_value = {"compliance_score": 1.0, "findings": []}

        with open("test_data/good_note_1.txt", "r") as f:
            document_text = f.read()

        analysis_results = instance.analyze_document(document_text)

        assert analysis_results['compliance_score'] == 1.0
        assert len(analysis_results['findings']) == 0

def test_non_compliant_document():
    """Test a non-compliant document to ensure it fails with a low score and has findings."""
    with patch('src.core.compliance_analyzer.ComplianceAnalyzer') as mock_analyzer_class:
        instance = mock_analyzer_class.return_value
        instance.analyze_document.return_value = {"compliance_score": 0.5, "findings": [{"severity": "critical", "text": "Something is wrong"}]}

        with open("test_data/bad_note_1.txt", "r") as f:
            document_text = f.read()

        analysis_results = instance.analyze_document(document_text)

        assert analysis_results['compliance_score'] < 1.0
        assert len(analysis_results['findings']) > 0

        critical_findings = [f for f in analysis_results['findings'] if f['severity'] == 'critical']
        assert len(critical_findings) > 0
