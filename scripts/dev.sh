#!/bin/sh

set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
frontend_port=${FRONTEND_PORT:-5173}
backend_port=${BACKEND_PORT:-8000}
python_bin="$root_dir/.venv/bin/python"

if [ ! -x "$python_bin" ]; then
  echo "Missing project virtual environment: $python_bin" >&2
  echo "Create it and install backend dependencies before running npm run dev." >&2
  exit 1
fi

cleanup() {
  trap - EXIT INT TERM
  [ -n "${frontend_pid:-}" ] && kill "$frontend_pid" 2>/dev/null || true
  [ -n "${backend_pid:-}" ] && kill "$backend_pid" 2>/dev/null || true
  wait 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo "Starting API at http://127.0.0.1:$backend_port"
(cd "$root_dir" && exec "$python_bin" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port "$backend_port" --reload) &
backend_pid=$!

echo "Starting web app at http://127.0.0.1:$frontend_port"
(cd "$root_dir" && VITE_API_BASE_URL="http://127.0.0.1:$backend_port/api/v1" exec npm --prefix frontend run dev -- --host 127.0.0.1 --port "$frontend_port" --strictPort) &
frontend_pid=$!

while :; do
  if ! kill -0 "$backend_pid" 2>/dev/null; then
    wait "$backend_pid"
    exit $?
  fi
  if ! kill -0 "$frontend_pid" 2>/dev/null; then
    wait "$frontend_pid"
    exit $?
  fi
  sleep 1
done
