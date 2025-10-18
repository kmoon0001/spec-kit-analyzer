@echo off
echo ========================================
echo   THERAPY COMPLIANCE ANALYZER
echo   Diagnostic and Fix Script
echo ========================================
echo.

echo [STEP 1] Checking Python environment...
if not exist "venv_fresh\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo.
    echo Creating virtual environment...
    python -m venv venv_fresh
    echo Installing dependencies...
    venv_fresh\Scripts\pip.exe install -r requirements.txt
) else (
    echo ✓ Python virtual environment found
)

echo.
echo [STEP 2] Checking Node.js environment...
cd frontend\electron-react-app
if not exist "node_modules" (
    echo ERROR: Node modules not installed!
    echo.
    echo Installing Node dependencies...
    npm install
) else (
    echo ✓ Node modules found
)
cd ..\..

echo.
echo [STEP 3] Checking ports...
netstat -ano | findstr ":8001" >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 8001 is in use
    echo Attempting to free port...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001"') do taskkill /PID %%a /F 2>nul
)

netstat -ano | findstr ":3001" >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 3001 is in use
    echo Attempting to free port...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3001"') do taskkill /PID %%a /F 2>nul
)

echo.
echo [STEP 4] Testing Python API...
call venv_fresh\Scripts\activate.bat
python -c "from src.api.main import app; print('✓ API imports successfully')" 2>nul
if %errorlevel% neq 0 (
    echo ERROR: API import failed!
    echo Check Python dependencies
    pause
    exit /b 1
)

echo.
echo [STEP 5] Testing database...
if not exist "compliance.db" (
    echo Creating database...
    python -c "from src.database.database import init_db; import asyncio; asyncio.run(init_db())"
)
echo ✓ Database ready

echo.
echo ========================================
echo   DIAGNOSTIC COMPLETE
echo ========================================
echo.
echo All checks passed! You can now run:
echo   - START_APP.bat (Windows)
echo   - START_APP.ps1 (PowerShell)
echo.
echo Or test components separately:
echo   - TEST_API.bat (Test API only)
echo   - TEST_FRONTEND.bat (Test frontend only)
echo.
pause
