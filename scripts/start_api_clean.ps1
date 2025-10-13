Param(
    [string]$Host = '127.0.0.1',
    [int]$Port = 8001,
    [string]$LogLevel = 'INFO'
)

$ErrorActionPreference = 'Stop'

# Stop existing python processes from this repo binding the port
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*Letsgo#999*' } | Stop-Process -Force -ErrorAction SilentlyContinue

# Activate venv and start API
. .\venv_fresh\Scripts\Activate.ps1
$env:HOST = $Host
$env:PORT = "$Port"
$env:LOG_LEVEL = $LogLevel
python scripts\run_api.py
