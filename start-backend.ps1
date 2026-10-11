# start-backend.ps1 - PowerShell Startup Script for Indian Traffic Intelligence Backend
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Indian Traffic Intelligence Backend (FastAPI)  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$ScriptDir\backend"

# Check for virtual environment (.venv or venv)
$VenvDir = ""
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    $VenvDir = ".\.venv"
} elseif (Test-Path ".\venv\Scripts\Activate.ps1") {
    $VenvDir = ".\venv"
} else {
    Write-Host "Creating Python virtual environment in .venv..." -ForegroundColor Yellow
    python -m venv .venv
    $VenvDir = ".\.venv"
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    & "$VenvDir\Scripts\python.exe" -m pip install --upgrade pip
    & "$VenvDir\Scripts\pip.exe" install -r requirements.txt
}

Write-Host "Activating virtual environment: $VenvDir" -ForegroundColor Green
try {
    & "$VenvDir\Scripts\Activate.ps1"
} catch {
    Write-Warning "PowerShell script execution restricted. Using direct python execution."
}

Write-Host "Starting FastAPI application at http://127.0.0.1:8000..." -ForegroundColor Cyan
Write-Host "Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor Gray
Write-Host "Health Check: http://127.0.0.1:8000/api/health" -ForegroundColor Gray

& "$VenvDir\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
