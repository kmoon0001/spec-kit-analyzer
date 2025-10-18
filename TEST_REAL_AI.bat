@echo off
echo ========================================
echo  Testing Real AI Models
echo ========================================
echo.

echo This will test if real AI models work on your system.
echo.
echo RECOMMENDED: Llama 3.2 3B Instruct
echo - Size: ~2GB download
echo - RAM: 4-6GB needed
echo - Speed: Fast
echo - Stability: Excellent
echo.

choice /C YN /M "Do you want to test Llama 3.2 3B"
if errorlevel 2 goto :skip_test
if errorlevel 1 goto :test_llama32

:test_llama32
echo.
echo [1/3] Backing up current config...
copy config.yaml config_backup.yaml >nul
echo ✓ Backup created: config_backup.yaml

echo.
echo [2/3] Switching to Llama 3.2 3B config...
copy config_llama32.yaml config.yaml >nul
echo ✓ Config updated

echo.
echo [3/3] Starting API and testing...
echo.
echo NOTE: First run will download the model (~2GB)
echo This may take 5-10 minutes depending on your internet.
echo.
pause

REM Kill existing processes
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

REM Start API
start "API Test" cmd /c "call venv_fresh\Scripts\activate.bat && python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001"

echo Waiting for API to start and download model...
echo (This will take longer on first run)
timeout /t 30 /nobreak >nul

echo.
echo Running analysis test...
call venv_fresh\Scripts\activate.bat
python test_analysis_direct.py

echo.
echo ========================================
if %ERRORLEVEL% EQU 0 (
    echo ✓ SUCCESS! Real AI is working!
    echo.
    echo Your config has been updated to use Llama 3.2 3B.
    echo The model is now cached and will be fast on next run.
    echo.
    choice /C YN /M "Keep this configuration"
    if errorlevel 2 goto :restore_backup
    if errorlevel 1 goto :keep_config
) else (
    echo ✗ FAILED! Real AI crashed or timed out.
    echo.
    echo Restoring backup config with mocks...
    copy config_backup.yaml config.yaml >nul
    echo ✓ Restored to mock AI configuration
)
echo ========================================
goto :cleanup

:keep_config
echo.
echo ✓ Configuration saved!
echo You can now use: LAUNCH_COMPLETE_APP.bat
goto :cleanup

:restore_backup
echo.
echo Restoring original config...
copy config_backup.yaml config.yaml >nul
echo ✓ Restored original configuration
goto :cleanup

:skip_test
echo.
echo Test cancelled. No changes made.
goto :end

:cleanup
echo.
echo Stopping API...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

:end
echo.
echo Done!
pause
