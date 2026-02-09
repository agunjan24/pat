#!/usr/bin/env bash
# Stop PAT backend and frontend servers
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/.pids"

if [ -f "$PID_FILE" ]; then
    while read -r pid; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            echo "Stopped PID $pid"
        fi
    done < "$PID_FILE"
    rm -f "$PID_FILE"
    echo "PAT servers stopped."
else
    echo "No .pids file found. Trying to stop by port..."
    lsof -ti:8000 | xargs -r kill 2>/dev/null && echo "Stopped backend on :8000" || echo "No backend found on :8000"
    lsof -ti:5173 | xargs -r kill 2>/dev/null && echo "Stopped frontend on :5173" || echo "No frontend found on :5173"
fi
