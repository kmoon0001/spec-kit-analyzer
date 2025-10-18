@echo off
echo ========================================
echo   THERAPY COMPLIANCE ANALYZER
echo   Starting Application...
echo ========================================
echo.
echo RECENT FIXES APPLIED:
echo  - Fixed analysis stuck at 5%% progress
echo  - Improved Qt-like UI styling
echo  - Enhanced progress tracking
echo.
echo ========================================
echo.

REM Start API in new window
echo Starting Python API...
start "API Server" cmd /k "venv_fresh\Scripts\activate && python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001"

REM Wait a bit for API to start
echo Waiting for API to start...
timeout /t 10 /nobreak

REM Start frontend
echo Starting Electron frontend...
cd frontend\electron-react-app
npm run dev

pause
