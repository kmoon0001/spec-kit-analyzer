"""Simple test configuration without full app dependencies."""

import pytest
import asyncio
from unittest.mock import Mock, patch


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing."""
    with patch('src.core.analysis_service.AnalysisService') as mock_service:
        mock_instance = Mock()
        mock_instance.use_mocks = True
        mock_instance.analyze_document.return_value = {
            "compliance_score": 85.5,
            "findings": [
                {
                    "rule_id": "test_rule",
                    "risk": "Medium",
                    "message": "Test finding",
                    "confidence": 0.8
                }
            ]
        }
        mock_service.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_metrics_collector():
    """Mock metrics collector for testing."""
    with patch('src.core.performance_metrics_collector.metrics_collector') as mock_collector:
        mock_collector.get_metrics_summary.return_value = {
            "uptime_seconds": 3600,
            "requests": {
                "total": 100,
                "avg_duration_ms": 150.5,
                "error_count": 5,
                "error_rate_percent": 5.0
            },
            "system": {
                "memory_usage_mb": 512.0,
                "cpu_usage_percent": 25.5
            }
        }
        yield mock_collector


@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "use_ai_mocks": True,
        "database_url": "sqlite:///:memory:",
        "log_level": "DEBUG",
        "max_request_size": 1024,
        "rate_limit": "100/minute"
    }


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    import os
    with patch.dict(os.environ, {
        "SECRET_KEY": "test-secret-key",
        "ENVIRONMENT": "testing",
        "USE_AI_MOCKS": "true",
        "LOG_LEVEL": "DEBUG"
    }):
        yield


# Test markers
pytestmark = [
    pytest.mark.asyncio,
]
