"""Performance Test Orchestrator - Comprehensive testing framework coordinator

This module provides the main orchestration for all performance testing activities,
including test suite management, execution coordination, and result aggregation.
"""

import asyncio
import logging
import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import sqlalchemy
import sqlalchemy.exc
import yaml

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Test execution status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PerformanceCategory(Enum):
    """Test category enumeration"""

    BASELINE = "baseline"
    OPTIMIZATION = "optimization"
    LOAD = "load"
    STRESS = "stress"
    INTEGRATION = "integration"
    BENCHMARK = "benchmark"


@dataclass
class PerformanceTestConfig:
    """Configuration for individual performance tests"""

    name: str
    category: PerformanceCategory
    description: str
    timeout_seconds: int = 300
    retry_count: int = 3
    enabled: bool = True
    parameters: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)


@dataclass
class SingleTestResult:
    """Result of a single performance test"""

    test_name: str
    category: PerformanceCategory
    status: ExecutionStatus
    start_time: datetime
    end_time: datetime | None = None
    duration_seconds: float | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    artifacts: dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceTestResults:
    """Aggregated results from performance test suite"""

    suite_name: str
    start_time: datetime
    end_time: datetime | None = None
    total_duration_seconds: float | None = None
    test_results: list[SingleTestResult] = field(default_factory=list)
    summary_metrics: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


