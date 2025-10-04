@echo off
echo ========================================
echo  Therapy Compliance Analyzer
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

echo Checking virtual environment...
if not exist ".venv" (
    echo Creating