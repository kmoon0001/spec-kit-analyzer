"""
Tests for AI Guardrails Service

This module provides comprehensive tests for the AI guardrails system,
ensuring responsible AI controls, bias mitigation, and ethical compliance.
"""

import pytest
from unittest.mock import Mock

from src.core.ai_guardrails_service import (
    AIGuardrailsService,
    ContentSafetyGuardrail,
    BiasDetectionGuardrail,
    AccuracyValidationGuardrail,
    EthicalComplianceGuardrail,
    TransparencyEnforcementGuardrail,
    GuardrailType,
    RiskLevel,
    ActionType
)


class TestContentSafetyGuardrail:
    """Test ContentSafetyGuardrail functionality"""
    
    @pytest.fixture
    def guardrail(self):
        return ContentSafetyGuardrail()
    
    def test_safe_content_passes(self, guardrail):
        """Test that safe content passes without violations"""
        safe_content = "The patient showed improvement in mobility and strength."
        context = {"content_type": "clinical_note"}
        
        violations = guardrail.evaluate(safe_content, context)
        
        assert len(violations) == 0
    
    def test_harmful_language_detected(self, guardrail):
        """Test detection of harmful language"""
        harmful_content = "This treatment will kill the patient's pain completely."
        context = {"content_type": "clinical_note"}
        
        violations = guardrail.evaluate(harmful_content, context)
        
        assert len(violations) > 0
        assert any(v.violation_type == "prohibited_content" for v in violations)
        assert any(v.risk_level == RiskLevel.HIGH for v in violations)
    
    def test_inappropriate_medical_claims_detected(self, guardrail):
        """Test detection of inappropriate medical claims"""
        claim_content = "This treatment will definitely cure all patients completely."
        context = {"content_type": "recommendation"}
        
        violations = guardrail.evaluate(claim_content, context)
        
        assert len(violations) > 0
        assert any(v.violation_type == "inappropriate_medical_claims" for v in violations)
    
    def test_professional_content_passes(self, guardrail):
        """Test that professional medical content passes"""
        professional_content = """
        The patient demonstrates progress in functional mobility. 
        Treatment recommendations include continued physical therapy 
        with focus on strength and balance training.
        """
        context = {"content_type": "clinical_note"}
        
        violations = guardrail.evaluate(professional_content, context)
        
        assert len(violations) == 0


class TestBiasDetectionGuardrail:
    """Test BiasDetectionGuardrail functionality"""
    
    @pytest.fixture
    def guardrail(self):
        return BiasDetectionGuardrail()
    
    def test_inclusive_language_passes(self, guardrail):
        """Test that inclusive language passes without violations"""
        inclusive_content = "Patients may benefit from individualized treatment approaches."
        context = {"content_type": "recommendation"}
        
        violations = guardrail.evaluate(inclusive_content, context)
        
        assert len(violations) == 0
    
    def test_demographic_bias_detected(self, guardrail):
        """Test detection of demographic bias"""
        biased_content = "All elderly patients typically have compliance issues."
        context = {"content_type": "analysis"}
        
        violations = guardrail.evaluate(biased_content, context)
        
        assert len(violations) > 0
        assert any(v.violation_type == "demographic_bias" for v in violations)
        assert any(v.guardrail_type == GuardrailType.BIAS_DETECTION for v in violations)
    
    def test_socioeconomic_bias_detected(self, guardrail):
        """Test detection of socioeconomic bias"""
        biased_content = "Low-income patients usually have poor adherence to treatment."
        context = {"content_type": "analysis"}
        
        violations = guardrail.evaluate(biased_content, context)
        
        assert len(violations) > 0
        assert any(v.violation_type == "socioeconomic_bias" for v in violations)
    
    def test_geographic_bias_detected(self, guardrail):
        """Test detection of geographic bias"""
        biased_content = "Rural patients typically lack access to proper care."
        context = {"content_type": "analysis"}
        
        violations = guardrail.evaluate(biased_content, context)
        
        assert len(violations) > 0
        assert any(v.violation_type == "geographic_bias" for v in violations)


class TestAccuracyValidationGuardrail:
    """Test AccuracyValidationGuardrail functionality"""
    
    @pytest.fixture
    def guardrail(self):
        return AccuracyValidationGuardrail()
    
    def test_qualified_statements_pass(self, guardrail):
        """Test that properly qualified statements pass"""
        qualified_content = "This approach may be beneficial for some patients."
        context = {"content_type": "recommendation"}
        
        violations = guardrail.evaluate(qualified_content, context)
        
        # Should have no hallucination violations
        hallucination_violations = [v for v in violations if v.guardrail_type == GuardrailType.HALLUCINATION_DETECTION]
        assert len(hallucination_violations) == 0
    
    def test_potential_hallucination_detected(self, guardrail):
        """Test detection of potential hallucinations"""
        hallucination_content = "According to recent FDA research published last week, this new treatment shows 95.7% effectiveness."
        context = {"content_type": "analysis"}
        
        violations = guardrail.evaluate(hallucination_content, context)
        
        assert len(violations) > 0
        assert any(v.violation_type == "potential_hallucination" for v in violations)
        assert any(v.risk_level == RiskLevel.HIGH for v in violations)
    
    def test_overconfident_statements_detected(self, guardrail):
        """Test detection of overconfident statements"""
        overconfident_content = "This treatment will definitely work for all patients without exception."
        context = {"content_type": "recommendation"}
        
        violations = guardrail.evaluate(overconfident_content, context)
        
        assert len(violations) > 0
        assert any(v.violation_type == "overconfident_statements" for v in violations)


