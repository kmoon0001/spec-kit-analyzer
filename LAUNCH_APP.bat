@echo off
cls
echo ========================================
echo   THERAPY COMPLIANCE ANALYZER
echo   Unified Application Launcher
echo ========================================
echo.

REM Kill any existing processes
echo [1/5] Cleaning up existing processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" >nul 2>&1
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *electron*" >nul 2>&1
timeout /t 2 /nobreak >nul

REM Activate virtual environment
echo [2/5] Activating Python environment...
if not exist "venv_fresh\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv_fresh
    pause
    exit /b 1
)
call venv_fresh\Scripts\activate.bat

REM Start API on port 8001
echo [3/5] Starting Backend API on port 8001...
start "Therapy Analyzer API" cmd /k "python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8001"

REM Wait for API to be ready
echo [4/5] Waiting for API to initialize...
timeout /t 8 /nobreak >nul

:check_api
curl -s http://127.0.0.1:8001/health >nul 2>&1
if %errorlevel% neq 0 (
    echo    API not ready yet, waiting...
    timeout /t 2 /nobreak >nul
    goto check_api
)
echo    API is ready!

REM Start Electron frontend
echo [5/5] Starting Electron Frontend...
cd frontend\electron-react-app
start "Therapy Analyzer Frontend" cmd /k "npm run start:electron"
cd ..\..

echo.
echo ========================================
echo   APPLICATION STARTED SUCCESSFULLY
echo ========================================
echo.
echo Backend API: http://127.0.0.1:8001
echo Frontend: Will open in Electron window
echo.
echo Press any key to exit this launcher...
echo (Apps will continue running)
pause >nul
