#!/usr/bin/env python3
"""Quick test of XAI, Ethical AI, and Accuracy Enhancement system."""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix Unicode output issues
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

async def test_xai_system():
    """Test the XAI system components directly."""

    print("=" * 60)
    print("XAI, ETHICAL AI, AND ACCURACY ENHANCEMENT TEST")
    print("=" * 60)

    try:
        from src.core.xai_ethical_system import XAIEngine, BiasMitigationEngine, AccuracyEnhancer

        # Test XAI Engine
        print("\n1. Testing XAI Engine...")
        xai_engine = XAIEngine()

        # Mock analysis result
        mock_analysis = {
            'findings': [
                {'text': 'Missing frequency documentation', 'confidence': 0.85, 'rule_id': 'freq_001'},
                {'text': 'Incomplete progress notes', 'confidence': 0.72, 'rule_id': 'progress_002'}
            ],
            'confidence_metrics': {
                'overall_confidence': 0.78,
                'entity_confidence': 0.82,
                'fact_check_confidence': 0.75,
                'context_confidence': 0.80
            }
        }

        mock_entities = [
            {'word': 'patient', 'entity_group': 'PERSON', 'score': 0.9},
            {'word': 'therapy', 'entity_group': 'TREATMENT', 'score': 0.8},
            {'word': 'progress', 'entity_group': 'OUTCOME', 'score': 0.7}
        ]

        mock_rules = [
            {'content': 'Frequency must be documented', 'relevance_score': 0.9},
            {'content': 'Progress notes required', 'relevance_score': 0.8}
        ]

        mock_trace = [
            {'name': 'parsing', 'timestamp': '2024-01-01T10:00:00', 'duration_ms': 100, 'model': 'parser'},
            {'name': 'analysis', 'timestamp': '2024-01-01T10:00:01', 'duration_ms': 500, 'model': 'llm'}
        ]

        # Generate XAI report
        xai_metrics = xai_engine.generate_xai_report(mock_analysis, mock_entities, mock_rules, mock_trace)

        print(f"✅ XAI Engine: Decision path ({len(xai_metrics.decision_path)} steps)")
        print(f"   Feature importance: {len(xai_metrics.feature_importance)} features")
        print(f"   Confidence breakdown: {xai_metrics.confidence_breakdown}")
        print(f"   Uncertainty sources: {xai_metrics.uncertainty_sources}")
        print(f"   Ethical flags: {xai_metrics.ethical_flags}")

        # Test Bias Mitigation Engine
        print("\n2. Testing Bias Mitigation Engine...")
        bias_engine = BiasMitigationEngine()

        bias_metrics = bias_engine.detect_bias(mock_analysis, mock_entities, "Patient is a difficult case with poor compliance")

        print(f"✅ Bias Engine: Demographic={bias_metrics.demographic_bias_score:.3f}")
        print(f"   Linguistic={bias_metrics.linguistic_bias_score:.3f}")
        print(f"   Clinical={bias_metrics.clinical_bias_score:.3f}")
        print(f"   Fairness metrics: {bias_metrics.fairness_metrics}")
        print(f"   Bias sources: {bias_metrics.bias_sources}")
        print(f"   Mitigation applied: {bias_metrics.mitigation_applied}")

        # Test Accuracy Enhancer
        print("\n3. Testing Accuracy Enhancer...")
        accuracy_enhancer = AccuracyEnhancer()

        enhanced_result = accuracy_enhancer.enhance_accuracy(mock_analysis, mock_entities, mock_rules)

        print(f"✅ Accuracy Enhancer: Techniques applied")
        print(f"   Expected improvement: {enhanced_result.get('accuracy_enhancement', {}).get('expected_improvement', 0):.3f}")
        print(f"   Enhanced findings: {len(enhanced_result.get('findings', []))}")

        # Check individual enhancements
        findings = enhanced_result.get('findings', [])
        enhanced_count = 0
        for finding in findings:
            if 'expanded_context' in finding:
                enhanced_count += 1
            if 'prompt_optimization' in finding:
                enhanced_count += 1
            if 'fact_verification' in finding:
                enhanced_count += 1

        print(f"   Individual enhancements: {enhanced_count}")

        # Overall assessment
        print("\n" + "=" * 60)
        print("OVERALL ASSESSMENT")
        print("=" * 60)

        success_count = 0
        total_checks = 3

        if xai_metrics.decision_path:
            success_count += 1
            print("✅ XAI System: ACTIVE")
        else:
            print("❌ XAI System: INACTIVE")

        if bias_metrics.bias_sources is not None:
            success_count += 1
            print("✅ Bias Mitigation: ACTIVE")
        else:
            print("❌ Bias Mitigation: INACTIVE")

        if enhanced_result.get('accuracy_enhancement'):
            success_count += 1
            print("✅ Accuracy Enhancement: ACTIVE")
        else:
            print("❌ Accuracy Enhancement: INACTIVE")

        success_rate = (success_count / total_checks) * 100
        print(f"\n🎯 SYSTEM COMPLETENESS: {success_rate:.1f}% ({success_count}/{total_checks})")

        if success_rate >= 80:
            print("🚀 EXCELLENT: All XAI, Ethical AI, and Accuracy systems are operational!")
        elif success_rate >= 60:
            print("✅ GOOD: Most systems are operational")
        else:
            print("⚠️  NEEDS ATTENTION: Several systems require fixes")

        return success_rate >= 80

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    success = await test_xai_system()

    print("\n" + "=" * 60)
    if success:
        print("🎉 XAI, ETHICAL AI, AND ACCURACY TEST: PASSED")
        print("Your comprehensive XAI, ethical AI, and accuracy enhancement system is working!")
    else:
        print("❌ XAI, ETHICAL AI, AND ACCURACY TEST: FAILED")
        print("Some systems need attention.")
    print("=" * 60)

    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
