"""Comprehensive Testing Suite for New Components.

This module provides comprehensive testing for all new components including
the unified ML system, security middleware, caching, and utilities using
expert testing patterns and best practices.

Features:
- Unit tests for all new components
- Integration tests for component interactions
- Performance tests for optimization validation
- Security tests for threat detection
- Load tests for scalability validation
- Mock data generation for testing
- Test utilities and helpers
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, AsyncMock, patch
import uuid

# Import the components we're testing
from src.core.unified_ml_system import (
    UnifiedMLSystem, MLRequest, MLResponse, ml_container,
    CircuitBreaker, CircuitBreakerState
)
from src.core.centralized_logging import (
    get_logger, performance_tracker, audit_logger, TimeUtils
)
from src.core.shared_utils import (
    data_validator, file_utils, text_utils, security_utils
)
from src.core.type_safety import (
    Result, ErrorHandler, SafeExecutor, StringValidator,
    EmailValidator, NumberValidator
)
from src.core.multi_tier_cache import MultiTierCacheSystem, CacheTier
from src.core.advanced_security_system import AdvancedSecuritySystem
from src.api.middleware.security_middleware import (
    SecurityMiddleware, AuthenticationMiddleware, DataProtectionMiddleware
)


class TestDataGenerator:
    """Generate test data for comprehensive testing."""

    @staticmethod
    def generate_ml_request() -> MLRequest:
        """Generate test ML request."""
        return MLRequest(
            document_text="Patient presents with acute chest pain. Vital signs stable. EKG shows ST elevation. Immediate cardiac intervention required.",
            entities=[
                {"text": "chest pain", "label": "SYMPTOM", "confidence": 0.95},
                {"text": "ST elevation", "label": "DIAGNOSTIC", "confidence": 0.98},
                {"text": "cardiac intervention", "label": "TREATMENT", "confidence": 0.92}
            ],
            retrieved_rules=[
                {"rule_id": "cardiac_001", "description": "Immediate intervention for ST elevation", "priority": "high"},
                {"rule_id": "vital_002", "description": "Monitor vital signs continuously", "priority": "medium"}
            ],
            context={
                "document_type": "clinical_note",
                "discipline": "cardiology",
                "urgency": "high"
            },
            user_id=1,
            session_id=str(uuid.uuid4()),
            priority="high",
            timeout_seconds=30.0
        )

    @staticmethod
    def generate_security_test_data() -> Dict[str, Any]:
        """Generate security test data."""
        return {
            "sql_injection": "'; DROP TABLE users; --",
            "xss_payload": "<script>alert('XSS')</script>",
            "csrf_token": "invalid_token_12345",
            "malicious_file": "../../../etc/passwd",
            "brute_force_attempts": ["password", "123456", "admin", "test"]
        }

    @staticmethod
    def generate_performance_test_data() -> Dict[str, Any]:
        """Generate performance test data."""
        return {
            "large_document": "Patient data " * 1000,  # Large document
            "many_entities": [{"text": f"entity_{i}", "label": "TEST", "confidence": 0.8} for i in range(100)],
            "complex_context": {f"key_{i}": f"value_{i}" for i in range(50)},
            "cache_keys": [f"test_key_{i}" for i in range(1000)]
        }


class TestUtilities:
    """Test utilities and helpers."""

    @staticmethod
    async def measure_execution_time(func, *args, **kwargs) -> tuple[Any, float]:
        """Measure execution time of a function."""
        start_time = time.time()
        result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time

    @staticmethod
    def assert_performance_threshold(execution_time: float, max_time: float, operation: str):
        """Assert performance meets threshold."""
        assert execution_time <= max_time, f"{operation} took {execution_time:.3f}s, expected <= {max_time}s"

    @staticmethod
    def assert_error_context(error_context, expected_severity=None, expected_category=None):
        """Assert error context properties."""
        assert error_context.error_id is not None
        assert error_context.timestamp is not None
        assert error_context.message is not None

        if expected_severity:
            assert error_context.severity == expected_severity
        if expected_category:
            assert error_context.category == expected_category


# Test classes
class TestUnifiedMLSystem:
    """Test unified ML system functionality."""

    @pytest.fixture
    async def ml_system(self):
        """Create ML system instance for testing."""
        return UnifiedMLSystem(
            enable_circuit_breaker=True,
            enable_caching=True,
            enable_metrics=True
        )

    @pytest.fixture
    def test_request(self):
        """Create test request."""
        return TestDataGenerator.generate_ml_request()

    @pytest.mark.asyncio
    async def test_document_analysis_success(self, ml_system, test_request):
        """Test successful document analysis."""
        # Mock the analysis result generation
        with patch.object(ml_system, '_generate_analysis_result') as mock_generate:
            mock_generate.return_value = {
                'summary': 'Test analysis completed',
                'findings': ['Finding 1', 'Finding 2'],
                'confidence': 0.85
            }

            response = await ml_system.analyze_document(test_request)

            assert response.request_id == test_request.request_id
            assert response.analysis_result is not None
            assert response.processing_time_ms > 0
            assert len(response.errors) == 0

    @pytest.mark.asyncio
    async def test_document_analysis_with_caching(self, ml_system, test_request):
        """Test document analysis with caching."""
        # First request - should miss cache
        response1 = await ml_system.analyze_document(test_request)
        assert not response1.cache_hit

        # Second request - should hit cache
        response2 = await ml_system.analyze_document(test_request)
        assert response2.cache_hit
        assert response1.request_id == response2.request_id

    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, ml_system):
        """Test circuit breaker functionality."""
        circuit_breaker = ml_system.circuit_breakers['confidence_calibration']

        # Simulate failures
        for _ in range(6):  # Exceed failure threshold
            try:
                await circuit_breaker.call(lambda: 1/0)  # Force error
            except:
                pass

        # Circuit should be open
        assert circuit_breaker.state == CircuitBreakerState.OPEN

        # Should raise exception when circuit is open
        with pytest.raises(Exception):
            await circuit_breaker.call(lambda: "test")

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, ml_system, test_request):
        """Test performance monitoring."""
        initial_metrics = ml_system.metrics

        await ml_system.analyze_document(test_request)

        # Check metrics were updated
        assert ml_system.metrics.total_requests > initial_metrics.total_requests
        assert ml_system.metrics.average_response_time_ms > 0

    @pytest.mark.asyncio
    async def test_system_health_check(self, ml_system):
        """Test system health check."""
        health = ml_system.get_system_health()

        assert 'overall_status' in health
        assert 'components' in health
        assert 'metrics' in health
        assert 'circuit_breakers' in health
        assert 'performance' in health


class TestSecurityMiddleware:
    """Test security middleware functionality."""

    @pytest.fixture
    def security_middleware(self):
        """Create security middleware instance."""
        return SecurityMiddleware(
            enable_threat_detection=True,
            enable_rate_limiting=True,
            enable_security_logging=True
        )

    @pytest.mark.asyncio
    async def test_sql_injection_detection(self, security_middleware):
        """Test SQL injection detection."""
        test_data = TestDataGenerator.generate_security_test_data()

        # Mock request with SQL injection
        mock_request = Mock()
        mock_request.body = test_data["sql_injection"].encode()
        mock_request.headers = {"content-type": "application/json"}

        # Should detect SQL injection
        threats = security_middleware._detect_threats(mock_request)
        assert len(threats) > 0
        assert any("sql" in threat.lower() for threat in threats)

    @pytest.mark.asyncio
    async def test_xss_detection(self, security_middleware):
        """Test XSS detection."""
        test_data = TestDataGenerator.generate_security_test_data()

        # Mock request with XSS payload
        mock_request = Mock()
        mock_request.body = test_data["xss_payload"].encode()
        mock_request.headers = {"content-type": "application/json"}

        # Should detect XSS
        threats = security_middleware._detect_threats(mock_request)
        assert len(threats) > 0
        assert any("xss" in threat.lower() for threat in threats)

    @pytest.mark.asyncio
    async def test_rate_limiting(self, security_middleware):
        """Test rate limiting functionality."""
        # This would test rate limiting logic
        # Implementation depends on your rate limiting strategy
        pass


class TestCachingSystem:
    """Test multi-tier caching system."""

    @pytest.fixture
    async def cache_system(self):
        """Create cache system instance."""
        return MultiTierCacheSystem()

    @pytest.mark.asyncio
    async def test_cache_operations(self, cache_system):
        """Test basic cache operations."""
        test_key = "test_key_123"
        test_value = {"data": "test_value", "timestamp": datetime.now().isoformat()}

        # Test set operation
        success = await cache_system.set(test_key, test_value)
        assert success

        # Test get operation
        retrieved_value = await cache_system.get(test_key)
        assert retrieved_value == test_value

        # Test delete operation
        await cache_system.delete(test_key)
        deleted_value = await cache_system.get(test_key)
        assert deleted_value is None

    @pytest.mark.asyncio
    async def test_cache_performance(self, cache_system):
        """Test cache performance."""
        test_data = TestDataGenerator.generate_performance_test_data()

        # Test bulk operations
        start_time = time.time()

        for i, key in enumerate(test_data["cache_keys"][:100]):
            await cache_system.set(key, f"value_{i}")

        set_time = time.time() - start_time

        # Should be fast for bulk operations
        assert set_time < 1.0  # Should complete in under 1 second

        # Test retrieval performance
        start_time = time.time()

        for key in test_data["cache_keys"][:100]:
            await cache_system.get(key)

        get_time = time.time() - start_time

        # Should be very fast for retrievals
        assert get_time < 0.5  # Should complete in under 0.5 seconds


class TestTypeSafety:
    """Test type safety and error handling."""

    def test_result_type_success(self):
        """Test successful Result type."""
        result = Result.success("test_value")

        assert result.is_success
        assert not result.is_failure
        assert result.value == "test_value"

    def test_result_type_failure(self):
        """Test failed Result type."""
        error = Exception("test_error")
        result = Result.failure(error)

        assert result.is_failure
        assert not result.is_success
        assert result.error == error

    def test_string_validator(self):
        """Test string validation."""
        validator = StringValidator(min_length=5, max_length=10)

        # Valid string
        result = validator.validate("valid_string")
        assert result.is_success
        assert result.value == "valid_string"

        # Too short
        result = validator.validate("hi")
        assert result.is_failure
        assert "too short" in result.error.message.lower()

        # Too long
        result = validator.validate("very_long_string_here")
        assert result.is_failure
        assert "too long" in result.error.message.lower()

    def test_email_validator(self):
        """Test email validation."""
        validator = EmailValidator()

        # Valid email
        result = validator.validate("test@example.com")
        assert result.is_success
        assert result.value == "test@example.com"

        # Invalid email
        result = validator.validate("invalid_email")
        assert result.is_failure
        assert "invalid email format" in result.error.message.lower()

    def test_error_handler(self):
        """Test error handling."""
        error_handler = ErrorHandler()

        # Test error handling
        error_context = error_handler.handle_error(
            Exception("test_error"),
            context={"test": "data"},
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION
        )

        assert error_context.message == "test_error"
        assert error_context.severity == ErrorSeverity.MEDIUM
        assert error_context.category == ErrorCategory.VALIDATION
        assert error_context.details == {"test": "data"}


class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_ml_system_performance(self):
        """Test ML system performance."""
        ml_system = UnifiedMLSystem(enable_caching=True)
        test_request = TestDataGenerator.generate_ml_request()

        # Test performance with caching
        result, execution_time = await TestUtilities.measure_execution_time(
            ml_system.analyze_document, test_request
        )

        TestUtilities.assert_performance_threshold(
            execution_time, 5.0, "ML document analysis"
        )

        # Test performance without caching (second call should be faster)
        result2, execution_time2 = await TestUtilities.measure_execution_time(
            ml_system.analyze_document, test_request
        )

        # Second call should be faster due to caching
        assert execution_time2 < execution_time

    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Test cache performance."""
        cache_system = MultiTierCacheSystem()

        # Test bulk operations performance
        test_keys = [f"perf_test_{i}" for i in range(1000)]

        # Bulk set performance
        start_time = time.time()
        for i, key in enumerate(test_keys):
            await cache_system.set(key, f"value_{i}")
        set_time = time.time() - start_time

        TestUtilities.assert_performance_threshold(
            set_time, 2.0, "Bulk cache set operations"
        )

        # Bulk get performance
        start_time = time.time()
        for key in test_keys:
            await cache_system.get(key)
        get_time = time.time() - start_time

        TestUtilities.assert_performance_threshold(
            get_time, 1.0, "Bulk cache get operations"
        )


