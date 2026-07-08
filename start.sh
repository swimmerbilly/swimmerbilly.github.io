#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "Starting Personal Assistant backend..."
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt -q
fi
.venv/bin/uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting Personal Assistant frontend..."
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then
  npm install -q
fi
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Personal Assistant is running:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
