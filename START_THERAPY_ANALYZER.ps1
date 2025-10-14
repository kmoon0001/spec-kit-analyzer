# Therapy Compliance Analyzer - One-Click Launcher
# This script starts both the API server and GUI application

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   THERAPY COMPLIANCE ANALYZER" -ForegroundColor Yellow
Write-Host "   Starting Application..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv_fresh\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please ensure 'venv_fresh' directory exists with Python installed." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "[1/4] Activating virtual environment..." -ForegroundColor Green
try {
    & "venv_fresh\Scripts\Activate.ps1"
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Set environment variables
Write-Host "[2/4] Setting environment variables..." -ForegroundColor Green
$env:QT_OPENGL = "software"
$env:QT_SCALE_FACTOR_ROUNDING_POLICY = "PassThrough"
$env:USE_AI_MOCKS = "0"
Write-Host "✓ Environment variables set" -ForegroundColor Green

# Start API server
Write-Host "[3/4] Starting API server..." -ForegroundColor Green
Write-Host "  - Loading AI models (this may take 30-60 seconds)" -ForegroundColor Yellow
Write-Host "  - API will be available at http://127.0.0.1:8001" -ForegroundColor Yellow
Write-Host "  - Please wait for 'API server is ready!' message" -ForegroundColor Yellow
Write-Host ""

# Start API in background job
$apiJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & "venv_fresh\Scripts\Activate.ps1"
    python -c "import sys; sys.path.insert(0, '.'); from src.api.main import app; import uvicorn; print('API Server Starting...'); uvicorn.run(app, host='127.0.0.1', port=8001, log_level='info')"
}

# Wait for API to be ready
Write-Host "[4/4] Waiting for API to be ready..." -ForegroundColor Green
$maxWait = 60  # Maximum wait time in seconds
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
        Write-Host "  Waiting for API to start... ($waitTime/$maxWait seconds)" -ForegroundColor Yellow
    }
    
    if ($waitTime -ge $maxWait) {
        Write-Host "ERROR: API server failed to start within $maxWait seconds" -ForegroundColor Red
        Write-Host "Please check the API server logs for errors" -ForegroundColor Red
        Stop-Job $apiJob
        Remove-Job $apiJob
        Read-Host "Press Enter to exit"
        exit 1
    }
} while ($true)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   API SERVER IS READY!" -ForegroundColor Green
Write-Host "   Starting GUI Application..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start GUI
try {
    python scripts\run_gui.py
} catch {
    Write-Host "ERROR: Failed to start GUI application" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

# Cleanup
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Application closed." -ForegroundColor Yellow
Write-Host "   Cleaning up..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

# Stop API job if still running
if ($apiJob.State -eq "Running") {
    Stop-Job $apiJob
    Remove-Job $apiJob
}

Read-Host "Press Enter to exit"
