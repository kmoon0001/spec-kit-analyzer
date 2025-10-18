@echo off
echo Testing API Server...
echo.

call venv_fresh\Scripts\activate.bat

echo Starting API on port 8001...
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001

pause
