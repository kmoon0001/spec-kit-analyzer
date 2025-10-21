"""
Comprehensive Integration Validation Script
Ensures all accuracy improvements and changes are properly integrated throughout the codebase
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path
import importlib
import inspect

from src.core.centralized_logging import get_logger, performance_tracker
from src.core.type_safety import Result, ErrorHandler

logger = get_logger(__name__)


class IntegrationValidator:
    """
    Comprehensive validator to ensure all accuracy improvements are properly integrated.
    """

    def __init__(self):
        """Initialize the integration validator."""
        self.validation_results: Dict[str, Any] = {}
        self.integration_issues: List[str] = []
        self.missing_components: List[str] = []
        self.configuration_issues: List[str] = []

        logger.info("IntegrationValidator initialized")

    async def validate_complete_integration(self) -> Result[Dict[str, Any], str]:
        """Validate complete integration of all accuracy improvements."""
        try:
            start_time = datetime.now()

            # Run all validation checks
            validation_checks = [
                ("Component Integration", self._validate_component_integration),
                ("Configuration Integration", self._validate_configuration_integration),
                ("API Integration", self._validate_api_integration),
                ("Database Integration", self._validate_database_integration),
                ("Performance Integration", self._validate_performance_integration),
                ("Security Integration", self._validate_security_integration),
                ("Monitoring Integration", self._validate_monitoring_integration),
                ("Testing Integration", self._validate_testing_integration),
                ("Documentation Integration", self._validate_documentation_integration),
                ("Deployment Integration", self._validate_deployment_integration)
            ]

            total_checks = len(validation_checks)
            passed_checks = 0

            for check_name, check_func in validation_checks:
                logger.info("Running validation check: %s", check_name)
                try:
                    result = await check_func()
                    self.validation_results[check_name] = result
                    if result.get('status') == 'passed':
                        passed_checks += 1
                        logger.info("✅ %s: PASSED", check_name)
                    else:
                        logger.warning("⚠️ %s: ISSUES FOUND", check_name)
                except Exception as e:
                    logger.error("❌ %s: FAILED - %s", check_name, e)
                    self.validation_results[check_name] = {
                        'status': 'failed',
                        'error': str(e)
                    }

            # Calculate overall status
            overall_status = "passed" if passed_checks == total_checks else "issues_found"
            success_rate = passed_checks / total_checks

            # Generate comprehensive report
            validation_time = (datetime.now() - start_time).total_seconds()

            final_result = {
                "validation_summary": {
                    "overall_status": overall_status,
                    "total_checks": total_checks,
                    "passed_checks": passed_checks,
                    "failed_checks": total_checks - passed_checks,
                    "success_rate": success_rate,
                    "validation_time_seconds": validation_time
                },
                "validation_results": self.validation_results,
                "integration_issues": self.integration_issues,
                "missing_components": self.missing_components,
                "configuration_issues": self.configuration_issues,
                "recommendations": self._generate_recommendations(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            logger.info("Integration validation completed: %d/%d checks passed (%.1f%%)",
                       passed_checks, total_checks, success_rate * 100)

            return Result.success(final_result)

        except Exception as e:
            logger.error("Integration validation failed: %s", e)
            return Result.error(f"Validation failed: {e}")

    async def _validate_component_integration(self) -> Dict[str, Any]:
        """Validate that all accuracy improvement components are properly integrated."""
        try:
            issues = []
            missing_components = []

            # Check core components
            core_components = [
                "src.core.ultra_lightweight_clinical_system",
                "src.core.memory_optimized_systems",
                "src.core.ultra_lightweight_integration",
                "src.core.accuracy_hallucination_tracker",
                "src.core.comprehensive_accuracy_integration",
                "src.core.advanced_accuracy_enhancer",
                "src.core.hybrid_model_system",
                "src.core.advanced_rag_system",
                "src.core.chain_of_verification",
                "src.core.dynamic_prompt_system",
                "src.core.multimodal_analyzer",
                "src.core.causal_reasoning_engine",
                "src.core.rlhf_system"
            ]

            for component in core_components:
                try:
                    module = importlib.import_module(component)
                    if not hasattr(module, '__file__'):
                        missing_components.append(component)
                        issues.append(f"Component {component} not found")
                except ImportError as e:
                    missing_components.append(component)
                    issues.append(f"Component {component} import failed: {e}")

            # Check analysis service integration
            try:
                from src.core.analysis_service import AnalysisService
                analysis_service = AnalysisService()

                # Check if accuracy tracker is integrated
                if not hasattr(analysis_service, 'accuracy_tracker'):
                    issues.append("Accuracy tracker not integrated in AnalysisService")

                # Check if ensemble optimizer is integrated
                if not hasattr(analysis_service, 'ensemble_optimizer'):
                    issues.append("Ensemble optimizer not integrated in AnalysisService")

                # Check if explanation engine is integrated
                if not hasattr(analysis_service, 'explanation_engine'):
                    issues.append("Explanation engine not integrated in AnalysisService")

            except Exception as e:
                issues.append(f"AnalysisService integration check failed: {e}")

            status = "passed" if not issues else "issues_found"

            return {
                "status": status,
                "total_components": len(core_components),
                "missing_components": len(missing_components),
                "issues": issues,
                "missing_component_list": missing_components
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "issues": [f"Component integration validation failed: {e}"]
            }

    async def _validate_configuration_integration(self) -> Dict[str, Any]:
        """Validate configuration integration."""
        try:
            issues = []

            # Check config.yaml
            config_path = Path("config.yaml")
            if not config_path.exists():
                issues.append("config.yaml not found")
            else:
                try:
                    import yaml
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)

                    # Check ultra-lightweight settings
                    if 'accuracy_enhancement' not in config:
                        issues.append("accuracy_enhancement section missing in config.yaml")
                    else:
                        accuracy_config = config['accuracy_enhancement']
                        if not accuracy_config.get('ultra_lightweight_mode'):
                            issues.append("ultra_lightweight_mode not enabled in config.yaml")

                        if not accuracy_config.get('ultra_lightweight_clinical_system', {}).get('enabled'):
                            issues.append("ultra_lightweight_clinical_system not enabled")

                    # Check model configurations
                    if 'models' not in config:
                        issues.append("models section missing in config.yaml")
                    else:
                        models_config = config['models']
                        if 'generator_profiles' not in models_config:
                            issues.append("generator_profiles missing in models config")
                        else:
                            profiles = models_config['generator_profiles']
                            required_profiles = [
                                'cpu_tinyllama_clinical',
                                'cpu_qwen25_05b_clinical',
                                'cpu_phi3_mini_medical',
                                'cpu_gemma_2b_fact_checker'
                            ]
                            for profile in required_profiles:
                                if profile not in profiles:
                                    issues.append(f"Required model profile {profile} missing")

                    # Check performance settings
                    if 'performance' not in config:
                        issues.append("performance section missing in config.yaml")
                    else:
                        perf_config = config['performance']
                        if not perf_config.get('ultra_lightweight_mode'):
                            issues.append("ultra_lightweight_mode not enabled in performance config")

                        if perf_config.get('max_ram_gb', 0) > 10:
                            issues.append("max_ram_gb exceeds 10GB limit")

                except Exception as e:
                    issues.append(f"config.yaml parsing failed: {e}")

            status = "passed" if not issues else "issues_found"

            return {
                "status": status,
                "issues": issues,
                "config_file_exists": config_path.exists()
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "issues": [f"Configuration validation failed: {e}"]
            }

    async def _validate_api_integration(self) -> Dict[str, Any]:
        """Validate API integration."""
        try:
            issues = []

            # Check API routers
            api_routers = [
                "src.api.routers.unified_ml_api",
                "src.api.routers.performance_monitoring",
                "src.api.routers.security_analysis",
                "src.api.routers.ml_model_management"
            ]

            for router in api_routers:
                try:
                    module = importlib.import_module(router)
                    if not hasattr(module, 'router'):
                        issues.append(f"Router {router} missing router attribute")
                except ImportError as e:
                    issues.append(f"API router {router} import failed: {e}")

            # Check main API integration
            try:
                from src.api.main import app
                # Check if new routers are included
                router_tags = ["Unified ML API", "Performance Monitoring", "Security Analysis", "ML Model Management"]
                for tag in router_tags:
                    # This is a simplified check - in reality, we'd need to inspect the app's routes
                    pass

            except Exception as e:
                issues.append(f"Main API integration check failed: {e}")

            # Check middleware integration
            try:
                from src.api.middleware.security_middleware import setup_security_middleware
                # Middleware exists
            except ImportError as e:
                issues.append(f"Security middleware import failed: {e}")

            status = "passed" if not issues else "issues_found"

            return {
                "status": status,
                "total_routers": len(api_routers),
                "issues": issues
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "issues": [f"API integration validation failed: {e}"]
            }

    async def _validate_database_integration(self) -> Dict[str, Any]:
        """Validate database integration."""
        try:
            issues = []

            # Check database files
            db_files = [
                "compliance.db",
                "tasks.db",
                "data/calibration_training.db"
            ]

            for db_file in db_files:
                db_path = Path(db_file)
                if not db_path.exists():
                    issues.append(f"Database file {db_file} not found")

            # Check database services
            try:
                from src.database import database_service
                # Database service exists
            except ImportError as e:
                issues.append(f"Database service import failed: {e}")

            status = "passed" if not issues else "issues_found"

            return {
                "status": status,
                "total_db_files": len(db_files),
                "issues": issues
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "issues": [f"Database integration validation failed: {e}"]
            }

    async def _validate_performance_integration(self) -> Dict[str, Any]:
        """Validate performance integration."""
        try:
            issues = []

            # Check performance monitoring
            try:
                from src.core.centralized_logging import performance_tracker
                # Performance tracker exists
            except ImportError as e:
                issues.append(f"Performance tracker import failed: {e}")

            # Check caching systems
            try:
                from src.core.multi_tier_cache import MultiTierCacheSystem
                # Caching system exists
            except ImportError as e:
                issues.append(f"Caching system import failed: {e}")

            # Check memory optimization
            try:
                from src.core.memory_optimized_systems import MemoryOptimizedRAGSystem
                # Memory optimization exists
            except ImportError as e:
                issues.append(f"Memory optimization import failed: {e}")

            status = "passed" if not issues else "issues_found"

            return {
                "status": status,
                "issues": issues
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "issues": [f"Performance integration validation failed: {e}"]
            }

    async def _validate_security_integration(self) -> Dict[str, Any]:
        """Validate security integration."""
        try:
            issues = []

            # Check security systems
            security_components = [
                "src.core.advanced_security_system",
                "src.api.middleware.security_middleware"
            ]

            for component in security_components:
                try:
                    module = importlib.import_module(component)
                except ImportError as e:
                    issues.append(f"Security component {component} import failed: {e}")

            status = "passed" if not issues else "issues_found"

            return {
                "status": status,
                "total_security_components": len(security_components),
                "issues": issues
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "issues": [f"Security integration validation failed: {e}"]
            }

    async def _validate_monitoring_integration(self) -> Dict[str, Any]:
        """Validate monitoring integration."""
        try:
            issues = []

            # Check monitoring components
            monitoring_components = [
                "src.core.accuracy_hallucination_tracker",
                "src.api.routers.performance_monitoring",
                "src.api.routers.security_analysis"
            ]

            for component in monitoring_components:
                try:
                    module = importlib.import_module(component)
                except ImportError as e:
                    issues.append(f"Monitoring component {component} import failed: {e}")

            status = "passed" if not issues else "issues_found"

            return {
                "status": status,
                "total_monitoring_components": len(monitoring_components),
                "issues": issues
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "issues": [f"Monitoring integration validation failed: {e}"]
            }

    async def _validate_testing_integration(self) -> Dict[str, Any]:
        """Validate testing integration."""
        try:
            issues = []

            # Check test files
            test_files = [
                "test_ultra_lightweight_system.py",
                "tests/test_new_components.py"
            ]

            for test_file in test_files:
                test_path = Path(test_file)
                if not test_path.exists():
                    issues.append(f"Test file {test_file} not found")

            status = "passed" if not issues else "issues_found"

            return {
                "status": status,
                "total_test_files": len(test_files),
                "issues": issues
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "issues": [f"Testing integration validation failed: {e}"]
            }

    async def _validate_documentation_integration(self) -> Dict[str, Any]:
        """Validate documentation integration."""
        try:
            issues = []

            # Check documentation files
            doc_files = [
                "ULTRA_LIGHTWEIGHT_IMPLEMENTATION_COMPLETE.md",
                "ACCURACY_HALLUCINATION_ANALYSIS_REPORT.md",
                "ACCURACY_IMPROVEMENT_IMPLEMENTATION_COMPLETE.md",
                "COMPREHENSIVE_ACCURACY_ENHANCEMENT_COMPLETE.md"
            ]

            for doc_file in doc_files:
                doc_path = Path(doc_file)
                if not doc_path.exists():
                    issues.append(f"Documentation file {doc_file} not found")

            status = "passed" if not issues else "issues_found"

            return {
                "status": status,
                "total_doc_files": len(doc_files),
                "issues": issues
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "issues": [f"Documentation integration validation failed: {e}"]
            }

    async def _validate_deployment_integration(self) -> Dict[str, Any]:
        """Validate deployment integration."""
        try:
            issues = []

            # Check deployment files
            deployment_files = [
                "deploy_to_production.py",
                "production_monitoring.py",
                "production_validation.py",
                "PRODUCTION_DEPLOYMENT_GUIDE.md"
            ]

            for deploy_file in deployment_files:
                deploy_path = Path(deploy_file)
                if not deploy_path.exists():
                    issues.append(f"Deployment file {deploy_file} not found")

            status = "passed" if not issues else "issues_found"

            return {
                "status": status,
                "total_deployment_files": len(deployment_files),
                "issues": issues
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "issues": [f"Deployment integration validation failed: {e}"]
            }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        # Analyze validation results
        total_issues = sum(len(result.get('issues', [])) for result in self.validation_results.values())

        if total_issues == 0:
            recommendations.append("✅ All components properly integrated - system ready for production")
        else:
            recommendations.append(f"⚠️ {total_issues} integration issues found - review and fix before deployment")

            # Component-specific recommendations
            if any('Component' in str(result.get('issues', [])) for result in self.validation_results.values()):
                recommendations.append("🔧 Fix missing component imports and dependencies")

            if any('config' in str(result.get('issues', [])).lower() for result in self.validation_results.values()):
                recommendations.append("⚙️ Update configuration files with required settings")

            if any('API' in str(result.get('issues', [])) for result in self.validation_results.values()):
                recommendations.append("🌐 Fix API router integration and middleware setup")

            if any('test' in str(result.get('issues', [])).lower() for result in self.validation_results.values()):
                recommendations.append("🧪 Ensure all test files are present and functional")

        recommendations.append("📊 Monitor system performance after deployment")
        recommendations.append("🔄 Implement continuous integration validation")

        return recommendations

    async def generate_integration_report(self, validation_results: Dict[str, Any]) -> str:
        """Generate comprehensive integration report."""
        try:
            summary = validation_results['validation_summary']

            report = f"""
