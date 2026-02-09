#!/usr/bin/env bash
# Start PAT backend and frontend servers
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting backend (uvicorn) on http://localhost:8000 ..."
cd "$SCRIPT_DIR/backend"
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting frontend (vite) on http://localhost:5173 ..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "PAT servers running:"
echo "  Backend:  http://localhost:8000  (PID $BACKEND_PID)"
echo "  Frontend: http://localhost:5173  (PID $FRONTEND_PID)"
echo ""
echo "Run stop.sh or press Ctrl+C to shut them down."

# Write PIDs for stop.sh
echo "$BACKEND_PID" > "$SCRIPT_DIR/.pids"
echo "$FRONTEND_PID" >> "$SCRIPT_DIR/.pids"

# Wait for both; Ctrl+C kills them
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f '$SCRIPT_DIR/.pids'; echo 'Servers stopped.'" EXIT
wait
