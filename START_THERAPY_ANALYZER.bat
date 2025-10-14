@echo off
echo ========================================
echo   THERAPY COMPLIANCE ANALYZER
echo   Starting Application...
echo ========================================
echo.

REM Activate virtual environment
echo [1/4] Activating virtual environment...
call venv_fresh\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    echo Please ensure venv_fresh exists and contains Python
    pause
    exit /b 1
)

REM Set environment variables for GUI
echo [2/4] Setting environment variables...
set QT_OPENGL=software
set QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough
set USE_AI_MOCKS=0

REM Start API server in background
echo [3/4] Starting API server...
echo   - Loading AI models (this may take 30-60 seconds)
echo   - API will be available at http://127.0.0.1:8001
echo   - Please wait for "API server is ready!" message
echo.
start "Therapy Analyzer API" /min cmd /c "python -c \"import sys; sys.path.insert(0, '.'); from src.api.main import app; import uvicorn; print('API Server Starting...'); uvicorn.run(app, host='127.0.0.1', port=8001, log_level='info')\""

REM Wait for API to be ready
echo [4/4] Waiting for API to be ready...
timeout /t 5 /nobreak >nul

REM Test API connection
:test_api
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://127.0.0.1:8001/health' -TimeoutSec 5; if ($response.status -eq 'ok') { Write-Host 'API is ready!' } else { Write-Host 'API not ready yet...' } } catch { Write-Host 'API not ready yet...' }" 2>nul
if errorlevel 1 (
    echo   Waiting for API to start... (this may take up to 60 seconds)
    timeout /t 3 /nobreak >nul
    goto test_api
)

echo.
echo ========================================
echo   API SERVER IS READY!
echo   Starting GUI Application...
echo ========================================
echo.

REM Start GUI
python scripts\run_gui.py

echo.
echo ========================================
echo   Application closed.
echo   Press any key to exit...
echo ========================================
pause >nul
