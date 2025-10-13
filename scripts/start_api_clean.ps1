Param(
    [string]$ApiHost = '127.0.0.1',
    [int]$ApiPort = 8001,
    [string]$LogLevel = 'INFO'
)

$ErrorActionPreference = 'Stop'

# Stop existing python processes from this repo binding the port
Get-Process -Name python -ErrorAction SilentlyContinue |
  Where-Object { $_.Path -like '*Letsgo#999*' } |
  Stop-Process -Force -ErrorAction SilentlyContinue

# Free the port explicitly if any process is bound to it
try {
  Get-NetTCPConnection -LocalPort $ApiPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
} catch { }

# Activate venv and start API
. .\venv_fresh\Scripts\Activate.ps1
$env:HOST = $ApiHost
$env:PORT = "$ApiPort"
$env:LOG_LEVEL = $LogLevel
python scripts\run_api.py
