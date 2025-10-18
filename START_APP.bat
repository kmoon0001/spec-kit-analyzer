@echo off
echo ========================================
echo   THERAPY COMPLIANCE ANALYZER
echo   Starting Application...
echo ========================================
echo.

REM Activate Python virtual environment
echo [1/3] Activating Python virtual environment...
call venv_fresh\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    echo Please run: python -m venv venv_fresh
    pause
    exit /b 1
)

REM Start API server in background
echo [2/3] Starting Python API server...
echo   - API will be available at http://127.0.0.1:8001
echo   - Loading AI models (may take 30-60 seconds on first run)
echo.
start "Therapy Analyzer API" cmd /c "venv_fresh\Scripts\python.exe -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001"

REM Wait for API to be ready
echo Waiting for API to start...
timeout /t 8 /nobreak >nul

REM Start Electron/React frontend
echo [3/3] Starting Electron frontend...
cd frontend\electron-react-app
if not exist "node_modules" (
    echo ERROR: Node modules not installed!
    echo Please run: cd frontend\electron-react-app ^&^& npm install
    pause
    exit /b 1
)

echo.
echo ========================================
echo   LAUNCHING APPLICATION...
echo ========================================
echo.

npm run dev

echo.
echo Application closed.
pause
