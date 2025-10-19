"""Comprehensive unit tests for input validation middleware."""

import json
import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from src.api.middleware.input_validation import InputValidationMiddleware


class TestInputValidationMiddleware:
    """Test suite for InputValidationMiddleware."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()

        @app.post("/test")
        async def test_endpoint(request: Request):
            return {"message": "success"}

        @app.get("/test-get")
        async def test_get():
            return {"message": "success"}

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client with middleware."""
        app.add_middleware(InputValidationMiddleware, max_request_size=1024)
        return TestClient(app)

    def test_valid_json_request(self, client):
        """Test valid JSON request passes validation."""
        response = client.post("/test", json={"name": "test", "value": 123})
        assert response.status_code == 200
        assert response.json() == {"message": "success"}

    def test_sql_injection_prevention(self, client):
        """Test SQL injection attempts are blocked."""
        malicious_payload = {
            "name": "'; DROP TABLE users; --",
            "query": "SELECT * FROM users WHERE id = 1 OR 1=1"
        }

        response = client.post("/test", json=malicious_payload)
        assert response.status_code == 400
        assert "Invalid request data" in response.json()["error"]

    def test_xss_prevention(self, client):
        """Test XSS attempts are blocked."""
        malicious_payload = {
            "content": "<script>alert('xss')</script>",
            "description": "javascript:alert('xss')"
        }

        response = client.post("/test", json=malicious_payload)
        assert response.status_code == 400
        assert "Invalid request data" in response.json()["error"]

    def test_request_size_limit(self, client):
        """Test request size limit enforcement."""
        large_data = {"data": "x" * 2000}  # Exceeds 1024 byte limit

        response = client.post("/test", json=large_data)
        assert response.status_code == 413
        assert "Request too large" in response.json()["error"]

    def test_invalid_content_type(self, client):
        """Test invalid content type rejection."""
        response = client.post(
            "/test",
            data="invalid data",
            headers={"Content-Type": "application/invalid"}
        )
        assert response.status_code == 415
        assert "Unsupported content type" in response.json()["error"]

    def test_query_parameter_sanitization(self, client):
        """Test query parameter sanitization."""
        response = client.get("/test-get?name=<script>alert('xss')</script>")
        assert response.status_code == 400
        assert "Invalid query parameters" in response.json()["error"]

    def test_valid_query_parameters(self, client):
        """Test valid query parameters pass."""
        response = client.get("/test-get?name=test&value=123")
        assert response.status_code == 200

    def test_request_id_generation(self, client):
        """Test request ID is generated and added to response."""
        response = client.post("/test", json={"test": "data"})
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 8

    def test_security_headers_added(self, client):
        """Test security headers are added to responses."""
        response = client.get("/test-get")
        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    def test_middleware_error_handling(self, client):
        """Test middleware handles internal errors gracefully."""
        with patch.object(InputValidationMiddleware, '_sanitize_json_data', side_effect=Exception("Test error")):
            response = client.post("/test", json={"test": "data"})
            assert response.status_code == 500
            assert "Internal validation error" in response.json()["error"]

    def test_empty_request_body(self, client):
        """Test empty request body handling."""
        response = client.post("/test", json={})
        assert response.status_code == 200

    def test_large_field_value(self, client):
        """Test large field value truncation."""
        large_field = "x" * 15000  # Exceeds 10KB field limit
        response = client.post("/test", json={"field": large_field})
        assert response.status_code == 200  # Should be truncated, not rejected

    def test_control_character_removal(self, client):
        """Test control characters are removed."""
        payload = {"text": "test\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x1f\x7f"}
        response = client.post("/test", json=payload)
        assert response.status_code == 200
        # The middleware should have cleaned the text

    def test_multipart_form_data(self, client):
        """Test multipart form data is accepted."""
        files = {"file": ("test.txt", "test content", "text/plain")}
        response = client.post("/test", files=files)
        assert response.status_code == 200

    def test_url_encoded_data(self, client):
        """Test URL encoded data is accepted."""
        data = {"name": "test", "value": "123"}
        response = client.post("/test", data=data)
        assert response.status_code == 200
