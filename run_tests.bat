@echo off
echo ========================================
echo  Comprehensive Test Suite Runner
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if pytest is installed
python -m pytest --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing test dependencies...
    pip install pytest pytest-cov pytest-asyncio pytest-mock pytest-xdist
)

echo.
echo 🧪 RUNNING COMPREHENSIVE TEST SUITE
echo ========================================
echo.

REM Run all tests with coverage
echo [1/4] Running Unit Tests...
python -m pytest tests/unit/ -v --cov=src --cov-report=term-missing --tb=short

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Unit tests failed
    pause
    exit /b 1
)

echo.
echo [2/4] Running Integration Tests...
python -m pytest tests/integration/ -v --cov=src --cov-report=term-missing --tb=short

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Integration tests failed
    pause
    exit /b 1
)

echo.
echo [3/4] Running Security Tests...
python -m pytest tests/security/ -v --cov=src --cov-report=term-missing --tb=short

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Security tests failed
    pause
    exit /b 1
)

echo.
echo [4/4] Running Performance Tests...
python -m pytest tests/performance/ -v --cov=src --cov-report=term-missing --tb=short

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Performance tests failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo 🎉 ALL TESTS PASSED!
echo ========================================
echo.

REM Generate comprehensive coverage report
echo 📊 Generating Coverage Report...
python -m pytest --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing

echo.
echo 📈 Coverage Report Generated:
echo   - HTML: htmlcov/index.html
echo   - XML: coverage.xml
echo   - Terminal: See above output
echo.

echo ✅ Test Suite Complete!
echo.
pause
