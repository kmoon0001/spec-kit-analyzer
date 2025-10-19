@echo off
REM ElectroAnalyzer Environment Setup for Windows
echo Setting up ElectroAnalyzer environment...

REM Generate a secure SECRET_KEY
for /f %%i in ('python -c "import secrets; print(secrets.token_urlsafe(32))"') do set SECRET_KEY=%%i

REM Set environment variables
set SECRET_KEY=%SECRET_KEY%
set USE_AI_MOCKS=false
set API_HOST=127.0.0.1
set API_PORT=8001
set LOG_LEVEL=INFO
set DEBUG=false
set TESTING=false

echo [SUCCESS] Environment variables set!
echo [KEY] SECRET_KEY: %SECRET_KEY:~0,10%...
echo.
echo You can now start your application.
echo.
echo To make these permanent, add them to your system environment variables
echo or create a .env file in your project directory.
