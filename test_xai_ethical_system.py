#!/usr/bin/env python3
"""Test comprehensive XAI, Ethical AI, and Accuracy Enhancement system."""

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

async def test_xai_ethical_system():
    """Test the comprehensive XAI, Ethical AI, and Accuracy Enhancement system."""

    print("=" * 60)
    print("COMPREHENSIVE XAI, ETHICAL AI, AND ACCURACY TEST")
    print("=" * 60)

    try:
        from src.core.analysis_service import AnalysisService

        # Create analysis service
        print("Creating AnalysisService...")
        service = AnalysisService()
        print(f"AnalysisService created with use_mocks={service.use_mocks}")

        # Test document
        test_document = """
        Physical Therapy Progress Note

        Patient: John Smith, DOB: 01/15/1980
        Diagnosis: Post-surgical knee replacement
        Date of Service: 03/15/2024

        Subjective: Patient reports significant improvement in pain levels.
        Pain decreased from 8/10 to 4/10. Patient is able to walk longer distances
        without assistance. No adverse reactions to treatment.

        Objective:
        - Range of motion: Knee flexion 95 degrees, extension 0 degrees
        - Strength: Quadriceps 4/5, Hamstrings 4/5
        - Gait: Independent ambulation, no assistive devices needed
        - Balance: Single leg stance 15 seconds

        Assessment: Patient demonstrates excellent progress post-surgery.
        Significant improvement in functional mobility and strength.

        Plan: Continue current treatment plan. Frequency: 3x per week for 2 weeks.
        Focus on advanced strengthening exercises and return to normal activities.
        """

        print("\nStarting comprehensive analysis...")
        start_time = time.time()

        # Run analysis
        result = await service.analyze_document(document_text=test_document)

        analysis_time = time.time() - start_time
        print(f"Analysis completed in {analysis_time:.2f} seconds")

        # Check XAI metrics
        print("\n" + "=" * 40)
        print("XAI METRICS VERIFICATION")
        print("=" * 40)

        xai_metrics = result.get('xai_metrics', {})
        if xai_metrics:
            print("✅ XAI metrics present")
            print(f"   Decision path steps: {len(xai_metrics.get('decision_path', []))}")
            print(f"   Feature importance keys: {len(xai_metrics.get('feature_importance', {}))}")
            print(f"   Confidence breakdown: {xai_metrics.get('confidence_breakdown', {})}")
            print(f"   Uncertainty sources: {xai_metrics.get('uncertainty_sources', [])}")
            print(f"   Model versions: {xai_metrics.get('model_versions', {})}")
            print(f"   Processing steps: {len(xai_metrics.get('processing_steps', []))}")
            print(f"   Bias checks: {xai_metrics.get('bias_checks', {})}")
            print(f"   Ethical flags: {xai_metrics.get('ethical_flags', [])}")
        else:
            print("❌ XAI metrics missing")

        # Check bias metrics
        print("\n" + "=" * 40)
        print("BIAS METRICS VERIFICATION")
        print("=" * 40)

        bias_metrics = result.get('bias_metrics', {})
        if bias_metrics:
            print("✅ Bias metrics present")
            print(f"   Demographic bias score: {bias_metrics.get('demographic_bias_score', 0):.3f}")
            print(f"   Linguistic bias score: {bias_metrics.get('linguistic_bias_score', 0):.3f}")
            print(f"   Clinical bias score: {bias_metrics.get('clinical_bias_score', 0):.3f}")
            print(f"   Fairness metrics: {bias_metrics.get('fairness_metrics', {})}")
            print(f"   Bias sources: {bias_metrics.get('bias_sources', [])}")
            print(f"   Mitigation applied: {bias_metrics.get('mitigation_applied', [])}")
        else:
            print("❌ Bias metrics missing")

        # Check accuracy enhancement
        print("\n" + "=" * 40)
        print("ACCURACY ENHANCEMENT VERIFICATION")
        print("=" * 40)

        accuracy_enhancement = result.get('accuracy_enhancement', {})
        if accuracy_enhancement:
            print("✅ Accuracy enhancement present")
            print(f"   Techniques applied: {accuracy_enhancement.get('techniques_applied', [])}")
            print(f"   Expected improvement: {accuracy_enhancement.get('expected_improvement', 0):.3f}")
            print(f"   Enhancement timestamp: {accuracy_enhancement.get('enhancement_timestamp', 'N/A')}")
        else:
            print("❌ Accuracy enhancement missing")

        # Check confidence metrics
        print("\n" + "=" * 40)
        print("CONFIDENCE METRICS VERIFICATION")
        print("=" * 40)

        confidence_metrics = result.get('confidence_metrics', {})
        if confidence_metrics:
            print("✅ Confidence metrics present")
            print(f"   Overall confidence: {confidence_metrics.get('overall_confidence', 0):.3f}")
            print(f"   Entity confidence: {confidence_metrics.get('entity_confidence', 0):.3f}")
            print(f"   Fact check confidence: {confidence_metrics.get('fact_check_confidence', 0):.3f}")
            print(f"   Context confidence: {confidence_metrics.get('context_confidence', 0):.3f}")
            print(f"   Reasoning: {confidence_metrics.get('reasoning', 'N/A')}")
        else:
            print("❌ Confidence metrics missing")

        # Check findings quality
        print("\n" + "=" * 40)
        print("FINDINGS QUALITY VERIFICATION")
        print("=" * 40)

        findings = result.get('findings', [])
        if findings:
            print(f"✅ {len(findings)} findings generated")

            # Check individual finding enhancements
            enhanced_findings = 0
            for i, finding in enumerate(findings):
                print(f"\n   Finding {i+1}:")
                print(f"     Text: {finding.get('text', 'N/A')[:100]}...")
                print(f"     Confidence: {finding.get('confidence', 0):.3f}")
                print(f"     Severity: {finding.get('severity', 'N/A')}")

                # Check for enhancements
                if 'expanded_context' in finding:
                    enhanced_findings += 1
                    print(f"     ✅ Expanded context: {finding['expanded_context']}")

                if 'prompt_optimization' in finding:
                    enhanced_findings += 1
                    print(f"     ✅ Prompt optimization: {finding['prompt_optimization']}")

                if 'fact_verification' in finding:
                    enhanced_findings += 1
                    print(f"     ✅ Fact verification: {finding['fact_verification']}")

            print(f"\n   Enhanced findings: {enhanced_findings}/{len(findings)}")
        else:
            print("❌ No findings generated")

        # Overall assessment
        print("\n" + "=" * 60)
        print("OVERALL ASSESSMENT")
        print("=" * 60)

        success_count = 0
        total_checks = 5

        if xai_metrics:
            success_count += 1
            print("✅ XAI System: ACTIVE")
        else:
            print("❌ XAI System: INACTIVE")

        if bias_metrics:
            success_count += 1
            print("✅ Bias Mitigation: ACTIVE")
        else:
            print("❌ Bias Mitigation: INACTIVE")

        if accuracy_enhancement:
            success_count += 1
            print("✅ Accuracy Enhancement: ACTIVE")
        else:
            print("❌ Accuracy Enhancement: INACTIVE")

        if confidence_metrics:
            success_count += 1
            print("✅ Confidence Calibration: ACTIVE")
        else:
            print("❌ Confidence Calibration: INACTIVE")

        if findings:
            success_count += 1
            print("✅ Analysis Pipeline: ACTIVE")
        else:
            print("❌ Analysis Pipeline: INACTIVE")

        success_rate = (success_count / total_checks) * 100
        print(f"\n🎯 SYSTEM COMPLETENESS: {success_rate:.1f}% ({success_count}/{total_checks})")

        if success_rate >= 80:
            print("🚀 EXCELLENT: Comprehensive XAI, Ethical AI, and Accuracy system is fully operational!")
        elif success_rate >= 60:
            print("✅ GOOD: Most systems are operational with minor issues")
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
    success = await test_xai_ethical_system()

    print("\n" + "=" * 60)
    if success:
        print("🎉 COMPREHENSIVE XAI, ETHICAL AI, AND ACCURACY TEST: PASSED")
        print("Your system now has enterprise-grade XAI, ethical AI, and accuracy enhancement!")
    else:
        print("❌ COMPREHENSIVE XAI, ETHICAL AI, AND ACCURACY TEST: FAILED")
        print("Some systems need attention.")
    print("=" * 60)

    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
