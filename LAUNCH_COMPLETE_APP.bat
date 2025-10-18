@echo off
echo ========================================
echo  Therapy Compliance Analyzer
echo  Complete Application Launcher
echo ========================================
echo.

REM Kill any existing processes
echo Cleaning up existing processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM electron.exe 2>nul
timeout /t 2 /nobreak >nul

REM Start the API backend
echo.
echo [1/2] Starting FastAPI Backend (with AI Mocks)...
start "API Backend" cmd /c "call venv_fresh\Scripts\activate.bat && python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001"

REM Wait for API to be ready
echo Waiting for API to initialize...
timeout /t 8 /nobreak >nul

REM Start the Electron frontend
echo.
echo [2/2] Starting Electron Frontend...
cd frontend\electron-react-app
start "Electron App" cmd /c "npm start"

echo.
echo ========================================
echo  Application Started Successfully!
echo ========================================
echo.
echo API Backend:  http://127.0.0.1:8001
echo Frontend:     Electron window opening...
echo.
echo Press any key to stop all services...
pause >nul

REM Cleanup on exit
echo.
echo Stopping services...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM electron.exe 2>nul
echo Done!
