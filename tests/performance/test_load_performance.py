"""Performance and load testing for enhanced features."""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from src.api.main import app


class TestPerformanceLoad:
    """Performance and load testing suite."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_single_request_performance(self, client):
        """Test single request performance."""
        start_time = time.time()

        response = client.get("/health/")

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code in [200, 503]
        assert response_time < 1.0  # Should respond within 1 second

    def test_concurrent_requests_performance(self, client):
        """Test performance under concurrent load."""
        def make_request():
            return client.get("/health/")

        # Test with 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
            end_time = time.time()

        total_time = end_time - start_time

        # All requests should succeed
        for response in responses:
            assert response.status_code in [200, 503]

        # Should handle 10 concurrent requests in reasonable time
        assert total_time < 5.0
        assert len(responses) == 10

    def test_middleware_performance_impact(self, client):
        """Test middleware doesn't significantly impact performance."""
        # Test without middleware (basic request)
        start_time = time.time()
        response = client.get("/health/live")
        basic_time = time.time() - start_time

        # Test with middleware (more complex request)
        start_time = time.time()
        response = client.post("/auth/login", json={
            "username": "test",
            "password": "test"
        })
        middleware_time = time.time() - start_time

        # Middleware should not add more than 100ms overhead
        overhead = middleware_time - basic_time
        assert overhead < 0.1

    def test_metrics_collection_performance(self, client):
        """Test metrics collection doesn't impact performance."""
        # Make several requests to generate metrics
        start_time = time.time()

        for _ in range(5):
            client.get("/health/")

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete quickly even with metrics collection
        assert total_time < 2.0

        # Check metrics endpoint performance
        start_time = time.time()
        response = client.get("/metrics")
        metrics_time = time.time() - start_time

        assert response.status_code == 200
        assert metrics_time < 0.5  # Metrics should be fast to retrieve

    def test_error_handling_performance(self, client):
        """Test error handling doesn't impact performance."""
        # Test error response performance
        start_time = time.time()
        response = client.post("/analysis/start", json={"invalid": "data"})
        error_time = time.time() - start_time

        assert response.status_code in [400, 422]
        assert error_time < 0.5  # Error handling should be fast

    def test_memory_usage_under_load(self, client):
        """Test memory usage doesn't grow excessively under load."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make many requests
        for _ in range(50):
            client.get("/health/")

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 10MB)
        assert memory_increase < 10 * 1024 * 1024

    def test_database_performance_under_load(self, client):
        """Test database performance under load."""
        # Test database health check performance
        start_time = time.time()
        response = client.get("/health/detailed")
        db_time = time.time() - start_time

        assert response.status_code in [200, 503]
        assert db_time < 2.0  # Database operations should be fast

    def test_websocket_performance(self, client):
        """Test WebSocket performance (basic connection test)."""
        # Test WebSocket endpoint response time
        start_time = time.time()
        response = client.get("/ws/analysis/test-task")
        ws_time = time.time() - start_time

        assert response.status_code == 426  # Upgrade Required
        assert ws_time < 0.5  # WebSocket setup should be fast

    def test_api_documentation_performance(self, client):
        """Test API documentation performance."""
        # Test OpenAPI schema generation
        start_time = time.time()
        response = client.get("/openapi.json")
        schema_time = time.time() - start_time

        assert response.status_code == 200
        assert schema_time < 1.0  # Schema generation should be fast

        # Test Swagger UI
        start_time = time.time()
        response = client.get("/docs")
        ui_time = time.time() - start_time

        assert response.status_code == 200
        assert ui_time < 2.0  # UI should load reasonably fast

    def test_security_headers_performance(self, client):
        """Test security headers don't impact performance."""
        # Test multiple requests to ensure headers are added consistently
        start_time = time.time()

        for _ in range(10):
            response = client.get("/health/")
            assert "X-Content-Type-Options" in response.headers

        end_time = time.time()
        total_time = end_time - start_time

        # Security headers should not significantly impact performance
        assert total_time < 2.0

    def test_rate_limiting_performance(self, client):
        """Test rate limiting performance."""
        # Make requests quickly to test rate limiting
        start_time = time.time()

        responses = []
        for _ in range(20):
            response = client.get("/health/")
            responses.append(response)

        end_time = time.time()
        total_time = end_time - start_time

        # Should handle rate limiting efficiently
        assert total_time < 3.0

        # Most requests should succeed (health endpoint may not be rate limited)
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 15  # Most should succeed


class TestStressTesting:
    """Stress testing for enhanced features."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_high_concurrency_stress(self, client):
        """Test system under high concurrency."""
        def make_request():
            return client.get("/health/")

        # Test with 50 concurrent requests
        with ThreadPoolExecutor(max_workers=50) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(50)]
            responses = [future.result() for future in futures]
            end_time = time.time()

        total_time = end_time - start_time

        # Should handle high concurrency
        assert total_time < 10.0
        assert len(responses) == 50

        # Most requests should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 40  # At least 80% should succeed

    def test_sustained_load_stress(self, client):
        """Test system under sustained load."""
        # Make requests continuously for 10 seconds
        start_time = time.time()
        request_count = 0

        while time.time() - start_time < 10:
            response = client.get("/health/")
            request_count += 1

            # Ensure we don't overwhelm the system
            time.sleep(0.1)

        # Should handle sustained load
        assert request_count >= 50  # Should make at least 50 requests
        assert request_count <= 200  # But not too many

    def test_memory_leak_stress(self, client):
        """Test for memory leaks under stress."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make many requests to test for memory leaks
        for _ in range(100):
            client.get("/health/")
            client.get("/metrics")

        # Force garbage collection
        import gc
        gc.collect()

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable
        assert memory_increase < 50 * 1024 * 1024  # Less than 50MB

    def test_error_recovery_stress(self, client):
        """Test error recovery under stress."""
        # Make many requests that will cause errors
        error_count = 0
        success_count = 0

        for _ in range(50):
            # Mix of valid and invalid requests
            if _ % 3 == 0:
                response = client.post("/analysis/start", json={"invalid": "data"})
                if response.status_code >= 400:
                    error_count += 1
            else:
                response = client.get("/health/")
                if response.status_code == 200:
                    success_count += 1

        # System should handle errors gracefully
        assert error_count > 0  # Should have some errors
        assert success_count > 0  # Should have some successes
        assert error_count + success_count == 50  # All requests processed
