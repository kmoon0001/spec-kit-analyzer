@echo off
echo Starting Therapy Compliance Analyzer...
echo.

echo Starting Core Enhanced Services...
start "Core Services" cmd /k "venv_fresh\Scripts\activate && python start_simple.py"

timeout /t 3 /nobreak >nul

echo Starting API Server...
start "API Server" cmd /k "venv_fresh\Scripts\activate && python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001"

timeout /t 5 /nobreak >nul

echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd frontend/electron-react-app && npm run start:renderer"

timeout /t 5 /nobreak >nul

echo Starting Electron Desktop App...
start "Electron App" cmd /k "cd frontend/electron-react-app && npm run electron:dev"

echo.
echo All services are starting...
echo.
echo Access Points:
echo - API Server: http://localhost:8001
echo - Frontend: http://localhost:3001
echo - API Documentation: http://localhost:8001/docs
echo.
echo Press any key to exit this launcher...
pause >nul
