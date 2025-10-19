# ElectroAnalyzer Environment Setup for PowerShell
Write-Host "Setting up ElectroAnalyzer environment..." -ForegroundColor Green

# Generate a secure SECRET_KEY
$secretKey = python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set environment variables
$env:SECRET_KEY = $secretKey
$env:USE_AI_MOCKS = "false"
$env:API_HOST = "127.0.0.1"
$env:API_PORT = "8001"
$env:LOG_LEVEL = "INFO"
$env:DEBUG = "false"
$env:TESTING = "false"

Write-Host "[SUCCESS] Environment variables set!" -ForegroundColor Green
Write-Host "[KEY] SECRET_KEY: $($secretKey.Substring(0,10))..." -ForegroundColor Yellow
Write-Host ""
Write-Host "You can now start your application." -ForegroundColor Cyan
Write-Host ""
Write-Host "To make these permanent, add them to your system environment variables" -ForegroundColor Gray
Write-Host "or create a .env file in your project directory." -ForegroundColor Gray
