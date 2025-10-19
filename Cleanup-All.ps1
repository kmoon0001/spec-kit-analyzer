# Comprehensive cleanup script for Therapy Compliance Analyzer
# This script addresses all potential resource leaks and cleanup issues

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  THERAPY COMPLIANCE ANALYZER" -ForegroundColor Cyan
Write-Host "  COMPREHENSIVE CLEANUP SCRIPT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to safely terminate processes
function Stop-ProcessSafely {
    param($ProcessName, $Description)

    Write-Host "[$Description] Stopping $ProcessName processes..." -ForegroundColor Yellow

    $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    if ($processes) {
        foreach ($process in $processes) {
            try {
                Write-Host "  - Terminating $ProcessName (PID: $($process.Id))" -ForegroundColor Gray
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            }
            catch {
                Write-Host "  - Could not terminate $ProcessName (PID: $($process.Id))" -ForegroundColor Red
            }
        }
    }
    else {
        Write-Host "  - No $ProcessName processes found" -ForegroundColor Green
    }
}

# Function to clean up directories
function Clean-Directory {
    param($Path, $Description)

    Write-Host "[$Description] Cleaning $Path..." -ForegroundColor Yellow

    if (Test-Path $Path) {
        try {
            Remove-Item -Path $Path -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  - $Description cleaned" -ForegroundColor Green
        }
        catch {
            Write-Host "  - Could not clean $Description" -ForegroundColor Red
        }
    }
    else {
        Write-Host "  - No $Description found" -ForegroundColor Green
    }
}

# Function to clean up files by pattern
function Clean-FilesByPattern {
    param($Pattern, $Description, $MaxAgeDays = 7)

    Write-Host "[$Description] Cleaning files matching $Pattern..." -ForegroundColor Yellow

    $files = Get-ChildItem -Path . -Recurse -Include $Pattern -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$MaxAgeDays) }

    if ($files) {
        foreach ($file in $files) {
            try {
                Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
                Write-Host "  - Removed $($file.Name)" -ForegroundColor Gray
            }
            catch {
                Write-Host "  - Could not remove $($file.Name)" -ForegroundColor Red
            }
        }
        Write-Host "  - $Description cleaned" -ForegroundColor Green
    }
    else {
        Write-Host "  - No $Description found" -ForegroundColor Green
    }
}

# Function to check port availability
function Test-PortAvailability {
    param($Port, $Description)

    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($connections) {
        Write-Host "  WARNING: Port $Port still in use" -ForegroundColor Red
    }
    else {
        Write-Host "  - Port $Port is free" -ForegroundColor Green
    }
}

# Main cleanup process
Write-Host "Starting comprehensive cleanup..." -ForegroundColor Cyan
Write-Host ""

# 1. Stop all application processes
Stop-ProcessSafely "electron" "1/10"
Stop-ProcessSafely "node" "2/10"
Stop-ProcessSafely "python" "3/10"

# 2. Wait for processes to terminate
Write-Host "[4/10] Waiting for processes to terminate..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 3. Clean up temporary files
Clean-Directory "temp" "5/10 - Temporary files"

# 4. Clean up cache files
Clean-Directory ".cache" "6/10 - Cache files"

# 5. Clean up old log files
Clean-FilesByPattern "*.log" "7/10 - Old log files" 7

# 6. Clean up Python cache
Clean-FilesByPattern "__pycache__" "8/10 - Python cache" 1

# 7. Clean up database lock files
Write-Host "[9/10] Cleaning database lock files..." -ForegroundColor Yellow
$lockFiles = @("compliance.db-shm", "compliance.db-wal")
foreach ($file in $lockFiles) {
    if (Test-Path $file) {
        try {
            Remove-Item -Path $file -Force -ErrorAction SilentlyContinue
            Write-Host "  - Removed $file" -ForegroundColor Gray
        }
        catch {
            Write-Host "  - Could not remove $file" -ForegroundColor Red
        }
    }
}

# 8. Check port availability
Write-Host "[10/10] Verifying ports are available..." -ForegroundColor Yellow
Test-PortAvailability 8001 "API Server"
Test-PortAvailability 3001 "Frontend"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  COMPREHENSIVE CLEANUP COMPLETE!" -ForegroundColor Green
Write-Host "  All resources have been cleaned up." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Read-Host "Press Enter to exit"
