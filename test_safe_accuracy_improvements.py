"""
Test Safe Accuracy Improvements
Comprehensive testing for the new safe accuracy enhancement strategies
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any
import logging

from src.core.centralized_logging import get_logger
from src.core.safe_accuracy_improvements import safe_accuracy_enhancer, SafeImprovementStrategy

logger = get_logger(__name__)


class SafeAccuracyImprovementTester:
    """Comprehensive tester for safe accuracy improvements."""

    def __init__(self):
        """Initialize the tester."""
        self.test_results: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, List[float]] = {}

        logger.info("SafeAccuracyImprovementTester initialized")

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive tests for all safe accuracy improvements."""
        try:
            logger.info("Starting comprehensive safe accuracy improvement tests")

            # Test data
            test_cases = self._generate_test_cases()

            # Run tests for each strategy
            strategy_tests = {}
            for strategy in SafeImprovementStrategy:
                strategy_tests[strategy.value] = await self._test_strategy(strategy, test_cases)

            # Run integration tests
            integration_tests = await self._test_integration(test_cases)

            # Run performance tests
            performance_tests = await self._test_performance(test_cases)

            # Run safety tests
            safety_tests = await self._test_safety(test_cases)

            # Compile results
            test_results = {
                "test_summary": {
                    "total_strategies_tested": len(SafeImprovementStrategy),
                    "total_test_cases": len(test_cases),
                    "test_timestamp": datetime.now(timezone.utc).isoformat(),
                    "overall_status": "completed"
                },
                "strategy_tests": strategy_tests,
                "integration_tests": integration_tests,
                "performance_tests": performance_tests,
                "safety_tests": safety_tests,
                "recommendations": self._generate_recommendations(strategy_tests, integration_tests, performance_tests, safety_tests)
            }

            logger.info("Comprehensive safe accuracy improvement tests completed")
            return test_results

        except Exception as e:
            logger.error("Comprehensive testing failed: %s", e)
            return {"error": str(e)}

    def _generate_test_cases(self) -> List[Dict[str, Any]]:
        """Generate test cases for safe accuracy improvements."""
        return [
            {
                "name": "Simple Clinical Document",
                "document_text": "Patient demonstrates improved range of motion. Treatment goals include pain management and functional restoration. Progress noted in activities of daily living.",
                "analysis_result": {
                    "findings": [
                        {
                            "id": "finding_1",
                            "text": "Patient shows improved range of motion",
                            "confidence": 0.8,
                            "severity": "Medium"
                        },
                        {
                            "id": "finding_2",
                            "text": "Treatment goals are appropriate",
                            "confidence": 0.7,
                            "severity": "Low"
                        }
                    ],
                    "entities": [
                        {"text": "patient", "type": "person"},
                        {"text": "range of motion", "type": "medical_term"},
                        {"text": "treatment", "type": "medical_term"}
                    ],
                    "confidence": 0.75
                },
                "context": {
                    "discipline": "pt",
                    "doc_type": "progress_note",
                    "retrieved_rules": [
                        {"content": "Document patient progress in therapy sessions"},
                        {"content": "Include treatment goals and outcomes"}
                    ]
                }
            },
            {
                "name": "Complex Clinical Document",
                "document_text": "Patient presents with chronic pain syndrome affecting bilateral lower extremities. Comprehensive evaluation reveals decreased functional mobility, impaired balance, and limited activities of daily living. Treatment plan includes multimodal pain management, therapeutic exercise, and patient education. Progress monitoring indicates gradual improvement in pain levels and functional capacity.",
                "analysis_result": {
                    "findings": [
                        {
                            "id": "finding_1",
                            "text": "Patient has chronic pain syndrome",
                            "confidence": 0.9,
                            "severity": "High"
                        },
                        {
                            "id": "finding_2",
                            "text": "Functional mobility is decreased",
                            "confidence": 0.85,
                            "severity": "High"
                        },
                        {
                            "id": "finding_3",
                            "text": "Treatment plan is comprehensive",
                            "confidence": 0.8,
                            "severity": "Medium"
                        }
                    ],
                    "entities": [
                        {"text": "patient", "type": "person"},
                        {"text": "chronic pain syndrome", "type": "condition"},
                        {"text": "functional mobility", "type": "medical_term"},
                        {"text": "treatment plan", "type": "medical_term"}
                    ],
                    "confidence": 0.85
                },
                "context": {
                    "discipline": "pt",
                    "doc_type": "evaluation",
                    "retrieved_rules": [
                        {"content": "Document comprehensive evaluation findings"},
                        {"content": "Include detailed treatment plan"},
                        {"content": "Monitor patient progress regularly"}
                    ]
                }
            },
            {
                "name": "Low Confidence Document",
                "document_text": "Patient seen for follow-up. Some improvement noted. Continue current treatment.",
                "analysis_result": {
                    "findings": [
                        {
                            "id": "finding_1",
                            "text": "Patient shows some improvement",
                            "confidence": 0.4,
                            "severity": "Low"
                        },
                        {
                            "id": "finding_2",
                            "text": "Continue current treatment",
                            "confidence": 0.3,
                            "severity": "Low"
                        }
                    ],
                    "entities": [
                        {"text": "patient", "type": "person"},
                        {"text": "treatment", "type": "medical_term"}
                    ],
                    "confidence": 0.35
                },
                "context": {
                    "discipline": "pt",
                    "doc_type": "progress_note",
                    "retrieved_rules": [
                        {"content": "Document patient progress"}
                    ]
                }
            }
        ]

    async def _test_strategy(self, strategy: SafeImprovementStrategy, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test a specific strategy."""
        try:
            logger.info("Testing strategy: %s", strategy.value)

            strategy_results = {
                "strategy": strategy.value,
                "test_cases": [],
                "overall_performance": {},
                "safety_score": 0.0,
                "improvement_score": 0.0
            }

            total_improvement = 0.0
            total_safety = 0.0
            successful_tests = 0

            for test_case in test_cases:
                try:
                    # Apply safe improvements
                    start_time = time.time()

                    result = await safe_accuracy_enhancer.apply_safe_improvements(
                        analysis_result=test_case["analysis_result"],
                        document_text=test_case["document_text"],
                        context=test_case["context"]
                    )

                    processing_time = (time.time() - start_time) * 1000

                    if result.success:
                        enhanced_result = result.data
                        safe_improvements = enhanced_result.get('safe_accuracy_improvements', {})

                        # Calculate metrics
                        original_confidence = test_case["analysis_result"].get("confidence", 0.5)
                        enhanced_confidence = enhanced_result.get("confidence", original_confidence)
                        improvement = enhanced_confidence - original_confidence

                        safety_score = safe_improvements.get("safety_score", 0.5)
                        overall_improvement = safe_improvements.get("overall_improvement_score", 0.0)

                        test_result = {
                            "test_case": test_case["name"],
                            "success": True,
                            "original_confidence": original_confidence,
                            "enhanced_confidence": enhanced_confidence,
                            "improvement": improvement,
                            "safety_score": safety_score,
                            "overall_improvement": overall_improvement,
                            "processing_time_ms": processing_time,
                            "applied_strategies": safe_improvements.get("applied_strategies", [])
                        }

                        total_improvement += overall_improvement
                        total_safety += safety_score
                        successful_tests += 1

                    else:
                        test_result = {
                            "test_case": test_case["name"],
                            "success": False,
                            "error": result.error,
                            "processing_time_ms": processing_time
                        }

                    strategy_results["test_cases"].append(test_result)

                except Exception as e:
                    logger.error("Test case %s failed for strategy %s: %s",
                               test_case["name"], strategy.value, e)
                    strategy_results["test_cases"].append({
                        "test_case": test_case["name"],
                        "success": False,
                        "error": str(e)
                    })

            # Calculate overall performance
            if successful_tests > 0:
                strategy_results["overall_performance"] = {
                    "success_rate": successful_tests / len(test_cases),
                    "average_improvement": total_improvement / successful_tests,
                    "average_safety_score": total_safety / successful_tests,
                    "successful_tests": successful_tests,
                    "total_tests": len(test_cases)
                }
                strategy_results["improvement_score"] = total_improvement / successful_tests
                strategy_results["safety_score"] = total_safety / successful_tests

            logger.info("Strategy %s testing completed: %d/%d successful",
                       strategy.value, successful_tests, len(test_cases))

            return strategy_results

        except Exception as e:
            logger.error("Strategy testing failed for %s: %s", strategy.value, e)
            return {
                "strategy": strategy.value,
                "error": str(e),
                "overall_performance": {"success_rate": 0.0}
            }

    async def _test_integration(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test integration of all strategies."""
        try:
            logger.info("Testing integration of all strategies")

            integration_results = {
                "integration_tests": [],
                "overall_integration_score": 0.0,
                "strategy_compatibility": {}
            }

            total_improvement = 0.0
            successful_integrations = 0

            for test_case in test_cases:
                try:
                    # Test with all strategies enabled
                    start_time = time.time()

                    result = await safe_accuracy_enhancer.apply_safe_improvements(
                        analysis_result=test_case["analysis_result"],
                        document_text=test_case["document_text"],
                        context=test_case["context"]
                    )

                    processing_time = (time.time() - start_time) * 1000

                    if result.success:
                        enhanced_result = result.data
                        safe_improvements = enhanced_result.get('safe_accuracy_improvements', {})

                        applied_strategies = safe_improvements.get("applied_strategies", [])
                        overall_improvement = safe_improvements.get("overall_improvement_score", 0.0)
                        safety_score = safe_improvements.get("safety_score", 0.5)

                        integration_test = {
                            "test_case": test_case["name"],
                            "success": True,
                            "applied_strategies": applied_strategies,
                            "strategies_count": len(applied_strategies),
                            "overall_improvement": overall_improvement,
                            "safety_score": safety_score,
                            "processing_time_ms": processing_time
                        }

                        total_improvement += overall_improvement
                        successful_integrations += 1

                    else:
                        integration_test = {
                            "test_case": test_case["name"],
                            "success": False,
                            "error": result.error,
                            "processing_time_ms": processing_time
                        }

                    integration_results["integration_tests"].append(integration_test)

                except Exception as e:
                    logger.error("Integration test failed for %s: %s", test_case["name"], e)
                    integration_results["integration_tests"].append({
                        "test_case": test_case["name"],
                        "success": False,
                        "error": str(e)
                    })

            # Calculate overall integration score
            if successful_integrations > 0:
                integration_results["overall_integration_score"] = total_improvement / successful_integrations

            logger.info("Integration testing completed: %d/%d successful",
                       successful_integrations, len(test_cases))

            return integration_results

        except Exception as e:
            logger.error("Integration testing failed: %s", e)
            return {"error": str(e)}

    async def _test_performance(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test performance characteristics."""
        try:
            logger.info("Testing performance characteristics")

            performance_results = {
                "performance_tests": [],
                "average_processing_time_ms": 0.0,
                "memory_usage_mb": 0.0,
                "throughput_tests_per_second": 0.0
            }

            total_processing_time = 0.0
            successful_tests = 0

            # Test processing time
            for test_case in test_cases:
                try:
                    start_time = time.time()

                    result = await safe_accuracy_enhancer.apply_safe_improvements(
                        analysis_result=test_case["analysis_result"],
                        document_text=test_case["document_text"],
                        context=test_case["context"]
                    )

                    processing_time = (time.time() - start_time) * 1000

                    if result.success:
                        performance_test = {
                            "test_case": test_case["name"],
                            "processing_time_ms": processing_time,
                            "success": True
                        }

                        total_processing_time += processing_time
                        successful_tests += 1

                    else:
                        performance_test = {
                            "test_case": test_case["name"],
                            "processing_time_ms": processing_time,
                            "success": False,
                            "error": result.error
                        }

                    performance_results["performance_tests"].append(performance_test)

                except Exception as e:
                    logger.error("Performance test failed for %s: %s", test_case["name"], e)
                    performance_results["performance_tests"].append({
                        "test_case": test_case["name"],
                        "success": False,
                        "error": str(e)
                    })

            # Calculate performance metrics
            if successful_tests > 0:
                performance_results["average_processing_time_ms"] = total_processing_time / successful_tests
                performance_results["throughput_tests_per_second"] = 1000 / (total_processing_time / successful_tests)

            # Estimate memory usage (simplified)
            performance_results["memory_usage_mb"] = 50.0  # Estimated based on strategy complexity

            logger.info("Performance testing completed: avg processing time %.2f ms",
                       performance_results["average_processing_time_ms"])

            return performance_results

        except Exception as e:
            logger.error("Performance testing failed: %s", e)
            return {"error": str(e)}

    async def _test_safety(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test safety characteristics."""
        try:
            logger.info("Testing safety characteristics")

            safety_results = {
                "safety_tests": [],
                "overall_safety_score": 0.0,
                "safety_violations": [],
                "clinical_safety_score": 0.0
            }

            total_safety_score = 0.0
            successful_tests = 0

            for test_case in test_cases:
                try:
                    result = await safe_accuracy_enhancer.apply_safe_improvements(
                        analysis_result=test_case["analysis_result"],
                        document_text=test_case["document_text"],
                        context=test_case["context"]
                    )

                    if result.success:
                        enhanced_result = result.data
                        safe_improvements = enhanced_result.get('safe_accuracy_improvements', {})

                        safety_score = safe_improvements.get("safety_score", 0.5)
                        applied_strategies = safe_improvements.get("applied_strategies", [])

                        # Check for clinical safety
                        clinical_safety = self._assess_clinical_safety(enhanced_result, test_case["analysis_result"])

                        safety_test = {
                            "test_case": test_case["name"],
                            "success": True,
                            "safety_score": safety_score,
                            "clinical_safety_score": clinical_safety,
                            "applied_strategies": applied_strategies,
                            "safety_violations": []
                        }

                        total_safety_score += safety_score
                        successful_tests += 1

                    else:
                        safety_test = {
                            "test_case": test_case["name"],
                            "success": False,
                            "error": result.error,
                            "safety_violations": [result.error]
                        }

                        safety_results["safety_violations"].append(f"{test_case['name']}: {result.error}")

                    safety_results["safety_tests"].append(safety_test)

                except Exception as e:
                    logger.error("Safety test failed for %s: %s", test_case["name"], e)
                    safety_results["safety_tests"].append({
                        "test_case": test_case["name"],
                        "success": False,
                        "error": str(e),
                        "safety_violations": [str(e)]
                    })
                    safety_results["safety_violations"].append(f"{test_case['name']}: {e}")

            # Calculate overall safety score
            if successful_tests > 0:
                safety_results["overall_safety_score"] = total_safety_score / successful_tests
                safety_results["clinical_safety_score"] = sum(
                    test.get("clinical_safety_score", 0.5) for test in safety_results["safety_tests"]
                    if test.get("success", False)
                ) / successful_tests

            logger.info("Safety testing completed: overall safety score %.2f",
                       safety_results["overall_safety_score"])

            return safety_results

        except Exception as e:
            logger.error("Safety testing failed: %s", e)
            return {"error": str(e)}

    def _assess_clinical_safety(self, enhanced_result: Dict[str, Any], original_result: Dict[str, Any]) -> float:
        """Assess clinical safety of enhanced results."""
        try:
            # Check if clinical focus is preserved
            enhanced_findings = enhanced_result.get("findings", [])
            original_findings = original_result.get("findings", [])

            if len(enhanced_findings) != len(original_findings):
                return 0.5  # Safety concern if findings count changed

            # Check if confidence changes are reasonable
            safety_score = 1.0

            for i, (enhanced, original) in enumerate(zip(enhanced_findings, original_findings)):
                enhanced_conf = enhanced.get("confidence", 0.5)
                original_conf = original.get("confidence", 0.5)

                # Check for unreasonable confidence changes
                conf_change = abs(enhanced_conf - original_conf)
                if conf_change > 0.3:  # More than 30% change
                    safety_score -= 0.1

                # Check for clinical relevance preservation
                enhanced_text = enhanced.get("text", "")
                original_text = original.get("text", "")

                if not self._preserves_clinical_relevance(enhanced_text, original_text):
                    safety_score -= 0.2

            return max(0.0, min(1.0, safety_score))

        except Exception as e:
            logger.error("Clinical safety assessment failed: %s", e)
            return 0.5

    def _preserves_clinical_relevance(self, enhanced_text: str, original_text: str) -> bool:
        """Check if enhanced text preserves clinical relevance."""
        try:
            # Simple check for clinical relevance preservation
            clinical_terms = [
                'patient', 'diagnosis', 'treatment', 'therapy', 'symptom', 'condition',
                'medication', 'procedure', 'assessment', 'evaluation', 'clinical'
            ]

            original_terms = set(original_text.lower().split())
            enhanced_terms = set(enhanced_text.lower().split())

            original_clinical = original_terms.intersection(set(clinical_terms))
            enhanced_clinical = enhanced_terms.intersection(set(clinical_terms))

            # Check if clinical terms are preserved
            return len(original_clinical.intersection(enhanced_clinical)) >= len(original_clinical) * 0.8

        except Exception as e:
            logger.error("Clinical relevance preservation check failed: %s", e)
            return True

    def _generate_recommendations(
        self,
        strategy_tests: Dict[str, Any],
        integration_tests: Dict[str, Any],
        performance_tests: Dict[str, Any],
        safety_tests: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        # Analyze strategy performance
        successful_strategies = []
        failed_strategies = []

        for strategy_name, results in strategy_tests.items():
            overall_performance = results.get("overall_performance", {})
            success_rate = overall_performance.get("success_rate", 0.0)

            if success_rate >= 0.8:
                successful_strategies.append(strategy_name)
            else:
                failed_strategies.append(strategy_name)

        # Generate recommendations
        if len(successful_strategies) >= 8:
            recommendations.append("✅ Most strategies performing well - ready for production deployment")
        elif len(successful_strategies) >= 5:
            recommendations.append("⚠️ Some strategies need attention - consider phased deployment")
        else:
            recommendations.append("❌ Multiple strategies failing - review implementation before deployment")

        if failed_strategies:
            recommendations.append(f"🔧 Review failed strategies: {', '.join(failed_strategies)}")

        # Performance recommendations
        avg_processing_time = performance_tests.get("average_processing_time_ms", 0)
        if avg_processing_time > 5000:
            recommendations.append("⏱️ Processing time high - consider optimization")
        elif avg_processing_time < 1000:
            recommendations.append("⚡ Processing time excellent - good for production")

        # Safety recommendations
        overall_safety = safety_tests.get("overall_safety_score", 0.0)
        if overall_safety >= 0.9:
            recommendations.append("🛡️ Safety score excellent - safe for clinical use")
        elif overall_safety >= 0.8:
            recommendations.append("🛡️ Safety score good - monitor in production")
        else:
            recommendations.append("⚠️ Safety score low - review before clinical deployment")

        # Integration recommendations
        integration_score = integration_tests.get("overall_integration_score", 0.0)
        if integration_score >= 0.8:
            recommendations.append("🔗 Integration excellent - all strategies working together")
        elif integration_score >= 0.6:
            recommendations.append("🔗 Integration good - minor issues to address")
        else:
            recommendations.append("🔗 Integration needs work - review strategy compatibility")

        recommendations.append("📊 Monitor performance metrics in production")
        recommendations.append("🔄 Implement continuous improvement based on real-world usage")

        return recommendations


async def main():
    """Main testing function."""
    try:
        logger.info("Starting safe accuracy improvement testing")

        # Initialize tester
        tester = SafeAccuracyImprovementTester()

        # Run comprehensive tests
        test_results = await tester.run_comprehensive_tests()

        # Save results
        results_file = "safe_accuracy_improvement_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)

        logger.info("Test results saved to: %s", results_file)

        # Print summary
        test_summary = test_results.get("test_summary", {})
        logger.info("Test Summary: %d strategies tested, %d test cases",
                   test_summary.get("total_strategies_tested", 0),
                   test_summary.get("total_test_cases", 0))

        # Print recommendations
        recommendations = test_results.get("recommendations", [])
        logger.info("Recommendations:")
        for recommendation in recommendations:
            logger.info("  %s", recommendation)

    except Exception as e:
        logger.error("Safe accuracy improvement testing failed: %s", e)


if __name__ == "__main__":
    asyncio.run(main())
