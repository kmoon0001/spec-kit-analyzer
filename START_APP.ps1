# Therapy Compliance Analyzer - Electron/React Launcher
# Starts Python FastAPI backend + Electron/React frontend

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   THERAPY COMPLIANCE ANALYZER" -ForegroundColor Yellow
Write-Host "   Electron + React + Python FastAPI" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python virtual environment
if (-not (Test-Path "venv_fresh\Scripts\python.exe")) {
    Write-Host "ERROR: Python virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv_fresh" -ForegroundColor Yellow
    Write-Host "Then run: venv_fresh\Scripts\pip.exe install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Node modules
if (-not (Test-Path "frontend\electron-react-app\node_modules")) {
    Write-Host "ERROR: Node modules not installed!" -ForegroundColor Red
    Write-Host "Please run: cd frontend\electron-react-app && npm install" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate Python virtual environment
Write-Host "[1/3] Activating Python virtual environment..." -ForegroundColor Green
& "venv_fresh\Scripts\Activate.ps1"
Write-Host "✓ Python environment activated" -ForegroundColor Green

# Start Python API server in background
Write-Host "[2/3] Starting Python API server..." -ForegroundColor Green
Write-Host "  - API: http://127.0.0.1:8001" -ForegroundColor Yellow
Write-Host "  - Loading AI models (30-60 seconds on first run)" -ForegroundColor Yellow
Write-Host ""

$apiJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & "venv_fresh\Scripts\python.exe" -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001
}

# Wait for API to be ready
Write-Host "Waiting for API to start..." -ForegroundColor Yellow
$maxWait = 60
$waitTime = 0

do {
    Start-Sleep -Seconds 3
    $waitTime += 3

    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8001/health" -TimeoutSec 5 -ErrorAction Stop
        if ($response.status -eq "ok") {
            Write-Host "✓ API server is ready!" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "  Waiting... ($waitTime/$maxWait seconds)" -ForegroundColor Yellow
    }

    if ($waitTime -ge $maxWait) {
        Write-Host "ERROR: API server failed to start" -ForegroundColor Red
        Stop-Job $apiJob
        Remove-Job $apiJob
        Read-Host "Press Enter to exit"
        exit 1
    }
} while ($true)

# Start Electron/React frontend
Write-Host ""
Write-Host "[3/3] Starting Electron frontend..." -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   LAUNCHING APPLICATION..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "frontend\electron-react-app"
npm run dev

# Cleanup
Write-Host ""
Write-Host "Application closed. Cleaning up..." -ForegroundColor Yellow
Set-Location "..\..\"

if ($apiJob.State -eq "Running") {
    Stop-Job $apiJob
    Remove-Job $apiJob
    Write-Host "✓ API server stopped" -ForegroundColor Green
}

Read-Host "Press Enter to exit"
