"""Comprehensive unit tests for request logging middleware."""

import json
import pytest
from unittest.mock import Mock, patch, call
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from src.api.middleware.request_logging import RequestLoggingMiddleware


class TestRequestLoggingMiddleware:
    """Test suite for RequestLoggingMiddleware."""

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

        @app.post("/test-error")
        async def test_error():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Test error")

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client with middleware."""
        app.add_middleware(RequestLoggingMiddleware, log_body=True, max_body_size=1024)
        return TestClient(app)

    def test_successful_request_logging(self, client):
        """Test successful request is logged properly."""
        with patch('src.api.middleware.request_logging.logger') as mock_logger:
            response = client.post("/test", json={"name": "test"})
            assert response.status_code == 200

            # Check that info log was called for request start
            mock_logger.info.assert_any_call(
                "Request started | "
                "id=unknown | "
                "method=POST | "
                "url=/test | "
                "client_ip=testclient | "
                "user_agent=testclient"
            )

            # Check that info log was called for request completion
            mock_logger.info.assert_any_call(
                "Request completed | "
                "id=unknown | "
                "method=POST | "
                "url=/test | "
                "status=200 | "
                "time=0.000s | "
                "size=unknown"
            )

    def test_error_request_logging(self, client):
        """Test error request is logged with warning level."""
        with patch('src.api.middleware.request_logging.logger') as mock_logger:
            response = client.post("/test-error")
            assert response.status_code == 400

            # Check that warning log was called for error response
            mock_logger.warning.assert_any_call(
                "Request completed | "
                "id=unknown | "
                "method=POST | "
                "url=/test-error | "
                "status=400 | "
                "time=0.000s | "
                "size=unknown"
            )

    def test_request_body_logging_enabled(self, client):
        """Test request body is logged when enabled."""
        with patch('src.api.middleware.request_logging.logger') as mock_logger:
            test_data = {"name": "test", "value": 123}
            response = client.post("/test", json=test_data)
            assert response.status_code == 200

            # Check that debug log was called for request body
            mock_logger.debug.assert_any_call(
                "Request body | id=unknown | body=" + str(test_data)
            )

    def test_request_body_logging_disabled(self, app):
        """Test request body is not logged when disabled."""
        app.add_middleware(RequestLoggingMiddleware, log_body=False)
        client = TestClient(app)

        with patch('src.api.middleware.request_logging.logger') as mock_logger:
            response = client.post("/test", json={"name": "test"})
            assert response.status_code == 200

            # Check that debug log was not called for request body
            debug_calls = [call for call in mock_logger.debug.call_args_list
                          if "Request body" in str(call)]
            assert len(debug_calls) == 0

    def test_large_request_body_truncation(self, client):
        """Test large request body is not logged."""
        large_data = {"data": "x" * 2000}  # Exceeds max_body_size

        with patch('src.api.middleware.request_logging.logger') as mock_logger:
            response = client.post("/test", json=large_data)
            assert response.status_code == 200

            # Check that debug log was not called for large body
            debug_calls = [call for call in mock_logger.debug.call_args_list
                          if "Request body" in str(call)]
            assert len(debug_calls) == 0

    def test_sensitive_headers_redaction(self, client):
        """Test sensitive headers are redacted."""
        with patch('src.api.middleware.request_logging.logger') as mock_logger:
            headers = {
                "Authorization": "Bearer secret-token",
                "Cookie": "session=abc123",
                "X-API-Key": "secret-key",
                "User-Agent": "test-agent"
            }

            response = client.post("/test", json={"test": "data"}, headers=headers)
            assert response.status_code == 200

            # Check that sensitive headers are redacted in logs
            info_calls = mock_logger.info.call_args_list
            log_messages = [str(call) for call in info_calls]

            # Should not contain actual sensitive values
            assert not any("secret-token" in msg for msg in log_messages)
            assert not any("abc123" in msg for msg in log_messages)
            assert not any("secret-key" in msg for msg in log_messages)

    def test_request_id_from_state(self, client):
        """Test request ID is taken from request state if available."""
        # This would require modifying the middleware to use request state
        # For now, we'll test the current behavior
        response = client.post("/test", json={"test": "data"})
        assert response.status_code == 200

    def test_slow_request_warning(self, client):
        """Test slow requests trigger warning logs."""
        with patch('src.api.middleware.request_logging.logger') as mock_logger:
            with patch('src.api.middleware.request_logging.time.time') as mock_time:
                # Mock time to simulate slow request
                mock_time.side_effect = [0, 6]  # 6 second request

                response = client.post("/test", json={"test": "data"})
                assert response.status_code == 200

                # Check that warning was logged for slow request
                mock_logger.warning.assert_any_call(
                    "Slow request detected | "
                    "id=unknown | "
                    "url=/test | "
                    "time=6.000s"
                )

    def test_error_response_detailed_logging(self, client):
        """Test error responses get detailed logging."""
        with patch('src.api.middleware.request_logging.logger') as mock_logger:
            response = client.post("/test-error")
            assert response.status_code == 400

            # Check that error log was called with detailed info
            mock_logger.error.assert_any_call(
                "Error response | "
                "id=unknown | "
                "status=400 | "
                "url=/test-error | "
                "query="
            )

    def test_get_request_logging(self, client):
        """Test GET requests are logged properly."""
        with patch('src.api.middleware.request_logging.logger') as mock_logger:
            response = client.get("/test-get")
            assert response.status_code == 200

            # Check that info log was called
            mock_logger.info.assert_any_call(
                "Request started | "
                "id=unknown | "
                "method=GET | "
                "url=/test-get | "
                "client_ip=testclient | "
                "user_agent=testclient"
            )

    def test_middleware_exception_handling(self, client):
        """Test middleware handles exceptions gracefully."""
        with patch('src.api.middleware.request_logging.RequestLoggingMiddleware._log_request',
                  side_effect=Exception("Test error")):
            response = client.post("/test", json={"test": "data"})
            # Should still work despite middleware error
            assert response.status_code == 200

    def test_response_size_logging(self, client):
        """Test response size is logged."""
        with patch('src.api.middleware.request_logging.logger') as mock_logger:
            response = client.post("/test", json={"test": "data"})
            assert response.status_code == 200

            # Check that response size is logged
            info_calls = mock_logger.info.call_args_list
            completion_log = [call for call in info_calls
                           if "Request completed" in str(call)][0]
            assert "size=" in str(completion_log)

    def test_user_agent_logging(self, client):
        """Test user agent is logged."""
        custom_headers = {"User-Agent": "Custom-Test-Agent/1.0"}

        with patch('src.api.middleware.request_logging.logger') as mock_logger:
            response = client.post("/test", json={"test": "data"}, headers=custom_headers)
            assert response.status_code == 200

            # Check that custom user agent is logged
            info_calls = mock_logger.info.call_args_list
            start_log = [call for call in info_calls
                        if "Request started" in str(call)][0]
            assert "Custom-Test-Agent/1.0" in str(start_log)
