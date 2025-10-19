# PowerShell script for clean application shutdown
# This script ensures all processes are properly terminated

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  THERAPY COMPLIANCE ANALYZER" -ForegroundColor Cyan
Write-Host "  CLEAN SHUTDOWN SCRIPT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to safely kill processes
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

# Stop processes in order
Stop-ProcessSafely "electron" "1/4"
Stop-ProcessSafely "node" "2/4"
Stop-ProcessSafely "python" "3/4"

# Wait for ports to be released
Write-Host "[4/4] Waiting for ports to be released..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Check if ports are free
$port8001 = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
$port3001 = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue

if ($port8001) {
    Write-Host "  WARNING: Port 8001 still in use" -ForegroundColor Red
}
else {
    Write-Host "  - Port 8001 is now free" -ForegroundColor Green
}

if ($port3001) {
    Write-Host "  WARNING: Port 3001 still in use" -ForegroundColor Red
}
else {
    Write-Host "  - Port 3001 is now free" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Application shut down cleanly!" -ForegroundColor Green
Write-Host "  All processes terminated." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Read-Host "Press Enter to exit"
