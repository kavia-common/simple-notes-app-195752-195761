#!/bin/bash
set -euo pipefail

# Starts the SQLite database visualizer (Express app) on port 5001.
#
# Why this exists:
# - The "Port 5001 is not ready" container error typically indicates the HTTP
#   visualizer service failed to start/bind.
# - We observed the installed `express` package can be corrupted/incomplete
#   (missing express/lib), which causes `require('express')` to fail at runtime.
# - `npm ci` ensures node_modules match package-lock.json and repairs corruption.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VIS_DIR="${SCRIPT_DIR}/db_visualizer"

cd "${VIS_DIR}"

# If node_modules is missing OR express is broken, re-install deterministically.
if [ ! -d "node_modules" ] || ! node -e "require('express'); process.exit(0)" >/dev/null 2>&1; then
  echo "[db_visualizer] Installing Node dependencies with npm ci..."
  npm ci --silent
fi

export PORT="${PORT:-5001}"

echo "[db_visualizer] Starting on 0.0.0.0:${PORT} ..."
exec node server.js --host 0.0.0.0
