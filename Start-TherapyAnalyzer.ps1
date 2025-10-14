# Therapy Compliance Analyzer - Universal Launcher
# This script can be run from anywhere and will find the project directory

param(
    [string]$ProjectPath = ""
)

# If no path provided, try to find the project
if (-not $ProjectPath) {
    $possiblePaths = @(
        "C:\Users\kevin\PycharmProjects\Letsgo#999",
        ".\",
        "..\",
        "..\..\"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path "$path\src\api\main.py") {
            $ProjectPath = (Resolve-Path $path).Path
            break
        }
    }
}

if (-not $ProjectPath -or -not (Test-Path "$ProjectPath\src\api\main.py")) {
    Write-Host "ERROR: Could not find Therapy Compliance Analyzer project directory" -ForegroundColor Red
    Write-Host "Please specify the project path:" -ForegroundColor Yellow
    Write-Host "  .\Start-TherapyAnalyzer.ps1 -ProjectPath 'C:\path\to\project'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Found project at: $ProjectPath" -ForegroundColor Green
Set-Location $ProjectPath

# Run the main launcher
& ".\START_THERAPY_ANALYZER.ps1"
