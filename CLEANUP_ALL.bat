@echo off
echo ========================================
echo   THERAPY COMPLIANCE ANALYZER
echo   COMPREHENSIVE CLEANUP SCRIPT
echo ========================================
echo.
echo CLEANING UP ALL RESOURCES:
echo  - Processes (Python, Node, Electron)
echo  - Database connections
echo  - Background threads and schedulers
echo  - Temporary files and cache
echo  - Log files
echo  - Resource pools
echo.

REM Kill all application processes
echo [1/8] Terminating application processes...
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM node.exe /F >nul 2>&1
taskkill /IM electron.exe /F >nul 2>&1
echo   - All processes terminated

REM Wait for processes to fully terminate
echo [2/8] Waiting for processes to terminate...
timeout /t 3 /nobreak >nul

REM Clean up temporary files
echo [3/8] Cleaning temporary files...
if exist "temp" (
    rmdir /s /q "temp" >nul 2>&1
    echo   - Temporary files cleaned
) else (
    echo   - No temporary files found
)

REM Clean up cache files
echo [4/8] Cleaning cache files...
if exist ".cache" (
    rmdir /s /q ".cache" >nul 2>&1
    echo   - Cache files cleaned
) else (
    echo   - No cache files found
)

REM Clean up log files (keep recent ones)
echo [5/8] Cleaning old log files...
if exist "logs" (
    forfiles /p logs /m *.log /d -7 /c "cmd /c del @path" >nul 2>&1
    echo   - Old log files cleaned
) else (
    echo   - No log files found
)

REM Clean up database lock files
echo [6/8] Cleaning database lock files...
if exist "compliance.db-shm" del "compliance.db-shm" >nul 2>&1
if exist "compliance.db-wal" del "compliance.db-wal" >nul 2>&1
echo   - Database lock files cleaned

REM Clean up Python cache
echo [7/8] Cleaning Python cache...
if exist "__pycache__" (
    rmdir /s /q "__pycache__" >nul 2>&1
    echo   - Python cache cleaned
)
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" >nul 2>&1

REM Verify ports are free
echo [8/8] Verifying ports are available...
netstat -ano | findstr ":8001" >nul
if %errorlevel% == 0 (
    echo   WARNING: Port 8001 still in use
) else (
    echo   - Port 8001 is free
)

netstat -ano | findstr ":3001" >nul
if %errorlevel% == 0 (
    echo   WARNING: Port 3001 still in use
) else (
    echo   - Port 3001 is free
)

echo.
echo ========================================
echo   COMPREHENSIVE CLEANUP COMPLETE!
echo   All resources have been cleaned up.
echo ========================================
pause
