# Comprehensive Diagnostic Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   THERAPY COMPLIANCE ANALYZER" -ForegroundColor Yellow
Write-Host "   Full System Diagnostic" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$errors = @()

# Check Python
Write-Host "[1/8] Checking Python..." -ForegroundColor Green
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found!" -ForegroundColor Red
    $errors += "Python not installed"
}

# Check Node
Write-Host "[2/8] Checking Node.js..." -ForegroundColor Green
try {
    $nodeVersion = & node --version 2>&1
    Write-Host "  ✓ Node $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js not found!" -ForegroundColor Red
    $errors += "Node.js not installed"
}

# Check venv
Write-Host "[3/8] Checking Python virtual environment..." -ForegroundColor Green
if (Test-Path "venv_fresh\Scripts\python.exe") {
    Write-Host "  ✓ Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ Virtual environment not found!" -ForegroundColor Red
    $errors += "Python venv missing"
}

# Check node_modules
Write-Host "[4/8] Checking Node modules..." -ForegroundColor Green
if (Test-Path "frontend\electron-react-app\node_modules") {
    Write-Host "  ✓ Node modules installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ Node modules not installed!" -ForegroundColor Red
    $errors += "Node modules missing"
}

# Check ports
Write-Host "[5/8] Checking ports..." -ForegroundColor Green
$port8001 = netstat -ano | Select-String ":8001"
$port3001 = netstat -ano | Select-String ":3001"

if ($port8001) {
    Write-Host "  ⚠ Port 8001 is in use" -ForegroundColor Yellow
} else {
    Write-Host "  ✓ Port 8001 is free" -ForegroundColor Green
}

if ($port3001) {
    Write-Host "  ⚠ Port 3001 is in use" -ForegroundColor Yellow
} else {
    Write-Host "  ✓ Port 3001 is free" -ForegroundColor Green
}

# Check database
Write-Host "[6/8] Checking database..." -ForegroundColor Green
if (Test-Path "compliance.db") {
    Write-Host "  ✓ Database file exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Database not initialized" -ForegroundColor Yellow
}

# Test API imports
Write-Host "[7/8] Testing API imports..." -ForegroundColor Green
try {
    & "venv_fresh\Scripts\python.exe" -c "from src.api.main import app; print('OK')" 2>&1 | Out-Null
    Write-Host "  ✓ API imports successfully" -ForegroundColor Green
} catch {
    Write-Host "  ✗ API import failed!" -ForegroundColor Red
    $errors += "API import error"
}

# Check config
Write-Host "[8/8] Checking configuration..." -ForegroundColor Green
if (Test-Path "config.yaml") {
    Write-Host "  ✓ config.yaml exists" -ForegroundColor Green
}
if (Test-Path ".env") {
    Write-Host "  ✓ .env exists" -ForegroundColor Green
}
if (Test-Path "frontend\electron-react-app\.env") {
    Write-Host "  ✓ frontend .env exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($errors.Count -eq 0) {
    Write-Host "   ✓ ALL CHECKS PASSED!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Ready to start! Run:" -ForegroundColor Green
    Write-Host "  .\START_APP.ps1" -ForegroundColor Yellow
} else {
    Write-Host "   ✗ ISSUES FOUND" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Issues:" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "  - $error" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Run DIAGNOSE_AND_FIX.bat to fix issues" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to exit"
