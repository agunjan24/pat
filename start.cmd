@echo off
REM Start PAT backend and frontend servers

echo Starting backend (uvicorn) on http://localhost:8000 ...
start "PAT Backend" cmd /c "cd /d %~dp0backend && uvicorn app.main:app --reload --port 8000"

echo Starting frontend (vite) on http://localhost:5173 ...
start "PAT Frontend" cmd /c "cd /d %~dp0frontend && npm run dev"

echo.
echo PAT servers starting in background windows.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo.
echo Run stop.cmd to shut them down.
