"""
System Validator - Clean Version

Comprehensive system validation to ensure all components are properly integrated.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation status levels."""
    PASS = "pass"
    WARN = "warning"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    component: str
    test_name: str
    status: ValidationStatus
    message: str
    details: Dict[str, Any]
    duration_ms: float
    timestamp: datetime


class SystemValidator:
    """Comprehensive system validation for all components."""
    
    def __init__(self):
        """Initialize the system validator."""
        self.validation_results: List[ValidationResult] = []
        logger.info("System validator initialized")
    
    async def run_full_validation(self) -> List[ValidationResult]:
        """Run comprehensive system validation."""
        logger.info("Starting comprehensive system validation")
        start_time = datetime.now()
        
        validation_tasks = [
            self._validate_core_services(),
            self._validate_api_endpoints(),
            self._validate_new_features(),
        ]
        
        # Run all validations concurrently
        results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        # Flatten results and handle exceptions
        all_results = []
        for result in results:
            if isinstance(result, Exception):
                all_results.append(ValidationResult(
                    component="system_validator",
                    test_name="validation_execution",
                    status=ValidationStatus.FAIL,
                    message=f"Validation failed: {str(result)}",
                    details={"exception": str(result)},
                    duration_ms=0,
                    timestamp=datetime.now()
                ))
            elif isinstance(result, list):
                all_results.extend(result)
            else:
                all_results.append(result)
        
        self.validation_results = all_results
        
        total_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"System validation completed in {total_time:.1f}ms")
        
        return all_results
    
    async def _validate_core_services(self) -> List[ValidationResult]:
        """Validate core service initialization and functionality."""
        results = []
        
        # Test core service imports
        services_to_test = [
            ("pdf_export_service", "src.core.pdf_export_service"),
            ("performance_monitor", "src.core.performance_monitor"),
            ("enhanced_error_handler", "src.core.enhanced_error_handler"),
            ("enterprise_copilot_service", "src.core.enterprise_copilot_service"),
        ]
        
        for service_name, module_path in services_to_test:
            start_time = datetime.now()
            try:
                import importlib
                module = importlib.import_module(module_path)
                assert module is not None
                
                duration = (datetime.now() - start_time).total_seconds() * 1000
                results.append(ValidationResult(
                    component="core_services",
                    test_name=f"import_{service_name}",
                    status=ValidationStatus.PASS,
                    message=f"{service_name} imported successfully",
                    details={"module": module_path},
                    duration_ms=duration,
                    timestamp=datetime.now()
                ))
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                results.append(ValidationResult(
                    component="core_services",
                    test_name=f"import_{service_name}",
                    status=ValidationStatus.FAIL,
                    message=f"Failed to import {service_name}: {str(e)}",
                    details={"error": str(e), "module": module_path},
                    duration_ms=duration,
                    timestamp=datetime.now()
                ))
        
        return results
    
    async def _validate_api_endpoints(self) -> List[ValidationResult]:
        """Validate API endpoint availability."""
        results = []
        
        # Test API imports
        start_time = datetime.now()
        try:
            from src.api.main import app
            assert app is not None
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            results.append(ValidationResult(
                component="api_endpoints",
                test_name="main_app_import",
                status=ValidationStatus.PASS,
                message="FastAPI application imported successfully",
                details={},
                duration_ms=duration,
                timestamp=datetime.now()
            ))
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            results.append(ValidationResult(
                component="api_endpoints",
                test_name="main_app_import",
                status=ValidationStatus.FAIL,
                message=f"Failed to import FastAPI app: {str(e)}",
                details={"error": str(e)},
                duration_ms=duration,
                timestamp=datetime.now()
            ))
        
        return results
    
    async def _validate_new_features(self) -> List[ValidationResult]:
        """Validate new features functionality."""
        results = []
        
        # Test new feature imports
        features_to_test = [
            ("plugin_system", "src.core.plugin_system"),
            ("multi_agent_orchestrator", "src.core.multi_agent_orchestrator"),
            ("workflow_automation", "src.core.workflow_automation"),
        ]
        
        for feature_name, module_path in features_to_test:
            start_time = datetime.now()
            try:
                import importlib
                module = importlib.import_module(module_path)
                assert module is not None
                
                duration = (datetime.now() - start_time).total_seconds() * 1000
                results.append(ValidationResult(
                    component="new_features",
                    test_name=f"import_{feature_name}",
                    status=ValidationStatus.PASS,
                    message=f"{feature_name} imported successfully",
                    details={"module": module_path},
                    duration_ms=duration,
                    timestamp=datetime.now()
                ))
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                results.append(ValidationResult(
                    component="new_features",
                    test_name=f"import_{feature_name}",
                    status=ValidationStatus.FAIL,
                    message=f"Failed to import {feature_name}: {str(e)}",
                    details={"error": str(e), "module": module_path},
                    duration_ms=duration,
                    timestamp=datetime.now()
                ))
        
        return results
    
    def get_overall_status(self, results: List[ValidationResult]) -> ValidationStatus:
        """Get overall system validation status."""
        if not results:
            return ValidationStatus.SKIP
        
        # Count status types
        status_counts = {
            ValidationStatus.PASS: 0,
            ValidationStatus.WARN: 0,
            ValidationStatus.FAIL: 0,
            ValidationStatus.SKIP: 0
        }
        
        for result in results:
            status_counts[result.status] += 1
        
        # Determine overall status
        if status_counts[ValidationStatus.FAIL] > 0:
            return ValidationStatus.FAIL
        elif status_counts[ValidationStatus.WARN] > 0:
            return ValidationStatus.WARN
        elif status_counts[ValidationStatus.PASS] > 0:
            return ValidationStatus.PASS
        else:
            return ValidationStatus.SKIP


# Global system validator instance
system_validator = SystemValidator()