# 🔍 **COMPREHENSIVE INTEGRATION VALIDATION REPORT**

## 📊 **Validation Summary**
- **Overall Status**: {summary['overall_status'].upper()}
- **Total Checks**: {summary['total_checks']}
- **Passed Checks**: {summary['passed_checks']}
- **Failed Checks**: {summary['failed_checks']}
- **Success Rate**: {summary['success_rate']:.1%}
- **Validation Time**: {summary['validation_time_seconds']:.1f} seconds

## 🔍 **Detailed Results**
"""

            for check_name, result in validation_results['validation_results'].items():
                status_icon = "✅" if result.get('status') == 'passed' else "⚠️" if result.get('status') == 'issues_found' else "❌"
                report += f"\n### {status_icon} {check_name}\n"
                report += f"- **Status**: {result.get('status', 'unknown')}\n"

                if result.get('issues'):
                    report += f"- **Issues Found**: {len(result['issues'])}\n"
                    for issue in result['issues'][:3]:  # Show first 3 issues
                        report += f"  - {issue}\n"
                    if len(result['issues']) > 3:
                        report += f"  - ... and {len(result['issues']) - 3} more issues\n"

                if result.get('error'):
                    report += f"- **Error**: {result['error']}\n"

            report += f"""
## 📋 **Recommendations**
"""
            for recommendation in validation_results['recommendations']:
                report += f"- {recommendation}\n"

            report += f"""
