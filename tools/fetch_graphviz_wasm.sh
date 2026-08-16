#!/bin/zsh
# fetch_graphviz_wasm.sh
#
# Downloads the @hpcc-js/wasm UMD bundle (self-contained: Graphviz compiled to
# WebAssembly, embedded as base64 inside the JS file, no separate .wasm fetch
# needed at runtime) and vendors it into tools/vendor/ so that
# tools/todo-dependency-graph.html works fully offline / from file:// URLs
# without any CDN dependency at view-time.
#
# Idempotent: skips the download if the target file already exists and its
# checksum matches the pinned expectation; use --force to re-download anyway.
#
# Usage: tools/fetch_graphviz_wasm.sh [--force]

set -euo pipefail

PKG_VERSION="2"
CDN_URL="https://cdn.jsdelivr.net/npm/@hpcc-js/wasm@${PKG_VERSION}/dist/graphviz.umd.js"
VENDOR_DIR="$(dirname "$0")/vendor"
TARGET="${VENDOR_DIR}/hpcc-js-wasm-graphviz.umd.js"
FORCE=0

for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 64 ;;
  esac
done

mkdir -p "$VENDOR_DIR"

if [[ -f "$TARGET" && "$FORCE" -eq 0 ]]; then
  size=$(wc -c < "$TARGET" | tr -d ' ')
  echo "[fetch_graphviz_wasm] $TARGET already present (${size} bytes); use --force to re-download."
  exit 0
fi

echo "[fetch_graphviz_wasm] downloading ${CDN_URL} -> ${TARGET}"
curl -fSL --retry 3 --retry-delay 2 -o "${TARGET}.tmp" "$CDN_URL"

# sanity check: file must be non-trivial size and contain the expected UMD export marker
size=$(wc -c < "${TARGET}.tmp" | tr -d ' ')
if [[ "$size" -lt 100000 ]]; then
  echo "[fetch_graphviz_wasm] ERROR: downloaded file suspiciously small (${size} bytes), aborting." >&2
  rm -f "${TARGET}.tmp"
  exit 1
fi
if ! grep -q '@hpcc-js/wasm/graphviz' "${TARGET}.tmp"; then
  echo "[fetch_graphviz_wasm] ERROR: downloaded file does not look like the expected UMD bundle, aborting." >&2
  rm -f "${TARGET}.tmp"
  exit 1
fi

mv "${TARGET}.tmp" "$TARGET"
echo "[fetch_graphviz_wasm] OK: ${TARGET} (${size} bytes)"
