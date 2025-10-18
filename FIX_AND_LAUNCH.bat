@echo off
cls
echo ========================================
echo   COMPREHENSIVE FIX AND LAUNCH
echo ========================================
echo.

echo This will:
echo  1. Kill existing processes
echo  2. Rebuild frontend with fixes
echo  3. Launch both backend and frontend
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

REM Kill existing processes
echo.
echo [1/6] Cleaning up existing processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM electron.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo    Done!

REM Activate virtual environment
echo.
echo [2/6] Activating Python environment...
if not exist "venv_fresh\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    pause
    exit /b 1
)
call venv_fresh\Scripts\activate.bat
echo    Done!

REM Rebuild frontend
echo.
echo [3/6] Rebuilding frontend with fixes...
cd frontend\electron-react-app
echo    Installing dependencies...
call npm install --silent
echo    Building React app...
call npm run build
cd ..\..
echo    Done!

REM Start API
echo.
echo [4/6] Starting Backend API on port 8001...
start "Therapy Analyzer API" cmd /k "python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8001"
echo    Started!

REM Wait for API
echo.
echo [5/6] Waiting for API to be ready...
timeout /t 8 /nobreak >nul
:check_api
curl -s http://127.0.0.1:8001/health >nul 2>&1
if %errorlevel% neq 0 (
    echo    Waiting...
    timeout /t 2 /nobreak >nul
    goto check_api
)
echo    API is ready!

REM Start Electron
echo.
echo [6/6] Starting Electron Frontend...
cd frontend\electron-react-app
start "Therapy Analyzer Frontend" cmd /k "npm run start:electron"
cd ..\..
echo    Started!

echo.
echo ========================================
echo   LAUNCH COMPLETE
echo ========================================
echo.
echo Backend: http://127.0.0.1:8001
echo Frontend: Opening in Electron...
echo.
echo TEST THE FIX:
echo  1. Upload a document
echo  2. Click "Start Analysis"
echo  3. Progress should go 0%% -^> 100%%
echo  4. Should NOT get stuck at 5%%
echo.
echo Press any key to exit launcher...
pause >nul
