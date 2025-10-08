#!/usr/bin/env bash 

set -euo pipefail 

PORT="${PORT:-8000}"

exec uv run python -m uvicorn reporter.app:app \
    --host 0.0.0.0 \
    --port "$PORT" 
