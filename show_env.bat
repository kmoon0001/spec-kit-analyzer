@echo off
REM Show ElectroAnalyzer Environment Variables
echo ========================================
echo ELECTROANALYZER ENVIRONMENT VARIABLES
echo ========================================
echo.

echo From .env file:
echo ----------------
type .env
echo.

echo From current shell:
echo -------------------
echo SECRET_KEY: %SECRET_KEY%
echo USE_AI_MOCKS: %USE_AI_MOCKS%
echo API_HOST: %API_HOST%
echo API_PORT: %API_PORT%
echo LOG_LEVEL: %LOG_LEVEL%
echo DEBUG: %DEBUG%
echo TESTING: %TESTING%
echo.

echo To set environment variables in current session:
echo ------------------------------------------------
echo set SECRET_KEY=your-key-here
echo set USE_AI_MOCKS=false
echo set API_HOST=127.0.0.1
echo set API_PORT=8001
echo set LOG_LEVEL=INFO
echo set DEBUG=false
echo set TESTING=false
echo.

echo To make them permanent, add to System Environment Variables
echo or run: setup_env.bat
