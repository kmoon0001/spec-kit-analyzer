@echo off
echo Starting Therapy Compliance Analyzer with clean shutdown...
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM node.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul
start "API" cmd /c "cd /d C:\Users\kevin\Desktop\ElectroAnalyzer && venv_fresh\Scripts\activate.bat && python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001"
timeout /t 10 /nobreak >nul
start "Frontend" cmd /c "cd /d C:\Users\kevin\Desktop\ElectroAnalyzer\frontend\electron-react-app && npm run dev"
echo Application started! Close this window to stop all processes.
pause
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM node.exe /F >nul 2>&1
taskkill /IM electron.exe /F >nul 2>&1
echo Cleanup complete!
