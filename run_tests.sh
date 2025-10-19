#!/bin/bash
# Comprehensive Test Suite Runner for Linux/Mac

echo "========================================"
echo "  Comprehensive Test Suite Runner"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if pytest is installed
if ! python3 -m pytest --version &> /dev/null; then
    echo "Installing test dependencies..."
    pip3 install pytest pytest-cov pytest-asyncio pytest-mock pytest-xdist
fi

echo
echo "🧪 RUNNING COMPREHENSIVE TEST SUITE"
echo "========================================"
echo

# Run all tests with coverage
echo "[1/4] Running Unit Tests..."
python3 -m pytest tests/unit/ -v --cov=src --cov-report=term-missing --tb=short

if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed"
    exit 1
fi

echo
echo "[2/4] Running Integration Tests..."
python3 -m pytest tests/integration/ -v --cov=src --cov-report=term-missing --tb=short

if [ $? -ne 0 ]; then
    echo "❌ Integration tests failed"
    exit 1
fi

echo
echo "[3/4] Running Security Tests..."
python3 -m pytest tests/security/ -v --cov=src --cov-report=term-missing --tb=short

if [ $? -ne 0 ]; then
    echo "❌ Security tests failed"
    exit 1
fi

echo
echo "[4/4] Running Performance Tests..."
python3 -m pytest tests/performance/ -v --cov=src --cov-report=term-missing --tb=short

if [ $? -ne 0 ]; then
    echo "❌ Performance tests failed"
    exit 1
fi

echo
echo "========================================"
echo "🎉 ALL TESTS PASSED!"
echo "========================================"
echo

# Generate comprehensive coverage report
echo "📊 Generating Coverage Report..."
python3 -m pytest --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing

echo
echo "📈 Coverage Report Generated:"
echo "  - HTML: htmlcov/index.html"
echo "  - XML: coverage.xml"
echo "  - Terminal: See above output"
echo

echo "✅ Test Suite Complete!"
echo