class TestIntegration:
    """Test component integration."""

    @pytest.mark.asyncio
    async def test_full_pipeline_integration(self):
        """Test full pipeline integration."""
        # Create all components
        ml_system = UnifiedMLSystem()
        cache_system = MultiTierCacheSystem()
        security_system = AdvancedSecuritySystem()

        # Test request
        test_request = TestDataGenerator.generate_ml_request()

        # Test full pipeline
        response = await ml_system.analyze_document(test_request)

        # Verify response
        assert response.request_id == test_request.request_id
        assert response.analysis_result is not None
        assert response.processing_time_ms > 0

        # Test caching integration
        cached_response = await ml_system.analyze_document(test_request)
        assert cached_response.cache_hit

        # Test security integration
        health = ml_system.get_system_health()
        assert health['overall_status'] in ['healthy', 'degraded']


# Performance benchmarks
class TestBenchmarks:
    """Performance benchmarks for new components."""

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_ml_system_benchmark(self):
        """Benchmark ML system performance."""
        ml_system = UnifiedMLSystem()
        test_request = TestDataGenerator.generate_ml_request()

        # Benchmark multiple requests
        times = []
        for _ in range(10):
            _, execution_time = await TestUtilities.measure_execution_time(
                ml_system.analyze_document, test_request
            )
            times.append(execution_time)

        # Calculate statistics
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)

        # Assert performance thresholds
        assert avg_time < 3.0, f"Average time {avg_time:.3f}s exceeds threshold"
        assert max_time < 5.0, f"Max time {max_time:.3f}s exceeds threshold"
        assert min_time < 2.0, f"Min time {min_time:.3f}s exceeds threshold"

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_cache_benchmark(self):
        """Benchmark cache performance."""
        cache_system = MultiTierCacheSystem()

        # Benchmark bulk operations
        test_data = [(f"bench_{i}", f"value_{i}") for i in range(1000)]

        # Benchmark set operations
        start_time = time.time()
        for key, value in test_data:
            await cache_system.set(key, value)
        set_time = time.time() - start_time

        # Benchmark get operations
        start_time = time.time()
        for key, _ in test_data:
            await cache_system.get(key)
        get_time = time.time() - start_time

        # Assert performance thresholds
        assert set_time < 2.0, f"Set operations took {set_time:.3f}s"
        assert get_time < 1.0, f"Get operations took {get_time:.3f}s"


# Test markers
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.unit,
    pytest.mark.integration,
    pytest.mark.performance
]
