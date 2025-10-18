@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Analysis Flow - Complete Test Suite
echo ========================================
echo.

:: Check Python
echo [1/6] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.11+ and try again.
    pause
    exit /b 1
)
python --version

:: Check Node
echo.
echo [2/6] Checking Node.js environment...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found!
    echo Please install Node.js 18+ and try again.
    pause
    exit /b 1
)
node --version

:: Check if backend is running
echo.
echo [3/6] Checking backend status...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo Backend is NOT running. Starting it now...
    echo.
    echo Starting FastAPI backend on port 8000...
    start "Therapy Analyzer Backend" cmd /k "python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"

    echo Waiting for backend to initialize...
    timeout /t 8 /nobreak >nul

    :: Verify backend started
    curl -s http://localhost:8000/health >nul 2>&1
    if %errorlevel% neq 0 (
        echo WARNING: Backend may not have started properly.
        echo Check the backend window for errors.
        echo.
    ) else (
        echo Backend started successfully!
    )
) else (
    echo Backend is already running!
)

:: Build frontend if needed
echo.
echo [4/6] Checking frontend build...
if not exist "frontend\electron-react-app\build\index.html" (
    echo Frontend needs to be built. This may take a few minutes...
    cd frontend\electron-react-app
    echo Running npm install...
    call npm install --silent
    echo Building React app...
    call npm run build
    cd ..\..
    echo Frontend built successfully!
) else (
    echo Frontend is already built!
)

:: Start Electron app
echo.
echo [5/6] Starting Electron application...
cd frontend\electron-react-app
start "Therapy Analyzer App" cmd /k "npm start"
cd ..\..

echo.
echo Waiting for Electron to start...
timeout /t 5 /nobreak >nul

:: Open browser as backup
echo.
echo [6/6] Opening diagnostic dashboard...
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo.
echo ========================================
echo Test Environment Ready!
echo ========================================
echo.
echo WHAT TO TEST:
echo.
echo 1. PROGRESS FIX:
echo    - Upload a test document
echo    - Click "Start Analysis"
echo    - Watch progress bar carefully
echo    - Should start at 0%% and smoothly progress to 100%%
echo    - Should NOT get stuck at 5%%
echo.
echo 2. UI IMPROVEMENTS (Qt-like styling):
echo    - Buttons should have 3D gradient appearance
echo    - Cards should show depth with shadows
echo    - Progress bar should have glossy effect
echo    - Dropzone should have gradient background
echo    - Hover effects should be smooth
echo.
echo 3. FUNCTIONALITY:
echo    - Document upload works
echo    - Discipline selection works
echo    - Strictness levels work
echo    - Analysis completes successfully
echo    - Results display correctly
echo.
echo ========================================
echo.
echo TROUBLESHOOTING:
echo - If backend fails: Check Python dependencies
echo - If frontend fails: Run 'npm install' in frontend/electron-react-app
echo - If stuck at 5%%: Check browser console for errors
echo.
echo Press any key to view backend health status...
pause >nul

echo.
echo ========================================
echo Backend Health Check
echo ========================================
curl -s http://localhost:8000/health
echo.
echo ========================================
echo.
echo Test complete! Keep windows open to continue testing.
echo Press any key to exit this window (apps will keep running)...
pause >nul
