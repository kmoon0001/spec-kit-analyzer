"""
Performance Test Orchestrator - Comprehensive testing framework coordinator

This module provides the main orchestration for all performance testing activities,
including test suite management, execution coordination, and result aggregation.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import yaml

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Test execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TestCategory(Enum):
    """Test category enumeration"""
    BASELINE = "baseline"
    OPTIMIZATION = "optimization"
    LOAD = "load"
    STRESS = "stress"
    INTEGRATION = "integration"
    BENCHMARK = "benchmark"


@dataclass
class TestConfiguration:
    """Configuration for individual performance tests"""
    name: str
    category: TestCategory
    description: str
    timeout_seconds: int = 300
    retry_count: int = 3
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    """Result of a single performance test"""
    test_name: str
    category: TestCategory
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    artifacts: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceTestResults:
    """Aggregated results from performance test suite"""
    suite_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    test_results: List[TestResult] = field(default_factory=list)
    summary_metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class TestSuiteManager:
    """Manages test suite configurations and organization"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config/performance_tests.yaml")
        self.test_configurations: Dict[str, TestConfiguration] = {}
        self.test_suites: Dict[str, List[str]] = {}
        self._load_configurations()
    
    def _load_configurations(self) -> None:
        """Load test configurations from YAML file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    
                # Load individual test configurations
                for test_config in config_data.get('tests', []):
                    test = TestConfiguration(
                        name=test_config['name'],
                        category=TestCategory(test_config['category']),
                        description=test_config['description'],
                        timeout_seconds=test_config.get('timeout_seconds', 300),
                        retry_count=test_config.get('retry_count', 3),
                        enabled=test_config.get('enabled', True),
                        parameters=test_config.get('parameters', {}),
                        dependencies=test_config.get('dependencies', [])
                    )
                    self.test_configurations[test.name] = test
                
                # Load test suite definitions
                self.test_suites = config_data.get('suites', {})
                
                logger.info(f"Loaded {len(self.test_configurations)} test configurations")
            else:
                logger.warning(f"Test configuration file not found: {self.config_path}")
                self._create_default_configuration()
                
        except Exception as e:
            logger.error(f"Error loading test configurations: {e}")
            self._create_default_configuration()
    
    def _create_default_configuration(self) -> None:
        """Create default test configuration"""
        default_tests = [
            TestConfiguration(
                name="baseline_response_time",
                category=TestCategory.BASELINE,
                description="Measure baseline response times without optimizations",
                parameters={"document_count": 10, "iterations": 5}
            ),
            TestConfiguration(
                name="cache_optimization_test",
                category=TestCategory.OPTIMIZATION,
                description="Test cache optimization effectiveness",
                parameters={"cache_enabled": True, "document_count": 20}
            ),
            TestConfiguration(
                name="memory_optimization_test",
                category=TestCategory.OPTIMIZATION,
                description="Test memory optimization effectiveness",
                parameters={"memory_optimization": True, "document_count": 15}
            ),
            TestConfiguration(
                name="load_test_standard",
                category=TestCategory.LOAD,
                description="Standard load testing with realistic document volumes",
                parameters={"documents_per_minute": 30, "duration_minutes": 5}
            )
        ]
        
        for test in default_tests:
            self.test_configurations[test.name] = test
        
        self.test_suites = {
            "full_suite": list(self.test_configurations.keys()),
            "optimization_suite": [
                "baseline_response_time",
                "cache_optimization_test", 
                "memory_optimization_test"
            ],
            "load_suite": ["load_test_standard"]
        }
    
    def get_test_configuration(self, test_name: str) -> Optional[TestConfiguration]:
        """Get configuration for a specific test"""
        return self.test_configurations.get(test_name)
    
    def get_suite_tests(self, suite_name: str) -> List[TestConfiguration]:
        """Get all test configurations for a test suite"""
        test_names = self.test_suites.get(suite_name, [])
        return [self.test_configurations[name] for name in test_names 
                if name in self.test_configurations]
    
    def get_available_suites(self) -> List[str]:
        """Get list of available test suites"""
        return list(self.test_suites.keys())


class TestExecutionEngine:
    """Executes individual tests and collects results"""
    
    def __init__(self):
        self.test_runners: Dict[TestCategory, Callable] = {}
        self.active_tests: Dict[str, asyncio.Task] = {}
    
    def register_test_runner(self, category: TestCategory, runner: Callable) -> None:
        """Register a test runner for a specific category"""
        self.test_runners[category] = runner
        logger.info(f"Registered test runner for category: {category.value}")
    
    async def execute_test(self, config: TestConfiguration) -> TestResult:
        """Execute a single performance test"""
        result = TestResult(
            test_name=config.name,
            category=config.category,
            status=TestStatus.RUNNING,
            start_time=datetime.now()
        )
        
        try:
            logger.info(f"Starting test: {config.name}")
            
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
                result.status = TestStatus.COMPLETED
                
            except asyncio.TimeoutError:
                test_task.cancel()
                result.status = TestStatus.FAILED
                result.error_message = f"Test timed out after {config.timeout_seconds} seconds"
                
            except Exception as e:
                result.status = TestStatus.FAILED
                result.error_message = str(e)
            
            end_time = time.time()
            result.end_time = datetime.now()
            result.duration_seconds = end_time - start_time
            
            logger.info(f"Test {config.name} completed with status: {result.status.value}")
            
        except Exception as e:
            result.status = TestStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            logger.error(f"Test {config.name} failed: {e}")
        
        return result
    
    async def execute_tests_parallel(self, configs: List[TestConfiguration]) -> List[TestResult]:
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
        test_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_result = TestResult(
                    test_name=configs[i].name,
                    category=configs[i].category,
                    status=TestStatus.FAILED,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    error_message=str(result)
                )
                test_results.append(failed_result)
            else:
                test_results.append(result)
        
        return test_results


class PerformanceTestOrchestrator:
    """Main orchestrator for performance testing activities"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.suite_manager = TestSuiteManager(config_path)
        self.execution_engine = TestExecutionEngine()
        self.results_history: List[PerformanceTestResults] = []
        
        # Register default test runners
        self._register_default_runners()
    
    def _register_default_runners(self) -> None:
        """Register default test runners for each category"""
        
        async def baseline_runner(config: TestConfiguration) -> Dict[str, Any]:
            """Default baseline test runner"""
            # Simulate baseline performance measurement
            await asyncio.sleep(1)  # Simulate test execution
            return {
                "response_time_ms": 150.0,
                "memory_usage_mb": 256.0,
                "cpu_usage_percent": 45.0,
                "test_type": "baseline"
            }
        
        async def optimization_runner(config: TestConfiguration) -> Dict[str, Any]:
            """Default optimization test runner"""
            # Simulate optimization performance measurement
            await asyncio.sleep(1.5)  # Simulate test execution
            return {
                "response_time_ms": 95.0,  # Improved performance
                "memory_usage_mb": 180.0,  # Reduced memory usage
                "cpu_usage_percent": 35.0,  # Reduced CPU usage
                "cache_hit_rate": 0.75,
                "optimization_enabled": True,
                "test_type": "optimization"
            }
        
        async def load_runner(config: TestConfiguration) -> Dict[str, Any]:
            """Default load test runner"""
            # Simulate load testing
            await asyncio.sleep(2)  # Simulate test execution
            return {
                "throughput_docs_per_minute": 25.0,
                "average_response_time_ms": 180.0,
                "peak_memory_usage_mb": 512.0,
                "error_rate_percent": 0.5,
                "concurrent_users": 10,
                "test_type": "load"
            }
        
        # Register runners
        self.execution_engine.register_test_runner(TestCategory.BASELINE, baseline_runner)
        self.execution_engine.register_test_runner(TestCategory.OPTIMIZATION, optimization_runner)
        self.execution_engine.register_test_runner(TestCategory.LOAD, load_runner)
        self.execution_engine.register_test_runner(TestCategory.STRESS, load_runner)  # Reuse for now
        self.execution_engine.register_test_runner(TestCategory.INTEGRATION, optimization_runner)  # Reuse for now
        self.execution_engine.register_test_runner(TestCategory.BENCHMARK, baseline_runner)  # Reuse for now
    
    async def run_test_suite(self, suite_name: str) -> PerformanceTestResults:
        """Run a complete test suite"""
        logger.info(f"Starting test suite: {suite_name}")
        
        suite_result = PerformanceTestResults(
            suite_name=suite_name,
            start_time=datetime.now()
        )
        
        try:
            # Get test configurations for the suite
            test_configs = self.suite_manager.get_suite_tests(suite_name)
            
            if not test_configs:
                logger.warning(f"No tests found for suite: {suite_name}")
                return suite_result
            
            # Execute tests
            test_results = await self.execution_engine.execute_tests_parallel(test_configs)
            suite_result.test_results = test_results
            
            # Calculate summary metrics
            suite_result.summary_metrics = self._calculate_summary_metrics(test_results)
            
            # Generate recommendations
            suite_result.recommendations = self._generate_recommendations(test_results)
            
            suite_result.end_time = datetime.now()
            suite_result.total_duration_seconds = (
                suite_result.end_time - suite_result.start_time
            ).total_seconds()
            
            # Store results
            self.results_history.append(suite_result)
            
            logger.info(f"Test suite {suite_name} completed in {suite_result.total_duration_seconds:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error running test suite {suite_name}: {e}")
            suite_result.end_time = datetime.now()
        
        return suite_result
    
    async def run_full_performance_suite(self) -> PerformanceTestResults:
        """Run the complete performance test suite"""
        return await self.run_test_suite("full_suite")
    
    async def run_baseline_tests(self) -> PerformanceTestResults:
        """Run baseline performance tests"""
        baseline_configs = [
            config for config in self.suite_manager.test_configurations.values()
            if config.category == TestCategory.BASELINE and config.enabled
        ]
        
        suite_result = PerformanceTestResults(
            suite_name="baseline_tests",
            start_time=datetime.now()
        )
        
        if baseline_configs:
            test_results = await self.execution_engine.execute_tests_parallel(baseline_configs)
            suite_result.test_results = test_results
            suite_result.summary_metrics = self._calculate_summary_metrics(test_results)
        
        suite_result.end_time = datetime.now()
        return suite_result
    
    async def run_optimization_tests(self) -> PerformanceTestResults:
        """Run optimization performance tests"""
        optimization_configs = [
            config for config in self.suite_manager.test_configurations.values()
            if config.category == TestCategory.OPTIMIZATION and config.enabled
        ]
        
        suite_result = PerformanceTestResults(
            suite_name="optimization_tests",
            start_time=datetime.now()
        )
        
        if optimization_configs:
            test_results = await self.execution_engine.execute_tests_parallel(optimization_configs)
            suite_result.test_results = test_results
            suite_result.summary_metrics = self._calculate_summary_metrics(test_results)
        
        suite_result.end_time = datetime.now()
        return suite_result
    
    def _calculate_summary_metrics(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Calculate summary metrics from test results"""
        if not test_results:
            return {}
        
        completed_tests = [r for r in test_results if r.status == TestStatus.COMPLETED]
        failed_tests = [r for r in test_results if r.status == TestStatus.FAILED]
        
        summary = {
            "total_tests": len(test_results),
            "completed_tests": len(completed_tests),
            "failed_tests": len(failed_tests),
            "success_rate": len(completed_tests) / len(test_results) if test_results else 0,
            "average_duration_seconds": 0.0,
            "total_duration_seconds": 0.0
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
    
    def _generate_recommendations(self, test_results: List[TestResult]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [r for r in test_results if r.status == TestStatus.FAILED]
        if failed_tests:
            recommendations.append(
                f"Address {len(failed_tests)} failed tests to improve system reliability"
            )
        
        completed_tests = [r for r in test_results if r.status == TestStatus.COMPLETED]
        
        # Analyze response times
        response_times = [
            r.metrics.get("response_time_ms", 0) for r in completed_tests
            if "response_time_ms" in r.metrics
        ]
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            if avg_response_time > 200:
                recommendations.append(
                    "Consider enabling additional optimizations to improve response times"
                )
        
        # Analyze memory usage
        memory_usage = [
            r.metrics.get("memory_usage_mb", 0) for r in completed_tests
            if "memory_usage_mb" in r.metrics
        ]
        
        if memory_usage:
            avg_memory = sum(memory_usage) / len(memory_usage)
            if avg_memory > 400:
                recommendations.append(
                    "High memory usage detected - consider memory optimization strategies"
                )
        
        if not recommendations:
            recommendations.append("Performance tests completed successfully - system is performing well")
        
        return recommendations
    
    def get_test_history(self) -> List[PerformanceTestResults]:
        """Get historical test results"""
        return self.results_history.copy()
    
    def get_available_suites(self) -> List[str]:
        """Get list of available test suites"""
        return self.suite_manager.get_available_suites()