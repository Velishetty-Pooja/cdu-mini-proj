# start-frontend.ps1 - PowerShell Startup Script for Indian Traffic Intelligence Frontend
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Indian Traffic Intelligence Frontend (Vite)    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$ScriptDir\frontend"

if (-not (Test-Path "node_modules")) {
    Write-Host "node_modules not found. Running npm install..." -ForegroundColor Yellow
    npm install
}

Write-Host "Launching Vite development server..." -ForegroundColor Green
Write-Host "Local URL: http://localhost:5173" -ForegroundColor Cyan

npm run dev
