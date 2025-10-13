Param(
    [string]$BaseUrl = 'http://127.0.0.1:8001',
    [string]$Username = 'admin',
    [string]$Password = 'admin123',
    [string]$FilePath = 'test_data\good_note_1.txt',
    [int]$PollSeconds = 2,
    [int]$MaxPolls = 15
)

$ErrorActionPreference = 'Stop'

function Get-Token {
    try {
        # Prefer dev-token when available (mock/dev mode)
        $resp = Invoke-RestMethod -Method Get -Uri "$BaseUrl/auth/dev-token" -ErrorAction SilentlyContinue
        if ($resp -and $resp.access_token) { return $resp.access_token }
    } catch { }
    $body = @{ username = $Username; password = $Password }
    $resp = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/token" -ContentType 'application/x-www-form-urlencoded' -Body $body
    return $resp.access_token
}

Write-Host "Getting token..."
$token = Get-Token
$headers = @{ Authorization = "Bearer $token" }
Write-Host "Token OK"

Write-Host "Listing rubrics..."
Invoke-RestMethod -Method Get -Uri "$BaseUrl/rubrics?limit=5" -Headers $headers | ConvertTo-Json -Depth 5 | Write-Output

Write-Host "Submitting analysis..."
$form = @{ file = Get-Item $FilePath; discipline = 'pt'; analysis_mode = 'rubric' }
$submit = Invoke-RestMethod -Method Post -Uri "$BaseUrl/analysis/submit" -Headers $headers -Form $form
$taskId = $submit.task_id
Write-Host "Task ID:" $taskId

Write-Host "Polling status..."
for ($i = 0; $i -lt $MaxPolls; $i++) {
    Start-Sleep -Seconds $PollSeconds
    $status = Invoke-RestMethod -Method Get -Uri "$BaseUrl/analysis/status/$taskId" -Headers $headers
    $status | ConvertTo-Json -Depth 6 | Write-Output
    if ($status.status -eq 'completed') { break }
}

Write-Host "Done."
