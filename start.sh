#!/usr/bin/env bash
# start.sh — entrypoint for HuggingFace Spaces and local Docker runs
set -euo pipefail

cd /app

echo "[start.sh] Starting Drug-Triage-Env server on port 7860..."

exec python -m uvicorn server.app:app \
    --host 0.0.0.0 \
    --port 7860 \
    --workers 1 \
    --log-level info
