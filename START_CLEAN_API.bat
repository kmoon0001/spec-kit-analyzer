@echo off
echo ========================================
echo   STARTING API SERVER
echo ========================================
echo.
echo Activating clean virtual environment...
call venv_clean\Scripts\activate.bat

echo Starting API server on http://127.0.0.1:8001
echo.
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001 --reload

pause
