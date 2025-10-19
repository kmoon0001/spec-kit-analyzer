@echo off
echo ========================================
echo  Environment Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 18+ and try again
    pause
    exit /b 1
)

echo ✓ Python and Node.js are installed
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv_fresh" (
    echo Creating Python virtual environment...
    python -m venv venv_fresh
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Activate virtual environment and install dependencies
echo.
echo Installing Python dependencies...
call venv_fresh\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
echo ✓ Python dependencies installed

REM Install frontend dependencies
echo.
echo Installing frontend dependencies...
cd frontend\electron-react-app
if not exist "node_modules" (
    npm install
    echo ✓ Frontend dependencies installed
) else (
    echo ✓ Frontend dependencies already installed
)

cd ..\..

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo.
    echo Creating .env file from template...
    copy env.example .env
    echo ✓ .env file created
    echo.
    echo IMPORTANT: Please edit .env file and set your SECRET_KEY
    echo You can generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))"
) else (
    echo ✓ .env file already exists
)

echo.
echo ========================================
echo  Environment Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file and set SECRET_KEY
echo 2. Run LAUNCH_COMPLETE_APP.bat to start the application
echo.
pause
