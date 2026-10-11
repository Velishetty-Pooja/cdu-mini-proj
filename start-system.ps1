# Indian Traffic Intelligence — Startup Script (Windows PowerShell)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  INDIAN TRAFFIC INTELLIGENCE — AI-POWERED SYSTEM" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$CurrentDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Start FastAPI Backend in background job or window
Write-Host "`n[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
$BackendPath = Join-Path $CurrentDir "backend"
$VenvPython = Join-Path $BackendPath "venv\Scripts\python.exe"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$BackendPath'; & '$VenvPython' -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

# 2. Start Vite Frontend
Write-Host "[2/2] Starting React Vite Frontend on http://localhost:5173..." -ForegroundColor Green
$FrontendPath = Join-Path $CurrentDir "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FrontendPath'; npm run dev"

Start-Sleep -Seconds 2
Write-Host "`nTraffic Intelligence System launched successfully!" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "Backend API & Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