class TestEthicalComplianceGuardrail:
    """Test EthicalComplianceGuardrail functionality"""
    
    @pytest.fixture
    def guardrail(self):
        return EthicalComplianceGuardrail()
    
    def test_ethical_content_passes(self, guardrail):
        """Test that ethical content passes"""
        ethical_content = "Treatment decisions should consider patient autonomy and individual circumstances."
        context = {"content_type": "recommendation"}
        
        violations = guardrail.evaluate(ethical_content, context)
        
        ethical_violations = [v for v in violations if v.violation_type == "ethical_violation"]
        assert len(ethical_violations) == 0
    
    def test_ethical_violation_detected(self, guardrail):
        """Test detection of ethical violations"""
        unethical_content = "Force the patient to comply with treatment regardless of their wishes."
        context = {"content_type": "recommendation"}
        
        violations = guardrail.evaluate(unethical_content, context)
        
        assert len(violations) > 0
        assert any(v.violation_type == "ethical_violation" for v in violations)
        assert any(v.risk_level == RiskLevel.HIGH for v in violations)
        assert any(v.suggested_action == ActionType.BLOCK for v in violations)
    
    def test_missing_ethical_considerations_detected(self, guardrail):
        """Test detection of missing ethical considerations"""
        content_without_ethics = "Implement this treatment plan immediately."
        context = {"content_type": "treatment_plan"}
        
        violations = guardrail.evaluate(content_without_ethics, context)
        
        assert len(violations) > 0
        assert any(v.violation_type == "missing_ethical_considerations" for v in violations)


class TestTransparencyEnforcementGuardrail:
    """Test TransparencyEnforcementGuardrail functionality"""
    
    @pytest.fixture
    def guardrail(self):
        return TransparencyEnforcementGuardrail()
    
    def test_transparent_content_passes(self, guardrail):
        """Test that transparent content passes"""
        transparent_content = """
        This AI-generated analysis has moderate confidence and requires professional judgment.
        The system has limitations and should be validated by clinical expertise.
        """
        context = {"ai_generated": True, "content_type": "analysis"}
        
        violations = guardrail.evaluate(transparent_content, context)
        
        assert len(violations) == 0
    
    def test_missing_ai_disclosure_detected(self, guardrail):
        """Test detection of missing AI disclosure"""
        non_transparent_content = "This analysis shows clear patterns in the data."
        context = {"ai_generated": True, "content_type": "analysis"}
        
        violations = guardrail.evaluate(non_transparent_content, context)
        
        assert len(violations) > 0
        assert any(v.violation_type == "missing_ai_disclosure" for v in violations)
    
    def test_missing_confidence_indicators_detected(self, guardrail):
        """Test detection of missing confidence indicators"""
        content_without_confidence = "The AI system generated this recommendation."
        context = {"ai_generated": True, "content_type": "recommendation"}
        
        violations = guardrail.evaluate(content_without_confidence, context)
        
        assert len(violations) > 0
        assert any(v.violation_type == "missing_confidence_indicators" for v in violations)


