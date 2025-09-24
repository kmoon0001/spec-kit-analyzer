import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.compliance_analyzer import ComplianceAnalyzer
from src.document_classifier import DocumentClassifier, DocumentType
from src.parsing import parse_document_into_sections
from typing import Dict, List
from src.rubric_service import ComplianceRule

class TestComplianceAnalyzer:

    # Note: The 'analyzer_instance' fixture is now function-scoped to ensure
    # that patches are applied correctly to each test function.
    @pytest.fixture(scope="function")
    def analyzer_instance(self):
        """
        Fixture to create a new ComplianceAnalyzer instance for each test function.
        """
        with patch('src.core.compliance_analyzer.AutoModelForCausalLM.from_pretrained'), \
             patch('src.core.compliance_analyzer.AutoTokenizer.from_pretrained'), \
             patch('src.core.compliance_analyzer.GuidelineService'), \
             patch('src.core.compliance_analyzer.load_config'):

            instance = ComplianceAnalyzer()
            yield instance

    def test_health_check(self, analyzer_instance):
        """Tests the AI system health check."""
        is_healthy, message = analyzer_instance.check_ai_systems_health()
        assert is_healthy
        assert message == "AI Systems: Online"

    def test_build_hybrid_prompt(self, analyzer_instance):
        """Tests the construction of the hybrid prompt."""
        document = "This is a test document."
        entity_list = "'test' (test_entity)"
        rules = [
            ComplianceRule(
                uri='test_rule_1',
                severity='High',
                strict_severity='Must',
                issue_title='Missing Signature',
                issue_detail='The document is missing a therapist signature.',
                issue_category='Documentation',
                discipline='PT',
                suggestion='Please ensure the therapist signs the document.'
            ),
            ComplianceRule(
                uri='test_rule_2',
                severity='Low',
                strict_severity='Should',
                issue_title='Illegible Handwriting',
                issue_detail='The handwriting in the document is difficult to read.',
                issue_category='Documentation',
                discipline='OT',
                suggestion='Please ensure all notes are legible.'
            )
        ]
        prompt = analyzer_instance._build_hybrid_prompt(document, entity_list, rules)
        assert "This is a test document." in prompt
        assert "'test' (test_entity)" in prompt
        assert "Rule 1: Missing Signature" in prompt
        assert "Rule 2: Illegible Handwriting" in prompt
        assert "You are an expert Medicare compliance officer" in prompt

    @patch('src.core.compliance_analyzer.ComplianceAnalyzer._get_rules_for_discipline')
    def test_analyze_document_hybrid_mode(self, mock_get_rules, analyzer_instance):
        """Tests the analyze_document method in hybrid mode."""
        mock_get_rules.return_value = [
            ComplianceRule(
                uri='test_rule_1',
                severity='High',
                strict_severity='Must',
                issue_title='Missing Signature',
                issue_detail='The document is missing a therapist signature.',
                issue_category='Documentation',
                discipline='PT',
                suggestion='Please ensure the therapist signs the document.'
            )
        ]
        analyzer_instance.generator_model.generate.return_value = MagicMock()
        analyzer_instance.tokenizer.decode.return_value = '{"findings": [{"rule_id": "test_rule_1", "risk": "High", "suggestion": "Sign it", "text": "Something"}]}'

        result = analyzer_instance.analyze_document("test doc", "PT", "hybrid")

        assert result['findings'][0]['rule_id'] == 'test_rule_1'

    def test_analyze_document_llm_only_mode(self, analyzer_instance):
        """Tests the analyze_document method in llm_only mode."""
        analyzer_instance.guideline_service.search.return_value = [{"source": "test", "text": "test"}]
        analyzer_instance.generator_model.generate.return_value = MagicMock()
        analyzer_instance.tokenizer.decode.return_value = '{"findings": [{"risk": "High", "suggestion": "Sign it", "text": "Something"}]}'

        result = analyzer_instance.analyze_document("test doc", "PT", "llm_only")

        assert result['findings'][0]['risk'] == 'High'
