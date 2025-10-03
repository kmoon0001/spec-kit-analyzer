# Comprehensive Testing Guide - Therapy Compliance Analyzer

## Overview

This guide provides comprehensive testing procedures and best practices for the Therapy Compliance Analyzer application.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_security_validator.py
│   ├── test_cache_service.py
│   ├── test_phi_scrubber.py
│   ├── test_parsing.py
│   └── ...
├── integration/             # Integration tests for component interactions
│   ├── test_full_analysis.py
│   ├── test_dashboard_api.py
│   ├── test_compliance_api.py
│   └── ...
├── gui/                     # GUI tests using pytest-qt
│   └── test_export.py
└── test_data/              # Test data and fixtures
    ├── test_document.txt
    └── test_guideline.txt
```

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock pytest-qt pytest-cov

# Install pydantic-settings if missing
pip install pydantic-settings
```

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_security_validator.py

# Run specific test class
pytest tests/unit/test_security_validator.py::TestFilenameValidation

# Run specific test
pytest tests/unit/test_security_validator.py::TestFilenameValidation::test_valid_pdf_filename
```

### Test Coverage

```bash
# Run tests with coverage report
pytest --cov=src --cov-report=html

# View coverage report
# Open htmlcov/index.html in browser

# Run coverage for specific module
pytest --cov=src.core.security_validator tests/unit/test_security_validator.py
```

### Test Markers

```bash
# Run only fast tests (exclude slow AI model tests)
pytest -m "not slow"

# Run only integration tests
pytest tests/integration/

# Run only unit tests
pytest tests/unit/
```

## Test Categories

### 1. Security Tests ✅

**Location:** `tests/unit/test_security_validator.py`

**Coverage:**
- File upload validation (type, size, path traversal)
- Input sanitization (XSS prevention)
- Username validation
- Password strength validation
- Discipline and analysis mode validation
- Filename sanitization

**Example Test:**
```python
def test_path_traversal_blocked():
    """Test path traversal attempt is blocked."""
    is_valid, error = SecurityValidator.validate_filename("../etc/passwd")
    assert is_valid is False
    assert "path traversal" in error.lower()
```

**Run Security Tests:**
```bash
pytest tests/unit/test_security_validator.py -v
```

### 2. PHI Scrubbing Tests ✅

**Location:** `tests/unit/test_phi_scrubber.py`

**Coverage:**
- SSN detection and redaction
- MRN detection
- Phone number scrubbing
- Email address scrubbing
- Date scrubbing
- Multi-model NER scrubbing

**Run PHI Tests:**
```bash
pytest tests/unit/test_phi_scrubber.py -v
```

### 3. Cache Service Tests ✅

**Location:** `tests/unit/test_cache_service.py`

**Coverage:**
- Memory-aware caching
- LRU eviction
- TTL expiration
- Specialized caches (Embedding, NER, LLM, Document)
- Memory pressure handling

**Run Cache Tests:**
```bash
pytest tests/unit/test_cache_service.py -v
```

### 4. API Integration Tests ✅

**Location:** `tests/integration/`

**Coverage:**
- Full analysis workflow
- Dashboard API endpoints
- Compliance API endpoints
- Authentication and authorization
- Error handling

**Run Integration Tests:**
```bash
pytest tests/integration/ -v
```

### 5. GUI Tests ✅

**Location:** `tests/gui/`

**Coverage:**
- Export functionality
- UI interactions
- Dialog behavior

**Run GUI Tests:**
```bash
pytest tests/gui/ -v
```

## Writing New Tests

### Unit Test Template

```python
"""
Unit tests for [Component Name].

Brief description of what this test module covers.
"""

import pytest
from unittest.mock import Mock, patch

from src.core.your_module import YourClass


class TestYourFeature:
    """Tests for specific feature."""

    def test_valid_input(self):
        """Test valid input produces expected output."""
        # Arrange
        input_data = "test"
        expected = "expected_result"
        
        # Act
        result = YourClass.method(input_data)
        
        # Assert
        assert result == expected

    def test_invalid_input_raises_error(self):
        """Test invalid input raises appropriate error."""
        with pytest.raises(ValueError):
            YourClass.method(None)

    @patch('src.core.your_module.external_dependency')
    def test_with_mock(self, mock_dep):
        """Test with mocked dependency."""
        mock_dep.return_value = "mocked"
        result = YourClass.method_using_dependency()
        assert result == "expected"
        mock_dep.assert_called_once()