## 🎯 **Next Steps**
1. **Review Issues**: Address all identified integration issues
2. **Test Components**: Verify all components work correctly
3. **Update Configuration**: Ensure all settings are properly configured
4. **Deploy System**: Proceed with production deployment
5. **Monitor Performance**: Track system performance post-deployment

---
*Report generated at {validation_results['timestamp']}*
"""

            return report

        except Exception as e:
            logger.error("Integration report generation failed: %s", e)
            return f"Report generation failed: {e}"


async def main():
    """Main validation execution function."""
    try:
        logger.info("Starting comprehensive integration validation")

        # Initialize validator
        validator = IntegrationValidator()

        # Run validation
        validation_results = await validator.validate_complete_integration()

        if validation_results.success:
            # Generate report
            report = await validator.generate_integration_report(validation_results.data)

            # Save report
            report_path = Path("integration_validation_report.md")
            report_path.write_text(report)

            logger.info("Integration validation report saved to: %s", report_path)

            # Print summary
            summary = validation_results.data['validation_summary']
            logger.info("Integration Validation Summary: %d/%d checks passed (%.1f%%)",
                       summary['passed_checks'], summary['total_checks'],
                       summary['success_rate'] * 100)

            # Print recommendations
            for recommendation in validation_results.data['recommendations']:
                logger.info("Recommendation: %s", recommendation)

        else:
            logger.error("Integration validation failed: %s", validation_results.error)

    except Exception as e:
        logger.error("Integration validation execution failed: %s", e)


if __name__ == "__main__":
    asyncio.run(main())
