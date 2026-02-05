# PowerShell script to start the CPG Conversational AI Chatbot
# Usage: .\start_chatbot.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "CPG Conversational AI Chatbot" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location -Path $PSScriptRoot

# Check if Python is available
$pythonCmd = $null

# Try different Python commands
$pythonCommands = @("python", "py", "python3")

foreach ($cmd in $pythonCommands) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            Write-Host "[OK] Found Python: $version" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if ($null -eq $pythonCmd) {
    Write-Host "[ERROR] Python is not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python from:" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or if Python is installed, try:" -ForegroundColor Yellow
    Write-Host "  python frontend\app.py" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Starting the web server..." -ForegroundColor Green
Write-Host ""
Write-Host "Open your browser and go to: " -NoNewline
Write-Host "http://localhost:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Start the Flask app
try {
    & $pythonCmd frontend\app.py
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to start the chatbot!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
