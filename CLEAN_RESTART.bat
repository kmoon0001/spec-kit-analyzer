@echo off
echo Cleaning and restarting...
echo.

cd frontend\electron-react-app

echo [1/3] Clearing cache...
if exist ".cache" rmdir /s /q .cache
if exist "node_modules\.cache" rmdir /s /q node_modules\.cache

echo [2/3] Killing any running processes...
taskkill /F /IM node.exe 2>nul
taskkill /F /IM electron.exe 2>nul
timeout /t 2 /nobreak >nul

echo [3/3] Starting fresh...
npm run dev

pause
