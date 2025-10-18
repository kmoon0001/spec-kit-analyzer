@echo off
echo Testing Electron Frontend...
echo.

cd frontend\electron-react-app

echo Checking Node modules...
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

echo.
echo Starting React dev server on port 3001...
npm run start:renderer

pause