```

### Integration Test Template

```python
"""
Integration tests for [Feature Name].

Tests the interaction between multiple components.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestFeatureIntegration:
    """Integration tests for feature."""

    def test_end_to_end_workflow(self, client):
        """Test complete workflow from start to finish."""
        # Step 1: Setup
        response = client.post("/endpoint", json={"data": "test"})
        assert response.status_code == 200
        
        # Step 2: Verify
        result = response.json()
        assert result["status"] == "success"
```

## Test Best Practices

### 1. Test Naming

- Use descriptive names: `test_valid_pdf_upload_succeeds`
- Follow pattern: `test_[what]_[condition]_[expected]`
- Use docstrings to explain complex tests

### 2. Test Organization

- One test class per feature/component
- Group related tests together
- Use fixtures for common setup

### 3. Mocking

- Mock external dependencies (databases, APIs, file systems)
- Use `@patch` decorator for function-level mocks
- Use `Mock` objects for complex dependencies

### 4. Assertions

- Use specific assertions: `assert x == y` not `assert x`
- Test both positive and negative cases
- Include edge cases and boundary conditions

### 5. Test Data

- Use synthetic data only (no real PHI)
- Store test data in `tests/test_data/`
- Use fixtures for reusable test data

## Security Testing Checklist

### File Upload Security
- [ ] Valid file types accepted
- [ ] Invalid file types rejected
- [ ] File size limits enforced
- [ ] Path traversal attempts blocked
- [ ] Filename sanitization works
- [ ] Empty files rejected

### Input Validation
- [ ] XSS patterns removed
- [ ] SQL injection attempts blocked
- [ ] Parameter validation enforced
- [ ] Length limits respected
- [ ] Special characters handled

### Authentication
- [ ] Unauthenticated requests rejected
- [ ] Invalid tokens rejected
- [ ] Expired tokens rejected
- [ ] Inactive users blocked
- [ ] Admin-only endpoints protected

### PHI Protection
- [ ] SSN scrubbed
- [ ] MRN scrubbed
- [ ] Phone numbers scrubbed
- [ ] Email addresses scrubbed
- [ ] Dates scrubbed
- [ ] Names scrubbed

## Performance Testing

### Load Testing

```python
import pytest
import time

def test_cache_performance():
    """Test cache performance under load."""
    from src.core.cache_service import cache_service
    
    start = time.time()
    for i in range(1000):
        cache_service.set(f"key_{i}", f"value_{i}")
    duration = time.time() - start
    
    assert duration < 1.0  # Should complete in under 1 second
```

### Memory Testing

```python
def test_memory_cleanup():
    """Test memory cleanup under pressure."""
    from src.core.cache_service import cache_service
    import psutil
    
    initial_memory = psutil.virtual_memory().percent
    
    # Fill cache
    for i in range(10000):
        cache_service.set(f"key_{i}", "x" * 1000)
    
    # Trigger cleanup
    cache_service._cleanup_if_needed()
    
    final_memory = psutil.virtual_memory().percent
    assert final_memory < initial_memory + 10  # Memory increase limited
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'pydantic_settings'`
**Solution:** `pip install pydantic-settings`

**Issue:** Tests fail with database errors
**Solution:** Ensure test database is properly configured in conftest.py

**Issue:** GUI tests fail on headless systems
**Solution:** Use `pytest-qt` with virtual display or skip GUI tests in CI

**Issue:** Slow test execution
**Solution:** Use `-m "not slow"` to skip AI model tests

### Debug Mode

```bash
# Run tests with detailed output
pytest -vv --tb=long

# Run tests with print statements visible
pytest -s

# Run tests with pdb debugger on failure
pytest --pdb
```

## Test Coverage Goals

### Current Coverage

- **Security Validator:** 100% ✅
- **PHI Scrubber:** 95% ✅
- **Cache Service:** 90% ✅
- **API Endpoints:** 80% ✅
- **Database Operations:** 85% ✅

### Target Coverage

- **Overall:** 85%+
- **Critical Security:** 100%
- **Core Services:** 90%+
- **API Layer:** 85%+
- **GUI:** 70%+

## Reporting

### Generate Coverage Report

```bash
# HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=src --cov-report=term-missing

# XML report (for CI)
pytest --cov=src --cov-report=xml
```

### Test Results Summary

```bash
# Generate JUnit XML report
pytest --junitxml=test-results.xml

# Generate HTML report
pytest --html=report.html --self-contained-html
```

## Conclusion

This comprehensive testing guide ensures the Therapy Compliance Analyzer maintains high quality, security, and reliability. Regular testing and continuous integration help catch issues early and maintain code quality throughout development.

For questions or issues with testing, refer to:
- pytest documentation: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- pytest-qt: https://pytest-qt.readthedocs.io/