class TestAIGuardrailsService:
    """Test AIGuardrailsService functionality"""
    
    @pytest.fixture
    def service(self):
        return AIGuardrailsService()
    
    def test_service_initialization(self, service):
        """Test service initialization"""
        assert len(service.guardrails) == 5  # Default guardrails
        assert service.transparency_templates is not None
        assert len(service.violation_history) == 0
    
    def test_safe_content_evaluation(self, service):
        """Test evaluation of safe content"""
        safe_content = "The patient shows improvement with current treatment plan."
        context = {"content_type": "clinical_note", "ai_generated": False}
        
        result = service.evaluate_content(safe_content, context)
        
        assert result.is_safe()
        assert result.action_taken == ActionType.ALLOW
        assert result.overall_risk_level == RiskLevel.LOW
        assert len(result.violations) == 0
    
    def test_unsafe_content_evaluation(self, service):
        """Test evaluation of unsafe content"""
        unsafe_content = "Force the patient to comply and guarantee complete cure."
        context = {"content_type": "recommendation", "ai_generated": True}
        
        result = service.evaluate_content(unsafe_content, context)
        
        assert not result.is_safe()
        assert result.action_taken in [ActionType.BLOCK, ActionType.MODIFY]
        assert result.overall_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert len(result.violations) > 0
    
    def test_content_modification(self, service):
        """Test content modification for violations"""
        problematic_content = "This treatment definitely works for all patients always."
        context = {"content_type": "recommendation", "ai_generated": True}
        
        result = service.evaluate_content(problematic_content, context)
        
        if result.modified_content:
            # Check that overconfident language was modified
            assert "definitely" not in result.modified_content.lower()
            assert "always" not in result.modified_content.lower()
    
    def test_transparency_statements_added(self, service):
        """Test that transparency statements are added when missing"""
        content_without_transparency = "This analysis shows significant patterns."
        context = {"content_type": "analysis", "ai_generated": True}
        
        result = service.evaluate_content(content_without_transparency, context)
        
        if result.modified_content:
            assert "AI Transparency Notice" in result.modified_content
            assert "artificial intelligence" in result.modified_content.lower()
    
    def test_confidence_adjustments(self, service):
        """Test confidence adjustments based on violations"""
        content_with_issues = "According to recent research, this treatment shows 100% success rate."
        context = {"content_type": "analysis", "ai_generated": True}
        
        result = service.evaluate_content(content_with_issues, context)
        
        assert len(result.confidence_adjustments) > 0
        # Should have negative adjustments for accuracy issues
        assert any(adj < 0 for adj in result.confidence_adjustments.values())
    
    def test_guardrail_statistics(self, service):
        """Test guardrail statistics collection"""
        # Generate some test evaluations
        test_contents = [
            "Safe content for testing",
            "This treatment definitely cures all patients",
            "Force patient compliance immediately"
        ]
        
        for content in test_contents:
            service.evaluate_content(content, {"content_type": "test", "ai_generated": True})
        
        stats = service.get_guardrail_statistics()
        
        assert stats['total_evaluations'] == 3
        assert 'violation_types' in stats
        assert 'risk_level_distribution' in stats
        assert 'action_distribution' in stats
        assert 'guardrail_status' in stats
    
    def test_guardrail_enable_disable(self, service):
        """Test enabling and disabling guardrails"""
        # Disable content safety guardrail
        success = service.disable_guardrail("Content Safety")
        assert success is True
        
        # Check that it's disabled
        content_safety = next((g for g in service.guardrails if g.name == "Content Safety"), None)
        assert content_safety is not None
        assert content_safety.enabled is False
        
        # Re-enable it
        success = service.enable_guardrail("Content Safety")
        assert success is True
        assert content_safety.enabled is True
    
    def test_custom_guardrail_addition(self, service):
        """Test adding custom guardrails"""
        # Create mock custom guardrail
        custom_guardrail = Mock()
        custom_guardrail.name = "Custom Test Guardrail"
        custom_guardrail.enabled = True
        
        initial_count = len(service.guardrails)
        service.add_custom_guardrail(custom_guardrail)
        
        assert len(service.guardrails) == initial_count + 1
        assert custom_guardrail in service.guardrails
    
    def test_violation_history_management(self, service):
        """Test violation history management"""
        # Generate test evaluation
        service.evaluate_content("Test content", {"content_type": "test"})
        
        assert len(service.violation_history) == 1
        
        # Clear history
        service.clear_violation_history()
        assert len(service.violation_history) == 0


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases"""
    
    def test_healthcare_specific_content(self):
        """Test guardrails with healthcare-specific content"""
        service = AIGuardrailsService()
        
        healthcare_content = """
        Patient presents with chronic pain. Treatment plan includes:
        1. Physical therapy 3x weekly
        2. Pain management consultation
        3. Patient education on self-care techniques
        
        Prognosis is generally positive with patient compliance.
        Professional judgment required for medication adjustments.
        """
        
        context = {
            "content_type": "treatment_plan",
            "healthcare_context": True,
            "ai_generated": True
        }
        
        result = service.evaluate_content(healthcare_content, context)
        
        # Should pass with minimal violations
        assert result.is_safe()
        assert result.overall_risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
    
    def test_multiple_violation_types(self):
        """Test content with multiple types of violations"""
        service = AIGuardrailsService()
        
        problematic_content = """
        All elderly patients definitely have compliance problems.
        Recent FDA research proves this treatment cures 100% of cases.
        Force patients to follow the protocol without exception.
        """
        
        context = {"content_type": "analysis", "ai_generated": True}
        
        result = service.evaluate_content(problematic_content, context)
        
        # Should detect multiple violation types
        violation_types = {v.guardrail_type for v in result.violations}
        assert len(violation_types) > 1
        
        # Should have high risk level
        assert result.overall_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # Should require blocking or significant modification
        assert result.action_taken in [ActionType.BLOCK, ActionType.MODIFY]
    
    def test_edge_case_empty_content(self):
        """Test handling of empty content"""
        service = AIGuardrailsService()
        
        result = service.evaluate_content("", {"content_type": "test"})
        
        assert result.is_safe()
        assert result.overall_risk_level == RiskLevel.LOW
        assert len(result.violations) == 0
    
    def test_edge_case_very_long_content(self):
        """Test handling of very long content"""
        service = AIGuardrailsService()
        
        long_content = "This is safe content. " * 1000  # Very long but safe
        context = {"content_type": "analysis", "ai_generated": True}
        
        result = service.evaluate_content(long_content, context)
        
        # Should handle long content without errors
        assert result is not None
        assert result.content_id is not None


if __name__ == "__main__":
    pytest.main([__file__])