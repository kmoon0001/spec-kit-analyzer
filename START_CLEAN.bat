@echo off
echo ========================================
echo   THERAPY COMPLIANCE ANALYZER
echo   CLEAN STARTUP SCRIPT
echo ========================================
echo.
echo ROOT CAUSE FIXED:
echo  - Killing all existing Python processes
echo  - Killing all existing Node processes
echo  - Ensuring clean port availability
echo.

REM Kill all existing processes that might conflict
echo [1/6] Cleaning up existing processes...
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM node.exe /F >nul 2>&1
taskkill /IM electron.exe /F >nul 2>&1
echo   - All conflicting processes terminated

REM Wait for ports to be released
echo [2/6] Waiting for ports to be released...
timeout /t 3 /nobreak >nul

REM Verify ports are free
echo [3/6] Verifying ports are available...
netstat -ano | findstr ":8001" >nul
if %errorlevel% == 0 (
    echo   ERROR: Port 8001 still in use!
    pause
    exit /b 1
)
netstat -ano | findstr ":3001" >nul
if %errorlevel% == 0 (
    echo   ERROR: Port 3001 still in use!
    pause
    exit /b 1
)
echo   - Ports 8001 and 3001 are available

REM Activate virtual environment
echo [4/6] Activating virtual environment...
call venv_fresh\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Start API server in new window
echo [5/6] Starting API server...
echo   - Loading Meditron-7B clinical AI model
echo   - API will be available at http://127.0.0.1:8001
start "Therapy Analyzer API" /min cmd /c "venv_fresh\Scripts\activate.bat && python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001"

REM Wait for API to start
echo [6/6] Waiting for API to initialize...
timeout /t 15 /nobreak >nul

REM Start frontend
echo Starting Electron frontend...
cd frontend\electron-react-app
npm run dev

REM If we get here, the frontend has exited
echo.
echo ========================================
echo   Frontend has exited.
echo   Cleaning up remaining processes...
echo ========================================

REM Clean up API server
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM node.exe /F >nul 2>&1
taskkill /IM electron.exe /F >nul 2>&1

echo.
echo ========================================
echo   Application shut down cleanly!
echo   All processes terminated.
echo ========================================
pause