class ExecutionEngine:
    """Executes individual tests and collects results"""

    def __init__(self):
        """Initialize the execution engine."""
        self.test_runners = {}
        self.active_tests = {}

    def register_test_runner(self, category: PerformanceCategory, runner: Callable) -> None:
        """Register a test runner for a specific category"""
        self.test_runners[category] = runner
        logger.info("Registered test runner for category: %s", category.value)

    async def execute_test(self, config: PerformanceTestConfig) -> SingleTestResult:
        """Execute a single performance test"""
        result = SingleTestResult(
            test_name=config.name, category=config.category, status=ExecutionStatus.RUNNING, start_time=datetime.now()
        )

        try:
            logger.info("Starting test: %s", config.name)

            # Check if test runner is available
            if config.category not in self.test_runners:
                raise ValueError(f"No test runner registered for category: {config.category.value}")

            # Execute test with timeout
            test_runner = self.test_runners[config.category]

            start_time = time.time()
            test_task = asyncio.create_task(test_runner(config))

            try:
                test_metrics = await asyncio.wait_for(test_task, timeout=config.timeout_seconds)
                result.metrics = test_metrics
                result.status = ExecutionStatus.COMPLETED

            except TimeoutError:
                test_task.cancel()
                result.status = ExecutionStatus.FAILED
                result.error_message = f"Test timed out after {config.timeout_seconds} seconds"

            except Exception as e:
                result.status = ExecutionStatus.FAILED
                result.error_message = str(e)

            end_time = time.time()
            result.end_time = datetime.now()
            result.duration_seconds = end_time - start_time

            logger.info("Test %s completed with status: {result.status.value}", config.name)

        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            logger.exception("Test %s failed: {e}", config.name)

        return result

    async def execute_tests_parallel(self, configs: list[PerformanceTestConfig]) -> list[SingleTestResult]:
        """Execute multiple tests in parallel"""
        tasks = []
        for config in configs:
            if config.enabled:
                task = asyncio.create_task(self.execute_test(config))
                tasks.append(task)

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions that occurred
        test_results: list[SingleTestResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_result = SingleTestResult(
                    test_name=configs[i].name,
                    category=configs[i].category,
                    status=ExecutionStatus.FAILED,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    error_message=str(result),
                )
                test_results.append(failed_result)
            else:
                test_results.append(result)

        return test_results


class SuiteManager:
    """Manages test suites and configurations."""

    def __init__(self, config_path: str | None = None):
        """Initialize the suite manager.

        Args:
            config_path: Optional path to YAML configuration file
        """
        self.test_suites = {}
        self.test_configurations = {}
        self.config_path = config_path

        if config_path:
            self._load_configurations_from_yaml(config_path)
        else:
            self._load_default_suites()

    def _load_default_suites(self):
        """Load default test suites."""
        # Baseline tests suite
        baseline_tests = [
            PerformanceTestConfig(
                name="baseline_response_time",
                category=PerformanceCategory.BASELINE,
                description="Baseline response time performance",
            ),
            PerformanceTestConfig(
                name="document_processing_baseline",
                category=PerformanceCategory.BASELINE,
                description="Baseline document processing performance",
            ),
            PerformanceTestConfig(
                name="analysis_baseline",
                category=PerformanceCategory.BASELINE,
                description="Baseline analysis performance",
            ),
        ]

        # Optimization tests suite
        optimization_tests = [
            PerformanceTestConfig(
                name="cache_optimization",
                category=PerformanceCategory.OPTIMIZATION,
                description="Cache optimization performance",
            ),
            PerformanceTestConfig(
                name="memory_optimization",
                category=PerformanceCategory.OPTIMIZATION,
                description="Memory optimization performance",
            ),
        ]

        # Load tests suite
        load_tests = [
            PerformanceTestConfig(
                name="concurrent_processing",
                category=PerformanceCategory.LOAD,
                description="Concurrent document processing",
            )
        ]

        self.test_suites = {
            "baseline_tests": baseline_tests,
            "optimization_tests": optimization_tests,
            "optimization_suite": optimization_tests,  # Alias for test compatibility
            "load_tests": load_tests,
            "full_suite": baseline_tests + optimization_tests + load_tests,
        }

        # Also populate test_configurations for individual access
        all_tests = baseline_tests + optimization_tests + load_tests
        self.test_configurations = {test.name: test for test in all_tests}

    def get_suite(self, suite_name: str) -> list[PerformanceTestConfig]:
        """Get a test suite by name."""
        suite_data = self.test_suites.get(suite_name, [])

        # If suite contains test names (strings), convert to test objects
        if suite_data and isinstance(suite_data[0], str):
            return [self.test_configurations[name] for name in suite_data if name in self.test_configurations]

        # Otherwise return as-is (already test objects)
        return suite_data

    def get_available_suites(self) -> list[str]:
        """Get list of available suite names."""
        return list(self.test_suites.keys())

    def get_suite_tests(self, suite_name: str) -> list[PerformanceTestConfig]:
        """Get test configurations for a suite."""
        return self.get_suite(suite_name)

    def get_test_configuration(self, test_name: str) -> PerformanceTestConfig | None:
        """Get a specific test configuration by name."""
        return self.test_configurations.get(test_name)

    def _load_configurations_from_yaml(self, config_path: str) -> None:
        """Load test configurations from YAML file."""
        try:
            with open(config_path) as f:
                config_data = yaml.safe_load(f)

            # Load test configurations
            tests = config_data.get("tests", [])
            test_configs = []

            for test_data in tests:
                config = PerformanceTestConfig(
                    name=test_data["name"],
                    category=PerformanceCategory(test_data["category"]),
                    description=test_data["description"],
                    timeout_seconds=test_data.get("timeout_seconds", 300),
                    enabled=test_data.get("enabled", True),
                    parameters=test_data.get("parameters", {}),
                )
                test_configs.append(config)
                self.test_configurations[config.name] = config

            # Load test suites
            suites = config_data.get("suites", {})
            for suite_name, test_names in suites.items():
                # Store test names for direct access
                self.test_suites[suite_name] = test_names

        except Exception as e:
            logger.exception("Failed to load configurations from YAML: %s", e)
            # Fall back to default suites
            self._load_default_suites()


class PerformanceTestOrchestrator:
    """Main orchestrator for performance testing activities"""

    def __init__(self):
        """Initialize the performance test orchestrator."""
        self.execution_engine = ExecutionEngine()
        self.suite_manager = SuiteManager()
        self.results_history = []
        self._register_default_runners()

    def _register_default_runners(self) -> None:
        """Register default test runners for each category"""

        async def baseline_runner(config: PerformanceTestConfig) -> dict[str, Any]:
            """Default baseline test runner"""
            # Simulate baseline performance measurement
            await asyncio.sleep(1)  # Simulate test execution
            return {
                "response_time_ms": 150.0,
                "memory_usage_mb": 256.0,
                "cpu_usage_percent": 45.0,
                "test_type": "baseline",
            }

        async def optimization_runner(config: PerformanceTestConfig) -> dict[str, Any]:
            """Default optimization test runner"""
            # Simulate optimization performance measurement
            await asyncio.sleep(1.5)  # Simulate test execution
            return {
                "response_time_ms": 95.0,  # Improved performance
                "memory_usage_mb": 180.0,  # Reduced memory usage
                "cpu_usage_percent": 35.0,  # Reduced CPU usage
                "cache_hit_rate": 0.75,
                "optimization_enabled": True,
                "test_type": "optimization",
            }

        async def load_runner(config: PerformanceTestConfig) -> dict[str, Any]:
            """Default load test runner"""
            # Simulate load testing
            await asyncio.sleep(2)  # Simulate test execution
            return {
                "throughput_docs_per_minute": 25.0,
                "average_response_time_ms": 180.0,
                "peak_memory_usage_mb": 512.0,
                "error_rate_percent": 0.5,
                "concurrent_users": 10,
                "test_type": "load",
            }

        # Register runners
        self.execution_engine.register_test_runner(PerformanceCategory.BASELINE, baseline_runner)
        self.execution_engine.register_test_runner(PerformanceCategory.OPTIMIZATION, optimization_runner)
        self.execution_engine.register_test_runner(PerformanceCategory.LOAD, load_runner)
        self.execution_engine.register_test_runner(PerformanceCategory.STRESS, load_runner)  # Reuse for now
        self.execution_engine.register_test_runner(
            PerformanceCategory.INTEGRATION, optimization_runner
        )  # Reuse for now
        self.execution_engine.register_test_runner(PerformanceCategory.BENCHMARK, baseline_runner)  # Reuse for now

    async def run_test_suite(self, suite_name: str) -> PerformanceTestResults:
        """Run a complete test suite"""
        logger.info("Starting test suite: %s", suite_name)

        suite_result = PerformanceTestResults(suite_name=suite_name, start_time=datetime.now())

        try:
            # Get test configurations for the suite
            test_configs = self.suite_manager.get_suite_tests(suite_name)

            if not test_configs:
                logger.warning("No tests found for suite: %s", suite_name)
                return suite_result

            # Execute tests
            test_results = await self.execution_engine.execute_tests_parallel(test_configs)
            suite_result.test_results = test_results

            # Calculate summary metrics
            suite_result.summary_metrics = self._calculate_summary_metrics(test_results)

            # Generate recommendations
            suite_result.recommendations = self._generate_recommendations(test_results)

            suite_result.end_time = datetime.now()
            suite_result.total_duration_seconds = (suite_result.end_time - suite_result.start_time).total_seconds()

            # Store results
            self.results_history.append(suite_result)

            logger.info("Test suite %s completed in {suite_result.total_duration_seconds} seconds", suite_name)

        except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
            logger.exception("Error running test suite %s: {e}", suite_name)
            suite_result.end_time = datetime.now()

        return suite_result

    async def run_full_performance_suite(self) -> PerformanceTestResults:
        """Run the complete performance test suite"""
        return await self.run_test_suite("full_suite")

    async def run_baseline_tests(self) -> PerformanceTestResults:
        """Run baseline performance tests"""
        baseline_configs = [
            config
            for config in self.suite_manager.test_configurations.values()
            if config.category == PerformanceCategory.BASELINE and config.enabled
        ]

        suite_result = PerformanceTestResults(suite_name="baseline_tests", start_time=datetime.now())

        if baseline_configs:
            test_results = await self.execution_engine.execute_tests_parallel(baseline_configs)
            suite_result.test_results = test_results
            suite_result.summary_metrics = self._calculate_summary_metrics(test_results)

        suite_result.end_time = datetime.now()
        return suite_result

    async def run_optimization_tests(self) -> PerformanceTestResults:
        """Run optimization performance tests"""
        optimization_configs = [
            config
            for config in self.suite_manager.test_configurations.values()
            if config.category == PerformanceCategory.OPTIMIZATION and config.enabled
        ]

        suite_result = PerformanceTestResults(suite_name="optimization_tests", start_time=datetime.now())

        if optimization_configs:
            test_results = await self.execution_engine.execute_tests_parallel(optimization_configs)
            suite_result.test_results = test_results
            suite_result.summary_metrics = self._calculate_summary_metrics(test_results)

        suite_result.end_time = datetime.now()
        return suite_result

    def _calculate_summary_metrics(self, test_results: list[SingleTestResult]) -> dict[str, Any]:
        """Calculate summary metrics from test results"""
        if not test_results:
            return {}

        completed_tests = [r for r in test_results if r.status == ExecutionStatus.COMPLETED]
        failed_tests = [r for r in test_results if r.status == ExecutionStatus.FAILED]

        summary = {
            "total_tests": len(test_results),
            "completed_tests": len(completed_tests),
            "failed_tests": len(failed_tests),
            "success_rate": len(completed_tests) / len(test_results) if test_results else 0,
            "average_duration_seconds": 0.0,
            "total_duration_seconds": 0.0,
        }

        if completed_tests:
            durations = [r.duration_seconds for r in completed_tests if r.duration_seconds]
            if durations:
                summary["average_duration_seconds"] = sum(durations) / len(durations)
                summary["total_duration_seconds"] = sum(durations)

        # Aggregate performance metrics
        response_times = []
        memory_usage = []

        for result in completed_tests:
            if "response_time_ms" in result.metrics:
                response_times.append(result.metrics["response_time_ms"])
            if "memory_usage_mb" in result.metrics:
                memory_usage.append(result.metrics["memory_usage_mb"])

        if response_times:
            summary["average_response_time_ms"] = sum(response_times) / len(response_times)
            summary["min_response_time_ms"] = min(response_times)
            summary["max_response_time_ms"] = max(response_times)

        if memory_usage:
            summary["average_memory_usage_mb"] = sum(memory_usage) / len(memory_usage)
            summary["peak_memory_usage_mb"] = max(memory_usage)

        return summary

    def _generate_recommendations(self, test_results: list[SingleTestResult]) -> list[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        failed_tests = [r for r in test_results if r.status == ExecutionStatus.FAILED]
        if failed_tests:
            recommendations.append(f"Address {len(failed_tests)} failed tests to improve system reliability")

        completed_tests = [r for r in test_results if r.status == ExecutionStatus.COMPLETED]

        # Analyze response times
        response_times = [
            r.metrics.get("response_time_ms", 0) for r in completed_tests if "response_time_ms" in r.metrics
        ]

        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            if avg_response_time > 200:
                recommendations.append("Consider enabling additional optimizations to improve response times")

        # Analyze memory usage
        memory_usage = [r.metrics.get("memory_usage_mb", 0) for r in completed_tests if "memory_usage_mb" in r.metrics]

        if memory_usage:
            avg_memory = sum(memory_usage) / len(memory_usage)
            if avg_memory > 400:
                recommendations.append("High memory usage detected - consider memory optimization strategies")

        if not recommendations:
            recommendations.append("Performance tests completed successfully - system is performing well")

        return recommendations

    def get_test_history(self) -> list[PerformanceTestResults]:
        """Get historical test results"""
        return self.results_history.copy()

    def get_available_suites(self) -> list[str]:
        """Get list of available test suites."""
        return self.suite_manager.get_available_suites()
