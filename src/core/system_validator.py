import asyncio
import importlib
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import requests
from requests.exceptions import HTTPError

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
    details: dict[str, Any]
    duration_ms: float
    timestamp: datetime


class SystemValidator:
    """Comprehensive system validation for all components."""

    def __init__(self):
        """Initialize the system validator."""
        self.validation_results: list[ValidationResult] = []
        logger.info("System validator initialized")

    async def run_full_validation(self) -> list[ValidationResult]:
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
            if isinstance(result, BaseException):
                all_results.append(
                    ValidationResult(
                        component="system_validator",
                        test_name="validation_execution",
                        status=ValidationStatus.FAIL,
                        message=f"Validation failed: {result!s}",
                        details={"exception": str(result)},
                        duration_ms=0,
                        timestamp=datetime.now(),
                    )
                )
            elif isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, ValidationResult):
                all_results.append(result)
            else:
                # Handle unexpected types
                all_results.append(
                    ValidationResult(
                        component="system_validator",
                        test_name="validation_execution",
                        status=ValidationStatus.FAIL,
                        message=f"Unexpected result type: {type(result)}",
                        details={"result": str(result)},
                        duration_ms=0,
                        timestamp=datetime.now(),
                    )
                )

        self.validation_results = all_results

        total_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info("System validation completed in %sms", total_time)

        return all_results

    async def _validate_core_services(self) -> list[ValidationResult]:
        """Validate core service initialization and functionality."""
        results = []

        # Test core service imports
        services_to_test = [
            ("pdf_export_service", "src.core.pdf_export_service"),
            ("performance_monitor", "src.core.performance_monitor"),
            ("enhanced_error_handler", "src.core.enhanced_error_handler"),
        ]

        for service_name, module_path in services_to_test:
            start_time = datetime.now()
            try:
                import importlib

                module = importlib.import_module(module_path)
                assert module is not None

                duration = (datetime.now() - start_time).total_seconds() * 1000
                results.append(
                    ValidationResult(
                        component="core_services",
                        test_name=f"import_{service_name}",
                        status=ValidationStatus.PASS,
                        message=f"{service_name} imported successfully",
                        details={"module": module_path},
                        duration_ms=duration,
                        timestamp=datetime.now(),
                    )
                )

            except (FileNotFoundError, PermissionError, OSError) as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                results.append(
                    ValidationResult(
                        component="core_services",
                        test_name=f"import_{service_name}",
                        status=ValidationStatus.FAIL,
                        message=f"Failed to import {service_name}: {e!s}",
                        details={"error": str(e), "module": module_path},
                        duration_ms=duration,
                        timestamp=datetime.now(),
                    )
                )

        return results

    async def _validate_api_endpoints(self) -> list[ValidationResult]:
        """Validate API endpoint availability."""
        results = []

        # Test API imports
        start_time = datetime.now()
        try:
            from src.api.main import app

            assert app is not None

            duration = (datetime.now() - start_time).total_seconds() * 1000
            results.append(
                ValidationResult(
                    component="api_endpoints",
                    test_name="main_app_import",
                    status=ValidationStatus.PASS,
                    message="FastAPI application imported successfully",
                    details={},
                    duration_ms=duration,
                    timestamp=datetime.now(),
                )
            )

        except (
            requests.RequestException,
            ConnectionError,
            TimeoutError,
            HTTPError,
        ) as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            results.append(
                ValidationResult(
                    component="api_endpoints",
                    test_name="main_app_import",
                    status=ValidationStatus.FAIL,
                    message=f"Failed to import FastAPI app: {e!s}",
                    details={"error": str(e)},
                    duration_ms=duration,
                    timestamp=datetime.now(),
                )
            )

        return results

    async def _validate_new_features(self) -> list[ValidationResult]:
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
                module = importlib.import_module(module_path)
                assert module is not None

                duration = (datetime.now() - start_time).total_seconds() * 1000
                results.append(
                    ValidationResult(
                        component="new_features",
                        test_name=f"import_{feature_name}",
                        status=ValidationStatus.PASS,
                        message=f"{feature_name} imported successfully",
                        details={"module": module_path},
                        duration_ms=duration,
                        timestamp=datetime.now(),
                    )
                )

            except (FileNotFoundError, PermissionError, OSError) as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                results.append(
                    ValidationResult(
                        component="new_features",
                        test_name=f"import_{feature_name}",
                        status=ValidationStatus.FAIL,
                        message=f"Failed to import {feature_name}: {e!s}",
                        details={"error": str(e), "module": module_path},
                        duration_ms=duration,
                        timestamp=datetime.now(),
                    )
                )

        return results

    def get_overall_status(self, results: list[ValidationResult]) -> ValidationStatus:
        """Get overall system validation status."""
        if not results:
            return ValidationStatus.SKIP

        # Count status types
        status_counts = {
            ValidationStatus.PASS: 0,
            ValidationStatus.WARN: 0,
            ValidationStatus.FAIL: 0,
            ValidationStatus.SKIP: 0,
        }

        for result in results:
            status_counts[result.status] += 1

        # Determine overall status
        if status_counts[ValidationStatus.FAIL] > 0:
            return ValidationStatus.FAIL
        if status_counts[ValidationStatus.WARN] > 0:
            return ValidationStatus.WARN
        if status_counts[ValidationStatus.PASS] > 0:
            return ValidationStatus.PASS
        return ValidationStatus.SKIP


# Global system validator instance
# Global system validator instance
# Global system validator instance
system_validator = SystemValidator()
