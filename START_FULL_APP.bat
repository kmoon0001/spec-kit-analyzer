@echo off
echo ========================================
echo   THERAPY COMPLIANCE ANALYZER
echo   Full Application Startup
echo ========================================
echo.

REM Activate virtual environment
echo [1/5] Activating virtual environment...
call venv_fresh\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Start API server in background
echo [2/5] Starting Meditron-powered API server...
echo   - Loading Meditron-7B clinical AI model
echo   - API will be available at http://127.0.0.1:8001
start "Therapy Analyzer API" /min cmd /c "python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001"

REM Wait for API to be ready
echo [3/5] Waiting for API to initialize...
timeout /t 10 /nobreak >nul

REM Install frontend dependencies if needed
echo [4/5] Checking frontend dependencies...
cd frontend\electron-react-app
if not exist node_modules (
    echo Installing frontend dependencies...
    npm install
)

REM Start Electron frontend
echo [5/5] Starting Electron frontend...
echo   - React development server: http://localhost:3000
echo   - Electron app will launch automatically
npm run dev

echo.
echo ========================================
echo   Application closed.
echo   Press any key to exit...
echo ========================================
pause >nul