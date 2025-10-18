@echo off
echo ========================================
echo Testing Analysis Flow Improvements
echo ========================================
echo.

echo [1/4] Checking if backend is running...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo Backend is NOT running. Starting it now...
    start "Backend API" cmd /c "cd /d %~dp0 && python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"
    echo Waiting for backend to start...
    timeout /t 5 /nobreak >nul
) else (
    echo Backend is already running!
)

echo.
echo [2/4] Checking if frontend is built...
if not exist "frontend\electron-react-app\build\index.html" (
    echo Frontend is NOT built. Building now...
    cd frontend\electron-react-app
    call npm run build
    cd ..\..
) else (
    echo Frontend is already built!
)

echo.
echo [3/4] Starting Electron app...
cd frontend\electron-react-app
start "Electron App" cmd /c "npm start"
cd ..\..

echo.
echo [4/4] Opening diagnostic dashboard...
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo ========================================
echo Test Environment Ready!
echo ========================================
echo.
echo TESTING CHECKLIST:
echo [ ] Upload a document (PDF, DOCX, or TXT)
echo [ ] Select discipline (PT, OT, or SLP)
echo [ ] Choose strictness level
echo [ ] Click "Start Analysis"
echo [ ] Watch progress bar - should go from 0%% to 100%%
echo [ ] Verify progress updates smoothly (not stuck at 5%%)
echo [ ] Check that findings appear when complete
echo [ ] Test the improved Qt-like UI styling
echo.
echo Press any key to view logs...
pause >nul

echo.
echo Checking recent backend logs...
echo ========================================
curl -s http://localhost:8000/health
echo.
echo ========================================
echo.
echo Test complete! Press any key to exit...
pause >nul
