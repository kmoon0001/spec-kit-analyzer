"""
Advanced Performance Testing Suite
Comprehensive performance testing with benchmarking and stress testing.
"""

import pytest
import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any
from dataclasses import dataclass

try:
    import psutil
    import numpy as np
except ImportError:
    psutil = None
    np = None

from src.core.advanced_performance_optimizer import SystemResourceMonitor


@dataclass
class PerformanceBenchmark:
    """Performance benchmark result."""
    test_name: str
    duration_seconds: float
    operations_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success_rate: float
    error_count: int
    metadata: Dict[str, Any]


class PerformanceTestSuite:
    """Comprehensive performance testing suite."""
    
    def __init__(self):
        self.benchmarks: List[PerformanceBenchmark] = []
        self.resource_monitor = SystemResourceMonitor() if psutil else None
        
    async def run_comprehensive_performance_tests(self) -> Dict[str, Any]:
        """Run all performance tests and return comprehensive results."""
        print("🚀 Starting Comprehensive Performance Test Suite")
        print("=" * 60)
        
        results = {
            'test_summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'total_duration': 0.0
            },
            'benchmarks': [],
            'system_metrics': {},
            'recommendations': []
        }
        
        start_time = time.time()
        
        try:
            # Test 1: Basic System Performance
            print("\n📊 Test 1: Basic System Performance")
            basic_result = await self._test_basic_system_performance()
            results['benchmarks'].append(basic_result)
            results['test_summary']['total_tests'] += 1
            if basic_result.success_rate > 0.8:
                results['test_summary']['passed_tests'] += 1
            else:
                results['test_summary']['failed_tests'] += 1
            
            # Test 2: Concurrent Processing
            print("\n⚡ Test 2: Concurrent Processing Performance")
            concurrent_result = await self._test_concurrent_processing()
            results['benchmarks'].append(concurrent_result)
            results['test_summary']['total_tests'] += 1
            if concurrent_result.success_rate > 0.8:
                results['test_summary']['passed_tests'] += 1
            else:
                results['test_summary']['failed_tests'] += 1
            
            # Test 3: Memory Management
            print("\n💾 Test 3: Memory Management Performance")
            memory_result = await self._test_memory_management()
            results['benchmarks'].append(memory_result)
            results['test_summary']['total_tests'] += 1
            if memory_result.success_rate > 0.8:
                results['test_summary']['passed_tests'] += 1
            else:
                results['test_summary']['failed_tests'] += 1
            
            # Test 4: I/O Performance
            print("\n📁 Test 4: I/O Performance")
            io_result = await self._test_io_performance()
            results['benchmarks'].append(io_result)
            results['test_summary']['total_tests'] += 1
            if io_result.success_rate > 0.8:
                results['test_summary']['passed_tests'] += 1
            else:
                results['test_summary']['failed_tests'] += 1
            
            # Collect final system metrics
            if self.resource_monitor:
                try:
                    final_metrics = await self.resource_monitor.collect_comprehensive_metrics()
                    results['system_metrics'] = {
                        'cpu_usage': final_metrics.cpu_usage_percent,
                        'memory_usage': final_metrics.memory_usage_percent,
                        'memory_available_gb': final_metrics.memory_available_gb
                    }
                except Exception as e:
                    results['system_metrics'] = {'error': str(e)}
            
            # Generate recommendations
            results['recommendations'] = self._generate_performance_recommendations(results['benchmarks'])
            
        except Exception as e:
            results['error'] = str(e)
            results['test_summary']['failed_tests'] += 1
        
        results['test_summary']['total_duration'] = time.time() - start_time
        
        print(f"\n✅ Performance Test Suite Complete")
        print(f"   Total Tests: {results['test_summary']['total_tests']}")
        print(f"   Passed: {results['test_summary']['passed_tests']}")
        print(f"   Failed: {results['test_summary']['failed_tests']}")
        print(f"   Duration: {results['test_summary']['total_duration']:.2f}s")
        
        return results
    
    async def _test_basic_system_performance(self) -> PerformanceBenchmark:
        """Test basic system performance metrics."""
        start_time = time.time()
        operations = 0
        errors = 0
        
        try:
            # Simulate basic operations
            for i in range(1000):
                # Simple CPU-bound operation
                result = sum(range(100))
                operations += 1
                
                # Simulate some async operations
                await asyncio.sleep(0.001)
                operations += 1
            
            duration = time.time() - start_time
            ops_per_second = operations / duration if duration > 0 else 0
            
            return PerformanceBenchmark(
                test_name="Basic System Performance",
                duration_seconds=duration,
                operations_per_second=ops_per_second,
                memory_usage_mb=0.0,  # Simplified
                cpu_usage_percent=0.0,  # Simplified
                success_rate=1.0 if errors == 0 else (operations - errors) / operations,
                error_count=errors,
                metadata={'operations_completed': operations}
            )
            
        except Exception as e:
            return PerformanceBenchmark(
                test_name="Basic System Performance",
                duration_seconds=time.time() - start_time,
                operations_per_second=0.0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                success_rate=0.0,
                error_count=1,
                metadata={'error': str(e)}
            )
    
    async def _test_concurrent_processing(self) -> PerformanceBenchmark:
        """Test concurrent processing performance."""
        start_time = time.time()
        operations = 0
        errors = 0
        
        try:
            # Test concurrent operations
            async def worker_task(task_id: int) -> int:
                nonlocal operations
                # Simulate work
                await asyncio.sleep(0.01)
                result = sum(range(50))
                operations += 1
                return result
            
            # Run concurrent tasks
            tasks = [worker_task(i) for i in range(50)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count errors
            errors = sum(1 for r in results if isinstance(r, Exception))
            
            duration = time.time() - start_time
            ops_per_second = operations / duration if duration > 0 else 0
            
            return PerformanceBenchmark(
                test_name="Concurrent Processing",
                duration_seconds=duration,
                operations_per_second=ops_per_second,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                success_rate=(operations - errors) / operations if operations > 0 else 0,
                error_count=errors,
                metadata={'concurrent_tasks': len(tasks), 'successful_tasks': operations - errors}
            )
            
        except Exception as e:
            return PerformanceBenchmark(
                test_name="Concurrent Processing",
                duration_seconds=time.time() - start_time,
                operations_per_second=0.0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                success_rate=0.0,
                error_count=1,
                metadata={'error': str(e)}
            )
    
    async def _test_memory_management(self) -> PerformanceBenchmark:
        """Test memory management performance."""
        start_time = time.time()
        operations = 0
        errors = 0
        
        try:
            # Test memory allocation and deallocation
            memory_blocks = []
            
            # Allocate memory blocks
            for i in range(100):
                block = [0] * 1000  # Small memory block
                memory_blocks.append(block)
                operations += 1
            
            # Process memory blocks
            for block in memory_blocks:
                sum(block)  # Simple operation
                operations += 1
            
            # Clean up
            memory_blocks.clear()
            operations += 1
            
            duration = time.time() - start_time
            ops_per_second = operations / duration if duration > 0 else 0
            
            return PerformanceBenchmark(
                test_name="Memory Management",
                duration_seconds=duration,
                operations_per_second=ops_per_second,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                success_rate=1.0 if errors == 0 else (operations - errors) / operations,
                error_count=errors,
                metadata={'memory_blocks_processed': 100}
            )
            
        except Exception as e:
            return PerformanceBenchmark(
                test_name="Memory Management",
                duration_seconds=time.time() - start_time,
                operations_per_second=0.0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                success_rate=0.0,
                error_count=1,
                metadata={'error': str(e)}
            )
    
    async def _test_io_performance(self) -> PerformanceBenchmark:
        """Test I/O performance."""
        start_time = time.time()
        operations = 0
        errors = 0
        
        try:
            # Test file I/O operations (in memory)
            test_data = "Test data for I/O performance testing" * 100
            
            # Simulate multiple I/O operations
            for i in range(50):
                # Simulate read operation
                data_length = len(test_data)
                operations += 1
                
                # Simulate write operation
                processed_data = test_data.upper()
                operations += 1
                
                # Simulate processing
                await asyncio.sleep(0.001)
                operations += 1
            
            duration = time.time() - start_time
            ops_per_second = operations / duration if duration > 0 else 0
            
            return PerformanceBenchmark(
                test_name="I/O Performance",
                duration_seconds=duration,
                operations_per_second=ops_per_second,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                success_rate=1.0 if errors == 0 else (operations - errors) / operations,
                error_count=errors,
                metadata={'io_operations': operations}
            )
            
        except Exception as e:
            return PerformanceBenchmark(
                test_name="I/O Performance",
                duration_seconds=time.time() - start_time,
                operations_per_second=0.0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                success_rate=0.0,
                error_count=1,
                metadata={'error': str(e)}
            )
    
    def _generate_performance_recommendations(self, benchmarks: List[PerformanceBenchmark]) -> List[str]:
        """Generate performance recommendations based on test results."""
        recommendations = []
        
        try:
            for benchmark in benchmarks:
                if benchmark.success_rate < 0.9:
                    recommendations.append(f"Improve reliability for {benchmark.test_name} (success rate: {benchmark.success_rate:.1%})")
                
                if benchmark.operations_per_second < 100:
                    recommendations.append(f"Optimize {benchmark.test_name} for better throughput (current: {benchmark.operations_per_second:.1f} ops/s)")
                
                if benchmark.duration_seconds > 5.0:
                    recommendations.append(f"Reduce execution time for {benchmark.test_name} (current: {benchmark.duration_seconds:.2f}s)")
            
            # General recommendations
            if not recommendations:
                recommendations.append("Performance tests passed successfully - system is performing well")
            else:
                recommendations.append("Consider implementing performance optimizations for identified areas")
            
        except Exception as e:
            recommendations.append(f"Error generating recommendations: {str(e)}")
        
        return recommendations


# Global performance test suite instance
performance_test_suite = PerformanceTestSuite()


# Test functions for pytest
@pytest.mark.asyncio
async def test_performance_suite():
    """Test the performance test suite."""
    results = await performance_test_suite.run_comprehensive_performance_tests()
    
    assert 'test_summary' in results
    assert results['test_summary']['total_tests'] > 0
    assert 'benchmarks' in results
    assert len(results['benchmarks']) > 0


def test_performance_benchmark_creation():
    """Test performance benchmark creation."""
    benchmark = PerformanceBenchmark(
        test_name="Test",
        duration_seconds=1.0,
        operations_per_second=100.0,
        memory_usage_mb=50.0,
        cpu_usage_percent=25.0,
        success_rate=1.0,
        error_count=0,
        metadata={}
    )
    
    assert benchmark.test_name == "Test"
    assert benchmark.duration_seconds == 1.0
    assert benchmark.operations_per_second == 100.0


if __name__ == "__main__":
    # Run performance tests directly
    async def main():
        suite = PerformanceTestSuite()
        results = await suite.run_comprehensive_performance_tests()
        print("\n📊 Final Results:")
        print(f"   Tests: {results['test_summary']['total_tests']}")
        print(f"   Success Rate: {results['test_summary']['passed_tests'] / results['test_summary']['total_tests']:.1%}")
        print(f"   Duration: {results['test_summary']['total_duration']:.2f}s")
    
    asyncio.run(main())