@echo off
REM Stop PAT backend and frontend servers

echo Stopping backend (uvicorn) ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING"') do taskkill /PID %%a /F >nul 2>&1

echo Stopping frontend (vite) ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173.*LISTENING"') do taskkill /PID %%a /F >nul 2>&1

echo PAT servers stopped.
