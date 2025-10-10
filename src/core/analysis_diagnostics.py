"""Analysis Diagnostics - Health checks and diagnostic utilities for analysis workflow.
import json

This module provides comprehensive diagnostic capabilities to verify system
health and identify common issues that prevent analysis from completing.
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import requests

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DiagnosticStatus(Enum):
    """Diagnostic check status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""

    component: str
    status: DiagnosticStatus
    message: str
    details: dict[str, Any]
    timestamp: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class AnalysisDiagnostics:
    """Comprehensive diagnostic system for analysis workflow.

    Provides health checks for all components involved in document analysis
    including API connectivity, file processing, AI models, and system resources.
    """

    def __init__(self):
        self.api_url = settings.paths.api_url
        self.timeout = 10  # seconds

    def run_full_diagnostic(self) -> dict[str, DiagnosticResult]:
        """Run comprehensive diagnostic checks.

        Returns:
            Dictionary of diagnostic results keyed by component name

        """
        logger.info("Starting comprehensive analysis workflow diagnostics")

        diagnostics = {}

        # Run all diagnostic checks
        checks = [
            self.check_api_connectivity,
            self.check_api_health,
            self.check_analysis_endpoints,
            self.check_system_resources,
            self.check_file_system_access,
            self.check_ai_model_status,
        ]

        for check in checks:
            try:
                result = check()
                diagnostics[result.component] = result
                logger.debug("Diagnostic check '%s': {result.status.value}", result.component)
            except (ValueError, TypeError, AttributeError) as e:
                logger.exception("Diagnostic check failed: %s", e)
                diagnostics[f"check_error_{check.__name__}"] = DiagnosticResult(
                    component=check.__name__,
                    status=DiagnosticStatus.ERROR,
                    message=f"Diagnostic check failed: {e!s}",
                    details={"error": str(e)},
                    timestamp=time.time())

        # Generate overall health summary
        overall_status = self._calculate_overall_status(diagnostics)
        logger.info("Diagnostic summary: %s", overall_status)

        return diagnostics

    def check_api_connectivity(self) -> DiagnosticResult:
        """Check basic API connectivity."""
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_url}/health", timeout=self.timeout)
            response_time = time.time() - start_time

            if response.status_code == 200:
                return DiagnosticResult(
                    component="api_connectivity",
                    status=DiagnosticStatus.HEALTHY,
                    message=f"API is accessible (response time: {response_time}s)",
                    details={
                        "url": f"{self.api_url}/health",
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "server_info": response.json() if response.content else {},
                    },
                    timestamp=time.time())
            return DiagnosticResult(
                component="api_connectivity",
                status=DiagnosticStatus.ERROR,
                message=f"API returned status {response.status_code}",
                details={
                    "url": f"{self.api_url}/health",
                    "status_code": response.status_code,
                    "response_time": response_time,
                },
                timestamp=time.time())

        except requests.exceptions.ConnectionError:
            return DiagnosticResult(
                component="api_connectivity",
                status=DiagnosticStatus.ERROR,
                message="Cannot connect to API server - is it running?",
                details={
                    "url": f"{self.api_url}/health",
                    "error": "Connection refused",
                    "suggestion": "Start the API server with: python scripts/run_api.py",
                },
                timestamp=time.time())
        except requests.exceptions.Timeout:
            return DiagnosticResult(
                component="api_connectivity",
                status=DiagnosticStatus.WARNING,
                message=f"API health check timed out after {self.timeout}s",
                details={
                    "url": f"{self.api_url}/health",
                    "timeout": self.timeout,
                    "suggestion": "API server may be overloaded or slow",
                },
                timestamp=time.time())
        except Exception as e:
            return DiagnosticResult(
                component="api_connectivity",
                status=DiagnosticStatus.ERROR,
                message=f"API connectivity check failed: {e!s}",
                details={"error": str(e)},
                timestamp=time.time())

    def check_api_health(self) -> DiagnosticResult:
        """Check detailed API health status."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=self.timeout)

            if response.status_code == 200:
                try:
                    health_data = response.json()
                except ValueError:
                    # Response is not JSON
                    return DiagnosticResult(
                        component="api_health",
                        status=DiagnosticStatus.ERROR,
                        message=f"API returned non-JSON response: {response.text[:100]}",
                        details={"response_text": response.text[:500]},
                        timestamp=time.time())

                # Handle the actual API response format
                api_status = health_data.get("status", "unknown")
                database_status = health_data.get("database", "unknown")

                if api_status == "ok" and database_status == "connected":
                    status = DiagnosticStatus.HEALTHY
                    message = "API and database are healthy"
                elif api_status == "ok":
                    status = DiagnosticStatus.WARNING
                    message = "API is healthy but database status unclear"
                else:
                    status = DiagnosticStatus.ERROR
                    message = f"API health check failed: {api_status}"

                return DiagnosticResult(
                    component="api_health",
                    status=status,
                    message=message,
                    details={
                        "health_data": health_data,
                        "api_status": api_status,
                        "database_status": database_status,
                    },
                    timestamp=time.time())
            return DiagnosticResult(
                component="api_health",
                status=DiagnosticStatus.ERROR,
                message=f"API health endpoint returned {response.status_code}",
                details={"status_code": response.status_code},
                timestamp=time.time())

        except Exception as e:
            return DiagnosticResult(
                component="api_health",
                status=DiagnosticStatus.ERROR,
                message=f"API health check failed: {e!s}",
                details={"error": str(e)},
                timestamp=time.time())

    def check_analysis_endpoints(self) -> DiagnosticResult:
        """Check analysis-specific API endpoints."""
        endpoints_to_check = [
            ("/analysis/analyze", "POST"),
            ("/analysis/status/{task_id}", "GET"),
        ]

        endpoint_results = {}
        overall_status = DiagnosticStatus.HEALTHY

        for endpoint, method in endpoints_to_check:
            try:
                # For GET endpoints, we can test directly
                if method == "GET":
                    # Test with a dummy task ID to see if endpoint exists
                    test_url = f"{self.api_url}{endpoint.replace('{task_id}', 'test')}"
                    response = requests.get(test_url, timeout=self.timeout)

                    # We expect 404 for non-existent task or 401 for auth required, which means endpoint exists
                    if response.status_code in [200, 401, 404]:
                        endpoint_results[endpoint] = "accessible"
                    else:
                        endpoint_results[endpoint] = f"unexpected_status_{response.status_code}"
                        overall_status = DiagnosticStatus.WARNING
                else:
                    # For POST endpoints, we can only check if they're defined
                    # by looking at the response to an invalid request
                    test_url = f"{self.api_url}{endpoint}"
                    response = requests.post(test_url, json={}, timeout=self.timeout)

                    # We expect 422 (validation error), 400, or 401 (auth required), not 404 (not found)
                    if response.status_code in [400, 401, 422]:
                        endpoint_results[endpoint] = "accessible"
                    elif response.status_code == 404:
                        endpoint_results[endpoint] = "not_found"
                        overall_status = DiagnosticStatus.ERROR
                    else:
                        endpoint_results[endpoint] = f"status_{response.status_code}"
                        overall_status = DiagnosticStatus.WARNING

            except Exception as e:
                endpoint_results[endpoint] = f"error: {e!s}"
                overall_status = DiagnosticStatus.ERROR

        if overall_status == DiagnosticStatus.HEALTHY:
            message = "All analysis endpoints are accessible"
        elif overall_status == DiagnosticStatus.WARNING:
            message = "Some analysis endpoints have issues"
        else:
            message = "Critical analysis endpoints are not accessible"

        return DiagnosticResult(
            component="analysis_endpoints",
            status=overall_status,
            message=message,
            details={"endpoints": endpoint_results},
            timestamp=time.time())

    def check_system_resources(self) -> DiagnosticResult:
        """Check system resource availability."""
        try:
            import psutil  # type: ignore[import-untyped]

            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Determine status based on resource usage
            status = DiagnosticStatus.HEALTHY
            issues = []

            if cpu_percent > 90:
                status = DiagnosticStatus.WARNING
                issues.append(f"High CPU usage: {cpu_percent}%")

            if memory.percent > 90:
                status = DiagnosticStatus.WARNING
                issues.append(f"High memory usage: {memory.percent}%")

            if disk.percent > 95:
                status = DiagnosticStatus.ERROR
                issues.append(f"Very low disk space: {disk.percent}% used")
            elif disk.percent > 85:
                status = DiagnosticStatus.WARNING
                issues.append(f"Low disk space: {disk.percent}% used")

            message = "System resources are adequate" if not issues else "; ".join(issues)

            return DiagnosticResult(
                component="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3),
                },
                timestamp=time.time())

        except ImportError:
            return DiagnosticResult(
                component="system_resources",
                status=DiagnosticStatus.WARNING,
                message="Cannot check system resources (psutil not installed)",
                details={"suggestion": "Install psutil for resource monitoring: pip install psutil"},
                timestamp=time.time())
        except Exception as e:
            return DiagnosticResult(
                component="system_resources",
                status=DiagnosticStatus.ERROR,
                message=f"System resource check failed: {e!s}",
                details={"error": str(e)},
                timestamp=time.time())

    def check_file_system_access(self) -> DiagnosticResult:
        """Check file system access for document processing."""
        try:
            # Check if we can create temporary files
            temp_dir = Path.cwd() / "temp"
            temp_dir.mkdir(exist_ok=True)

            test_file = temp_dir / "diagnostic_test.txt"
            test_content = "Diagnostic test file"

            # Test write access
            test_file.write_text(test_content)

            # Test read access
            read_content = test_file.read_text()

            # Clean up
            test_file.unlink()

            if read_content == test_content:
                return DiagnosticResult(
                    component="file_system_access",
                    status=DiagnosticStatus.HEALTHY,
                    message="File system access is working correctly",
                    details={
                        "temp_directory": str(temp_dir),
                        "write_access": True,
                        "read_access": True,
                    },
                    timestamp=time.time())
            return DiagnosticResult(
                component="file_system_access",
                status=DiagnosticStatus.ERROR,
                message="File system read/write test failed",
                details={
                    "temp_directory": str(temp_dir),
                    "expected_content": test_content,
                    "actual_content": read_content,
                },
                timestamp=time.time())

        except PermissionError:
            return DiagnosticResult(
                component="file_system_access",
                status=DiagnosticStatus.ERROR,
                message="Insufficient file system permissions",
                details={
                    "error": "Permission denied",
                    "suggestion": "Check file system permissions for the application directory",
                },
                timestamp=time.time())
        except (OSError, FileNotFoundError) as e:
            return DiagnosticResult(
                component="file_system_access",
                status=DiagnosticStatus.ERROR,
                message=f"File system access check failed: {e!s}",
                details={"error": str(e)},
                timestamp=time.time())

    def check_ai_model_status(self) -> DiagnosticResult:
        """Check AI model loading status."""
        try:
            # Try to get AI model status from the API
            response = requests.get(f"{self.api_url}/ai/status", timeout=self.timeout)

            if response.status_code == 200:
                ai_status = response.json()

                models_ready = ai_status.get("models_ready", 0)
                total_models = ai_status.get("total_models", 0)
                loading_status = ai_status.get("status", "unknown")

                if loading_status == "ready" and models_ready == total_models:
                    status = DiagnosticStatus.HEALTHY
                    message = f"All AI models are ready ({models_ready}/{total_models})"
                elif loading_status == "loading":
                    status = DiagnosticStatus.WARNING
                    message = f"AI models are loading ({models_ready}/{total_models} ready)"
                else:
                    status = DiagnosticStatus.ERROR
                    message = f"AI models are not ready ({models_ready}/{total_models})"

                return DiagnosticResult(
                    component="ai_model_status",
                    status=status,
                    message=message,
                    details={
                        "loading_status": loading_status,
                        "models_ready": models_ready,
                        "total_models": total_models,
                        "model_details": ai_status.get("models", {}),
                    },
                    timestamp=time.time())
            if response.status_code == 404:
                return DiagnosticResult(
                    component="ai_model_status",
                    status=DiagnosticStatus.WARNING,
                    message="AI status endpoint not available",
                    details={
                        "suggestion": "AI model status checking may not be implemented",
                    },
                    timestamp=time.time())
            return DiagnosticResult(
                component="ai_model_status",
                status=DiagnosticStatus.ERROR,
                message=f"AI status check returned {response.status_code}",
                details={"status_code": response.status_code},
                timestamp=time.time())

        except Exception as e:
            return DiagnosticResult(
                component="ai_model_status",
                status=DiagnosticStatus.ERROR,
                message=f"AI model status check failed: {e!s}",
                details={"error": str(e)},
                timestamp=time.time())

    def validate_file_format(self, file_path: str) -> DiagnosticResult:
        """Validate if a file can be processed for analysis.

        Args:
            file_path: Path to the file to validate

        Returns:
            Diagnostic result for file validation

        """
        try:
            path = Path(file_path)

            if not path.exists():
                return DiagnosticResult(
                    component="file_validation",
                    status=DiagnosticStatus.ERROR,
                    message="File does not exist",
                    details={"file_path": file_path},
                    timestamp=time.time())

            # Check file size
            file_size = path.stat().st_size
            max_size = 50 * 1024 * 1024  # 50MB

            if file_size == 0:
                return DiagnosticResult(
                    component="file_validation",
                    status=DiagnosticStatus.ERROR,
                    message="File is empty",
                    details={"file_path": file_path, "file_size": file_size},
                    timestamp=time.time())

            if file_size > max_size:
                return DiagnosticResult(
                    component="file_validation",
                    status=DiagnosticStatus.WARNING,
                    message=f"File is large ({file_size / 1024 / 1024}MB)",
                    details={
                        "file_path": file_path,
                        "file_size": file_size,
                        "max_recommended_size": max_size,
                    },
                    timestamp=time.time())

            # Check file extension
            supported_extensions = {".txt", ".pdf", ".docx", ".doc"}
            file_extension = path.suffix.lower()

            if file_extension not in supported_extensions:
                return DiagnosticResult(
                    component="file_validation",
                    status=DiagnosticStatus.WARNING,
                    message=f"File extension '{file_extension}' may not be supported",
                    details={
                        "file_path": file_path,
                        "file_extension": file_extension,
                        "supported_extensions": list(supported_extensions),
                    },
                    timestamp=time.time())

            return DiagnosticResult(
                component="file_validation",
                status=DiagnosticStatus.HEALTHY,
                message="File appears to be valid for analysis",
                details={
                    "file_path": file_path,
                    "file_size": file_size,
                    "file_extension": file_extension,
                },
                timestamp=time.time())

        except (OSError, FileNotFoundError) as e:
            return DiagnosticResult(
                component="file_validation",
                status=DiagnosticStatus.ERROR,
                message=f"File validation failed: {e!s}",
                details={"file_path": file_path, "error": str(e)},
                timestamp=time.time())

    def _calculate_overall_status(self, diagnostics: dict[str, DiagnosticResult]) -> str:
        """Calculate overall system health status."""
        if not diagnostics:
            return "no_diagnostics"

        error_count = sum(1 for d in diagnostics.values() if d.status == DiagnosticStatus.ERROR)
        warning_count = sum(1 for d in diagnostics.values() if d.status == DiagnosticStatus.WARNING)

        if error_count > 0:
            return f"unhealthy ({error_count} errors, {warning_count} warnings)"
        if warning_count > 0:
            return f"degraded ({warning_count} warnings)"
        return "healthy"


# Global diagnostics instance
# Global diagnostics instance
# Global diagnostics instance
diagnostics = AnalysisDiagnostics()
