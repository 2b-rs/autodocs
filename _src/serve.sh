#!/usr/bin/env bash
# Canonical local preview server for the generated HTML tree and issue store.
# Usage: _src/serve.sh [--port 8100] [--host 0.0.0.0]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
else
  PY="${PYTHON:-python3}"
fi
exec "$PY" "$ROOT/_src/serve.py" "$@"
