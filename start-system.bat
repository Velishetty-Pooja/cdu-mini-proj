@echo off
echo ==========================================================
echo   INDIAN TRAFFIC INTELLIGENCE - AI LAUNCHER
echo ==========================================================

set BASE_DIR=%~dp0

echo.
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000...
start "ITI Backend (FastAPI)" cmd /k "cd /d %BASE_DIR%backend && venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Starting React Vite Frontend on http://localhost:5173...
start "ITI Frontend (Vite)" cmd /k "cd /d %BASE_DIR%frontend && npm run dev"

echo.
echo System started successfully!
echo Frontend: http://localhost:5173
echo API Docs: http://127.0.0.1:8000/docs
