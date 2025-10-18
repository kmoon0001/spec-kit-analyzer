@echo off
echo Starting API with AI Mocks...
call venv_fresh\Scripts\activate.bat
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001
