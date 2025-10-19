"""Comprehensive integration tests for enhanced features."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.api.main import app
from src.database import get_db, Base


class TestEnhancedFeaturesIntegration:
    """Integration tests for enhanced features."""

    @pytest.fixture
    def test_db(self):
        """Create test database."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        yield TestingSessionLocal
        app.dependency_overrides.clear()

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_endpoints_integration(self, client):
        """Test health endpoints work together."""
        # Test basic health
        response = client.get("/health/")
        assert response.status_code in [200, 503]  # May be unhealthy in test

        # Test detailed health
        response = client.get("/health/detailed")
        assert response.status_code in [200, 503]

        # Test readiness
        response = client.get("/health/ready")
        assert response.status_code in [200, 503]

        # Test liveness
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    def test_metrics_endpoint_integration(self, client):
        """Test metrics endpoint integration."""
        response = client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "uptime_seconds" in data
        assert "requests" in data
        assert "system" in data
        assert "cache" in data

    def test_api_documentation_integration(self, client):
        """Test API documentation endpoints."""
        # Test custom docs
        response = client.get("/docs/custom")
        assert response.status_code == 200

        # Test API status
        response = client.get("/api/status")
        assert response.status_code == 200
        assert response.json()["status"] == "operational"

    def test_middleware_integration(self, client):
        """Test middleware integration with API endpoints."""
        # Test request with middleware
        response = client.post("/auth/login", json={
            "username": "test",
            "password": "test"
        })

        # Should have security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers

        # Should have request ID
        assert "X-Request-ID" in response.headers

    def test_error_handling_integration(self, client):
        """Test error handling integration."""
        # Test validation error
        response = client.post("/analysis/start", json={
            "invalid": "data"
        })

        assert response.status_code in [400, 422]  # Validation error
        data = response.json()
        assert "error" in data
        assert "error_id" in data
        assert "timestamp" in data

    def test_websocket_integration(self, client):
        """Test WebSocket integration."""
        # Test WebSocket connection (would need proper WebSocket client)
        # For now, just test the endpoint exists
        response = client.get("/ws/analysis/test-task")
        assert response.status_code == 426  # Upgrade Required for WebSocket

    def test_security_headers_integration(self, client):
        """Test security headers are applied to all responses."""
        endpoints = [
            "/",
            "/health/",
            "/docs",
            "/openapi.json"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                assert "X-Content-Type-Options" in response.headers
                assert "X-Frame-Options" in response.headers
                assert "X-XSS-Protection" in response.headers

    def test_cors_integration(self, client):
        """Test CORS headers are properly set."""
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        })

        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers

    def test_rate_limiting_integration(self, client):
        """Test rate limiting integration."""
        # Make multiple requests quickly
        for _ in range(5):
            response = client.get("/health/")
            # Should not be rate limited for health checks

        # Test with a more sensitive endpoint
        for _ in range(5):
            response = client.post("/auth/login", json={
                "username": "test",
                "password": "test"
            })
            # May be rate limited after several attempts

    def test_database_integration(self, client, test_db):
        """Test database integration with enhanced features."""
        # Test database operations work with enhanced error handling
        response = client.get("/users/")
        assert response.status_code in [200, 401]  # May require auth

        # Test database health check
        response = client.get("/health/detailed")
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "checks" in data
            assert "database" in data["checks"]


class TestPerformanceIntegration:
    """Integration tests for performance features."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_metrics_collection_integration(self, client):
        """Test metrics are collected during API calls."""
        # Make several requests
        for _ in range(3):
            response = client.get("/health/")

        # Check metrics
        response = client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        assert data["requests"]["total"] >= 3

    def test_performance_monitoring_integration(self, client):
        """Test performance monitoring works end-to-end."""
        # Make a request that should be tracked
        response = client.post("/auth/login", json={
            "username": "test",
            "password": "test"
        })

        # Check that metrics were updated
        response = client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        assert data["requests"]["total"] >= 1

    def test_system_metrics_integration(self, client):
        """Test system metrics are collected."""
        response = client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "system" in data
        assert "memory_usage_mb" in data["system"]
        assert "cpu_usage_percent" in data["system"]


class TestSecurityIntegration:
    """Integration tests for security features."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_input_validation_integration(self, client):
        """Test input validation works with real endpoints."""
        # Test SQL injection attempt
        response = client.post("/analysis/start", json={
            "document_name": "'; DROP TABLE users; --",
            "rubric": "test"
        })

        # Should be blocked by input validation
        assert response.status_code == 400

    def test_xss_protection_integration(self, client):
        """Test XSS protection works with real endpoints."""
        # Test XSS attempt
        response = client.post("/analysis/start", json={
            "document_name": "<script>alert('xss')</script>",
            "rubric": "test"
        })

        # Should be blocked by input validation
        assert response.status_code == 400

    def test_security_headers_integration(self, client):
        """Test security headers are applied consistently."""
        endpoints = [
            "/",
            "/health/",
            "/docs",
            "/openapi.json",
            "/metrics"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                headers = response.headers
                assert headers.get("X-Content-Type-Options") == "nosniff"
                assert headers.get("X-Frame-Options") == "DENY"
                assert headers.get("X-XSS-Protection") == "1; mode=block"

    def test_cors_security_integration(self, client):
        """Test CORS is properly configured for security."""
        # Test with disallowed origin
        response = client.get("/", headers={
            "Origin": "https://malicious-site.com"
        })

        # Should not have CORS headers for disallowed origin
        assert "Access-Control-Allow-Origin" not in response.headers

        # Test with allowed origin
        response = client.get("/", headers={
            "Origin": "http://127.0.0.1:3000"
        })

        # Should have CORS headers for allowed origin
        assert "Access-Control-Allow-Origin" in response.headers
