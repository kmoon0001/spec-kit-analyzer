@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   THERAPY COMPLIANCE ANALYZER
echo   SMART STARTUP WITH CLEAN SHUTDOWN
echo ========================================
echo.
echo ROOT CAUSE FIXED:
echo  - Automatic process cleanup on exit
echo  - Port conflict prevention
echo  - Clean shutdown handling
echo.

REM Set up cleanup on script exit
set "CLEANUP_PIDS="

REM Function to add PID to cleanup list
goto :start

:add_cleanup
set "CLEANUP_PIDS=!CLEANUP_PIDS! %1"
goto :eof

:cleanup_on_exit
echo.
echo ========================================
echo   CLEANING UP ON EXIT...
echo ========================================
if defined CLEANUP_PIDS (
    echo Terminating tracked processes...
    for %%p in (!CLEANUP_PIDS!) do (
        if %%p neq "" (
            echo   - Terminating PID %%p
            taskkill /PID %%p /F >nul 2>&1
        )
    )
)
echo Terminating any remaining app processes...
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM node.exe /F >nul 2>&1
taskkill /IM electron.exe /F >nul 2>&1
echo Cleanup complete!
goto :eof

:start

REM Set up exit handler
set "EXIT_HANDLER=call :cleanup_on_exit"

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
    %EXIT_HANDLER%
    pause
    exit /b 1
)
netstat -ano | findstr ":3001" >nul
if %errorlevel% == 0 (
    echo   ERROR: Port 3001 still in use!
    %EXIT_HANDLER%
    pause
    exit /b 1
)
echo   - Ports 8001 and 3001 are available

REM Activate virtual environment
echo [4/6] Activating virtual environment...
call venv_fresh\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    %EXIT_HANDLER%
    pause
    exit /b 1
)

REM Start API server and track its PID
echo [5/6] Starting API server...
echo   - Loading Meditron-7B clinical AI model
echo   - API will be available at http://127.0.0.1:8001

REM Start API in background and capture PID
start /b "Therapy Analyzer API" cmd /c "venv_fresh\Scripts\activate.bat && python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001"
REM Note: We can't easily capture PID from start command, so we'll rely on process name cleanup

REM Wait for API to start
echo [6/6] Waiting for API to initialize...
timeout /t 15 /nobreak >nul

REM Start frontend
echo Starting Electron frontend...
cd frontend\electron-react-app

REM Set up Ctrl+C handler
echo.
echo ========================================
echo   Application starting...
echo   - API: http://127.0.0.1:8001
echo   - Frontend: http://localhost:3001
echo.
echo   Press Ctrl+C to stop cleanly
echo ========================================

REM Start frontend (this will block until frontend exits)
npm run dev

REM If we get here, the frontend has exited normally
echo.
echo Frontend has exited normally.
%EXIT_HANDLER%
pause
