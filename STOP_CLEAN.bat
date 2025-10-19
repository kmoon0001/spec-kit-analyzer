@echo off
echo ========================================
echo   THERAPY COMPLIANCE ANALYZER
echo   CLEAN SHUTDOWN SCRIPT
echo ========================================
echo.

echo [1/4] Stopping API server...
REM Find and kill Python processes related to our app
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| find "python.exe"') do (
    echo   - Terminating Python process %%i
    taskkill /PID %%i /F >nul 2>&1
)

echo [2/4] Stopping Electron frontend...
REM Find and kill Node processes related to our app
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq node.exe" /fo csv ^| find "node.exe"') do (
    echo   - Terminating Node process %%i
    taskkill /PID %%i /F >nul 2>&1
)

echo [3/4] Stopping Electron processes...
REM Kill any Electron processes
taskkill /IM electron.exe /F >nul 2>&1

echo [4/4] Waiting for ports to be released...
timeout /t 3 /nobreak >nul

REM Verify ports are free
netstat -ano | findstr ":8001" >nul
if %errorlevel% == 0 (
    echo   WARNING: Port 8001 still in use
) else (
    echo   - Port 8001 is now free
)

netstat -ano | findstr ":3001" >nul
if %errorlevel% == 0 (
    echo   WARNING: Port 3001 still in use
) else (
    echo   - Port 3001 is now free
)

echo.
echo ========================================
echo   Application shut down cleanly!
echo   All processes terminated.
echo ========================================
pause
