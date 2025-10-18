# Real-time Analysis Monitor
$apiUrl = "http://localhost:8001"

Write-Host "Analysis Monitor Started" -ForegroundColor Green
Write-Host "Monitoring: $apiUrl" -ForegroundColor Cyan
Write-Host ""

while ($true) {
    try {
        $response = Invoke-RestMethod -Uri "$apiUrl/analysis/all-tasks" -Method Get -ErrorAction Stop

        Clear-Host
        Write-Host "=== ANALYSIS MONITOR ===" -ForegroundColor Green
        Write-Host "Time: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
        Write-Host ""

        if ($response -and $response.PSObject.Properties.Count -gt 0) {
            foreach ($taskId in $response.PSObject.Properties.Name) {
                $task = $response.$taskId
                $status = if ($task.status) { $task.status } else { "unknown" }
                $progress = if ($task.progress) { $task.progress } else { 0 }
                $message = if ($task.status_message) { $task.status_message } else { "No message" }
                $filename = if ($task.filename) { $task.filename } else { "Unknown" }

                Write-Host "Task: $taskId" -ForegroundColor Yellow
                Write-Host "File: $filename"
                Write-Host "Status: $status"
                Write-Host "Progress: $progress%"
                Write-Host "Message: $message"

                $barLength = 40
                $filled = [math]::Floor($barLength * $progress / 100)
                $empty = $barLength - $filled
                $bar = "[" + ("=" * $filled) + (" " * $empty) + "]"
                Write-Host $bar -ForegroundColor Green
                Write-Host ""
            }
        }
        else {
            Write-Host "No active tasks" -ForegroundColor Yellow
            Write-Host "Start an analysis in the app to see progress here"
            Write-Host ""
        }

        Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
    }
    catch {
        Write-Host "Cannot connect to API" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
    }

    Start-Sleep -Seconds 2
}
