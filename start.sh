#!/usr/bin/env bash
# start.sh — entrypoint for HuggingFace Spaces and local Docker runs
set -euo pipefail

cd /app

echo "[start.sh] Starting Drug-Triage-Env server on port ${PORT:-7860}..."

exec python -m uvicorn server.app:app \
    --host 0.0.0.0 \
    --port "${PORT:-7860}" \
    --workers 1 \
    --log-level info \
    --timeout-keep-alive 30
    