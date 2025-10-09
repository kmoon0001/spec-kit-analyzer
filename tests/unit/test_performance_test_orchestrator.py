"""
Tests for Performance Test Orchestrator

This module tests the comprehensive performance testing framework coordination,
including test suite management, execution, and result aggregation.
"""

import asyncio
import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import yaml

from src.core.performance_test_orchestrator import (
    PerformanceTestOrchestrator,
    SuiteManager,
    ExecutionEngine,
    PerformanceTestConfig,
    SingleTestResult,
    ExecutionStatus,
    PerformanceCategory,
    PerformanceTestResults
)


class TestPerformanceTestConfig:
    """Test PerformanceTestConfig dataclass"""
    
    def test_performance_test_config_creation(self):
        """Test creating a test configuration"""
        config = PerformanceTestConfig(
            name="test_config",
            category=PerformanceCategory.BASELINE,
            description="Test configuration",
            timeout_seconds=120,
            parameters={"param1": "value1"}
        )
        
        assert config.name == "test_config"
        assert config.category == PerformanceCategory.BASELINE
        assert config.description == "Test configuration"
        assert config.timeout_seconds == 120
        assert config.parameters == {"param1": "value1"}
        assert config.enabled is True
        assert config.retry_count == 3


class TestSuiteManager:
    """Test SuiteManager functionality"""
    
    def test_initialization_with_default_config(self):
        """Test initialization with default configuration"""
        manager = SuiteManager()
        
        # Should have default configurations
        assert len(manager.test_configurations) > 0
        assert len(manager.test_suites) > 0
        assert "full_suite" in manager.test_suites
    
    def test_load_configurations_from_yaml(self):
        """Test loading configurations from YAML file"""
        # Create temporary YAML config
        config_data = {
            'tests': [
                {
                    'name': 'test1',
                    'category': 'baseline',
                    'description': 'Test 1',
                    'timeout_seconds': 60,
                    'parameters': {'param1': 'value1'}
                },
                {
                    'name': 'test2',
                    'category': 'optimization',
                    'description': 'Test 2',
                    'enabled': False
                }
            ],
            'suites': {
                'custom_suite': ['test1', 'test2']
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            manager = SuiteManager(config_path)
            
            # Verify configurations loaded
            assert len(manager.test_configurations) == 2
            assert 'test1' in manager.test_configurations
            assert 'test2' in manager.test_configurations
            
            test1 = manager.test_configurations['test1']
            assert test1.category == PerformanceCategory.BASELINE
            assert test1.timeout_seconds == 60
            assert test1.parameters == {'param1': 'value1'}
            
            test2 = manager.test_configurations['test2']
            assert test2.enabled is False
            
            # Verify suites loaded
            assert 'custom_suite' in manager.test_suites
            assert manager.test_suites['custom_suite'] == ['test1', 'test2']
            
        finally:
            config_path.unlink()  # Clean up
    
    def test_get_test_configuration(self):
        """Test getting specific test configuration"""
        manager = SuiteManager()
        
        # Should return existing configuration
        config = manager.get_test_configuration("baseline_response_time")
        assert config is not None
        assert config.name == "baseline_response_time"
        
        # Should return None for non-existent configuration
        config = manager.get_test_configuration("non_existent")
        assert config is None
    
    def test_get_suite_tests(self):
        """Test getting test configurations for a suite"""
        manager = SuiteManager()
        
        # Should return configurations for existing suite
        configs = manager.get_suite_tests("optimization_suite")
        assert len(configs) > 0
        assert all(isinstance(config, PerformanceTestConfig) for config in configs)
        
        # Should return empty list for non-existent suite
        configs = manager.get_suite_tests("non_existent_suite")
        assert configs == []
    
    def test_get_available_suites(self):
        """Test getting list of available suites"""
        manager = SuiteManager()
        
        suites = manager.get_available_suites()
        assert isinstance(suites, list)
        assert len(suites) > 0
        assert "full_suite" in suites


class TestExecutionEngine:
    """Test ExecutionEngine functionality"""
    
    def test_initialization(self):
        """Test engine initialization"""
        engine = ExecutionEngine()
        
        assert isinstance(engine.test_runners, dict)
        assert isinstance(engine.active_tests, dict)
        assert len(engine.test_runners) == 0
    
    def test_register_test_runner(self):
        """Test registering test runners"""
        engine = ExecutionEngine()
        
        async def mock_runner(config):
            return {"result": "success"}
        
        engine.register_test_runner(PerformanceCategory.BASELINE, mock_runner)
        
        assert PerformanceCategory.BASELINE in engine.test_runners
        assert engine.test_runners[PerformanceCategory.BASELINE] == mock_runner
    
    @pytest.mark.asyncio
    async def test_execute_test_success(self):
        """Test successful test execution"""
        engine = ExecutionEngine()
        
        # Register mock runner
        async def mock_runner(config):
            await asyncio.sleep(0.1)  # Simulate work
            return {"response_time_ms": 100.0, "success": True}
        
        engine.register_test_runner(PerformanceCategory.BASELINE, mock_runner)
        
        # Create test configuration
        config = PerformanceTestConfig(
            name="test_success",
            category=PerformanceCategory.BASELINE,
            description="Successful test"
        )
        
        # Execute test
        result = await engine.execute_test(config)
        
        assert result.test_name == "test_success"
        assert result.category == PerformanceCategory.BASELINE
        assert result.status == ExecutionStatus.COMPLETED
        assert result.start_time is not None
        assert result.end_time is not None
        assert result.duration_seconds is not None
        assert result.duration_seconds > 0
        assert result.metrics == {"response_time_ms": 100.0, "success": True}
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_execute_test_failure(self):
        """Test test execution with failure"""
        engine = ExecutionEngine()
        
        # Register failing runner
        async def failing_runner(config):
            raise ValueError("Test failed")
        
        engine.register_test_runner(PerformanceCategory.BASELINE, failing_runner)
        
        config = PerformanceTestConfig(
            name="test_failure",
            category=PerformanceCategory.BASELINE,
            description="Failing test"
        )
        
        result = await engine.execute_test(config)
        
        assert result.status == ExecutionStatus.FAILED
        assert "Test failed" in result.error_message
    
    @pytest.mark.asyncio
    async def test_execute_test_timeout(self):
        """Test test execution with timeout"""
        engine = ExecutionEngine()
        
        # Register slow runner
        async def slow_runner(config):
            await asyncio.sleep(2)  # Longer than timeout
            return {"result": "success"}
        
        engine.register_test_runner(PerformanceCategory.BASELINE, slow_runner)
        
        config = PerformanceTestConfig(
            name="test_timeout",
            category=PerformanceCategory.BASELINE,
            description="Timeout test",
            timeout_seconds=1  # Short timeout
        )
        
        result = await engine.execute_test(config)
        
        assert result.status == ExecutionStatus.FAILED
        assert "timed out" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_execute_test_no_runner(self):
        """Test test execution with no registered runner"""
        engine = ExecutionEngine()
        
        config = PerformanceTestConfig(
            name="test_no_runner",
            category=PerformanceCategory.BASELINE,
            description="Test with no runner"
        )
        
        result = await engine.execute_test(config)
        
        assert result.status == ExecutionStatus.FAILED
        assert "No test runner registered" in result.error_message
    
    @pytest.mark.asyncio
    async def test_execute_tests_parallel(self):
        """Test parallel test execution"""
        engine = ExecutionEngine()
        
        # Register mock runners
        async def fast_runner(config):
            await asyncio.sleep(0.1)
            return {"speed": "fast"}
        
        async def slow_runner(config):
            await asyncio.sleep(0.2)
            return {"speed": "slow"}
        
        engine.register_test_runner(PerformanceCategory.BASELINE, fast_runner)
        engine.register_test_runner(PerformanceCategory.OPTIMIZATION, slow_runner)
        
        configs = [
            PerformanceTestConfig("test1", PerformanceCategory.BASELINE, "Fast test"),
            PerformanceTestConfig("test2", PerformanceCategory.OPTIMIZATION, "Slow test"),
            PerformanceTestConfig("test3", PerformanceCategory.BASELINE, "Another fast test")
        ]
        
        start_time = asyncio.get_event_loop().time()
        results = await engine.execute_tests_parallel(configs)
        end_time = asyncio.get_event_loop().time()
        
        # Should complete in parallel (closer to slow_runner time than sum of all)
        assert end_time - start_time < 0.5  # Much less than sequential execution
        
        assert len(results) == 3
        assert all(result.status == ExecutionStatus.COMPLETED for result in results)
    
    @pytest.mark.asyncio
    async def test_execute_tests_parallel_with_disabled(self):
        """Test parallel execution with disabled tests"""
        engine = ExecutionEngine()
        
        async def mock_runner(config):
            return {"result": "success"}
        
        engine.register_test_runner(PerformanceCategory.BASELINE, mock_runner)
        
        configs = [
            PerformanceTestConfig("test1", PerformanceCategory.BASELINE, "Enabled test", enabled=True),
            PerformanceTestConfig("test2", PerformanceCategory.BASELINE, "Disabled test", enabled=False),
            PerformanceTestConfig("test3", PerformanceCategory.BASELINE, "Another enabled test", enabled=True)
        ]
        
        results = await engine.execute_tests_parallel(configs)
        
        # Should only execute enabled tests
        assert len(results) == 2
        assert all(result.status == ExecutionStatus.COMPLETED for result in results)


class TestPerformanceTestOrchestrator:
    """Test PerformanceTestOrchestrator functionality"""
    
    def test_initialization(self):
        """Test orchestrator initialization"""
        orchestrator = PerformanceTestOrchestrator()
        
        assert isinstance(orchestrator.suite_manager, SuiteManager)
        assert isinstance(orchestrator.execution_engine, ExecutionEngine)
        assert isinstance(orchestrator.results_history, list)
        
        # Should have default runners registered
        assert len(orchestrator.execution_engine.test_runners) > 0
    
    @pytest.mark.asyncio
    async def test_run_baseline_tests(self):
        """Test running baseline tests"""
        orchestrator = PerformanceTestOrchestrator()
        
        results = await orchestrator.run_baseline_tests()
        
        assert isinstance(results, PerformanceTestResults)
        assert results.suite_name == "baseline_tests"
        assert results.start_time is not None
        assert results.end_time is not None
        assert len(results.test_results) > 0
        
        # Should only contain baseline tests
        baseline_results = [r for r in results.test_results if r.category == PerformanceCategory.BASELINE]
        assert len(baseline_results) == len(results.test_results)
    
    @pytest.mark.asyncio
    async def test_run_optimization_tests(self):
        """Test running optimization tests"""
        orchestrator = PerformanceTestOrchestrator()
        
        results = await orchestrator.run_optimization_tests()
        
        assert isinstance(results, PerformanceTestResults)
        assert results.suite_name == "optimization_tests"
        assert len(results.test_results) > 0
        
        # Should only contain optimization tests
        optimization_results = [r for r in results.test_results if r.category == PerformanceCategory.OPTIMIZATION]
        assert len(optimization_results) == len(results.test_results)
    
    @pytest.mark.asyncio
    async def test_run_test_suite(self):
        """Test running a specific test suite"""
        orchestrator = PerformanceTestOrchestrator()
        
        results = await orchestrator.run_test_suite("optimization_suite")
        
        assert isinstance(results, PerformanceTestResults)
        assert results.suite_name == "optimization_suite"
        assert results.start_time is not None
        assert results.end_time is not None
        assert results.total_duration_seconds is not None
        assert results.total_duration_seconds > 0
        assert len(results.test_results) > 0
        assert isinstance(results.summary_metrics, dict)
        assert isinstance(results.recommendations, list)
        
        # Should be stored in history
        assert len(orchestrator.results_history) == 1
        assert orchestrator.results_history[0] == results
    
    @pytest.mark.asyncio
    async def test_run_full_performance_suite(self):
        """Test running the full performance suite"""
        orchestrator = PerformanceTestOrchestrator()
        
        results = await orchestrator.run_full_performance_suite()
        
        assert isinstance(results, PerformanceTestResults)
        assert results.suite_name == "full_suite"
        assert len(results.test_results) > 0
        
        # Should contain multiple test categories
        categories = {result.category for result in results.test_results}
        assert len(categories) > 1
    
    @pytest.mark.asyncio
    async def test_run_nonexistent_suite(self):
        """Test running a non-existent test suite"""
        orchestrator = PerformanceTestOrchestrator()
        
        results = await orchestrator.run_test_suite("nonexistent_suite")
        
        assert isinstance(results, PerformanceTestResults)
        assert results.suite_name == "nonexistent_suite"
        assert len(results.test_results) == 0
    
    def test_calculate_summary_metrics(self):
        """Test summary metrics calculation"""
        orchestrator = PerformanceTestOrchestrator()
        
        # Create mock test results
        test_results = [
            SingleTestResult(
                test_name="test1",
                category=PerformanceCategory.BASELINE,
                status=ExecutionStatus.COMPLETED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=1.5,
                metrics={"response_time_ms": 100.0, "memory_usage_mb": 200.0}
            ),
            SingleTestResult(
                test_name="test2",
                category=PerformanceCategory.OPTIMIZATION,
                status=ExecutionStatus.COMPLETED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=2.0,
                metrics={"response_time_ms": 80.0, "memory_usage_mb": 150.0}
            ),
            SingleTestResult(
                test_name="test3",
                category=PerformanceCategory.LOAD,
                status=ExecutionStatus.FAILED,
                start_time=datetime.now(),
                error_message="Test failed"
            )
        ]
        
        summary = orchestrator._calculate_summary_metrics(test_results)
        
        assert summary["total_tests"] == 3
        assert summary["completed_tests"] == 2
        assert summary["failed_tests"] == 1
        assert summary["success_rate"] == 2/3
        assert summary["average_duration_seconds"] == 1.75  # (1.5 + 2.0) / 2
        assert summary["total_duration_seconds"] == 3.5  # 1.5 + 2.0
        assert summary["average_response_time_ms"] == 90.0  # (100 + 80) / 2
        assert summary["min_response_time_ms"] == 80.0
        assert summary["max_response_time_ms"] == 100.0
        assert summary["average_memory_usage_mb"] == 175.0  # (200 + 150) / 2
        assert summary["peak_memory_usage_mb"] == 200.0
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        orchestrator = PerformanceTestOrchestrator()
        
        # Test with failed tests
        test_results_with_failures = [
            SingleTestResult("test1", PerformanceCategory.BASELINE, ExecutionStatus.FAILED, datetime.now()),
            SingleTestResult("test2", PerformanceCategory.OPTIMIZATION, ExecutionStatus.COMPLETED, datetime.now(),
                      metrics={"response_time_ms": 50.0, "memory_usage_mb": 100.0})
        ]
        
        recommendations = orchestrator._generate_recommendations(test_results_with_failures)
        assert any("failed tests" in rec.lower() for rec in recommendations)
        
        # Test with high response times
        test_results_slow = [
            SingleTestResult("test1", PerformanceCategory.BASELINE, ExecutionStatus.COMPLETED, datetime.now(),
                      metrics={"response_time_ms": 300.0})
        ]
        
        recommendations = orchestrator._generate_recommendations(test_results_slow)
        assert any("response times" in rec.lower() for rec in recommendations)
        
        # Test with high memory usage
        test_results_memory = [
            SingleTestResult("test1", PerformanceCategory.BASELINE, ExecutionStatus.COMPLETED, datetime.now(),
                      metrics={"memory_usage_mb": 500.0})
        ]
        
        recommendations = orchestrator._generate_recommendations(test_results_memory)
        assert any("memory" in rec.lower() for rec in recommendations)
        
        # Test with good performance
        test_results_good = [
            SingleTestResult("test1", PerformanceCategory.BASELINE, ExecutionStatus.COMPLETED, datetime.now(),
                      metrics={"response_time_ms": 50.0, "memory_usage_mb": 100.0})
        ]
        
        recommendations = orchestrator._generate_recommendations(test_results_good)
        assert any("performing well" in rec.lower() for rec in recommendations)
    
    def test_get_test_history(self):
        """Test getting test history"""
        orchestrator = PerformanceTestOrchestrator()
        
        # Initially empty
        history = orchestrator.get_test_history()
        assert history == []
        
        # Add some results
        result1 = PerformanceTestResults("suite1", datetime.now())
        result2 = PerformanceTestResults("suite2", datetime.now())
        orchestrator.results_history.extend([result1, result2])
        
        history = orchestrator.get_test_history()
        assert len(history) == 2
        assert history[0] == result1
        assert history[1] == result2
        
        # Should return a copy
        history.append("modified")
        assert len(orchestrator.results_history) == 2
    
    def test_get_available_suites(self):
        """Test getting available suites"""
        orchestrator = PerformanceTestOrchestrator()
        
        suites = orchestrator.get_available_suites()
        assert isinstance(suites, list)
        assert len(suites) > 0
        assert "full_suite" in suites


@pytest.mark.asyncio
async def test_integration_full_workflow():
    """Integration test for complete orchestrator workflow"""
    orchestrator = PerformanceTestOrchestrator()
    
    # Run full suite
    results = await orchestrator.run_full_performance_suite()
    
    # Verify comprehensive results
    assert isinstance(results, PerformanceTestResults)
    assert results.suite_name == "full_suite"
    assert len(results.test_results) > 0
    assert results.total_duration_seconds > 0
    assert isinstance(results.summary_metrics, dict)
    assert isinstance(results.recommendations, list)
    
    # Verify all tests completed successfully (with default runners)
    completed_tests = [r for r in results.test_results if r.status == ExecutionStatus.COMPLETED]
    assert len(completed_tests) > 0
    
    # Verify metrics are present
    assert "total_tests" in results.summary_metrics
    assert "success_rate" in results.summary_metrics
    
    # Verify stored in history
    assert len(orchestrator.get_test_history()) == 1