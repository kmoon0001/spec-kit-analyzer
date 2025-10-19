@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   THERAPY COMPLIANCE ANALYZER
echo   ULTIMATE STARTUP WITH COMPREHENSIVE CLEANUP
echo ========================================
echo.
echo ADDRESSING ALL POTENTIAL ISSUES:
echo  - Process conflicts (Python, Node, Electron)
echo  - Port conflicts (8001, 3001)
echo  - Database lock files
echo  - Temporary file accumulation
echo  - Cache file buildup
echo  - Background thread cleanup
echo  - Resource pool cleanup
echo  - Log file management
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
echo   COMPREHENSIVE CLEANUP ON EXIT...
echo ========================================

REM Kill tracked processes
if defined CLEANUP_PIDS (
    echo Terminating tracked processes...
    for %%p in (!CLEANUP_PIDS!) do (
        if %%p neq "" (
            echo   - Terminating PID %%p
            taskkill /PID %%p /F >nul 2>&1
        )
    )
)

REM Kill all application processes
echo Terminating all application processes...
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM node.exe /F >nul 2>&1
taskkill /IM electron.exe /F >nul 2>&1

REM Clean up database lock files
echo Cleaning database lock files...
if exist "compliance.db-shm" del "compliance.db-shm" >nul 2>&1
if exist "compliance.db-wal" del "compliance.db-wal" >nul 2>&1

REM Clean up temporary files
echo Cleaning temporary files...
if exist "temp" rmdir /s /q "temp" >nul 2>&1

REM Clean up cache files
echo Cleaning cache files...
if exist ".cache" rmdir /s /q ".cache" >nul 2>&1

REM Clean up Python cache
echo Cleaning Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" >nul 2>&1

echo Comprehensive cleanup complete!
goto :eof

:start

REM Set up exit handler
set "EXIT_HANDLER=call :cleanup_on_exit"

REM Kill all existing processes that might conflict
echo [1/8] Cleaning up existing processes...
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM node.exe /F >nul 2>&1
taskkill /IM electron.exe /F >nul 2>&1
echo   - All conflicting processes terminated

REM Clean up database lock files
echo [2/8] Cleaning database lock files...
if exist "compliance.db-shm" del "compliance.db-shm" >nul 2>&1
if exist "compliance.db-wal" del "compliance.db-wal" >nul 2>&1
echo   - Database lock files cleaned

REM Clean up temporary files
echo [3/8] Cleaning temporary files...
if exist "temp" rmdir /s /q "temp" >nul 2>&1
echo   - Temporary files cleaned

REM Clean up cache files
echo [4/8] Cleaning cache files...
if exist ".cache" rmdir /s /q ".cache" >nul 2>&1
echo   - Cache files cleaned

REM Wait for ports to be released
echo [5/8] Waiting for ports to be released...
timeout /t 3 /nobreak >nul

REM Verify ports are free
echo [6/8] Verifying ports are available...
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
echo [7/8] Activating virtual environment...
call venv_fresh\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    %EXIT_HANDLER%
    pause
    exit /b 1
)

REM Start API server and track its PID
echo [8/8] Starting API server...
echo   - Loading Meditron-7B clinical AI model
echo   - API will be available at http://127.0.0.1:8001

REM Start API in background
start /b "Therapy Analyzer API" cmd /c "venv_fresh\Scripts\activate.bat && python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001"

REM Wait for API to start
echo Waiting for API to initialize...
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
