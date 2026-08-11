#!/usr/bin/env bash
# One-way mirror of the volatile /tmp working copy to the durable backup in ~/devel.
#
# DIRECTION IS STRICTLY /tmp -> ~/devel. The destination is a backup and must
# never be edited; anything changed there is overwritten on the next run.
set -euo pipefail

SRC="/private/tmp/ara-api-doku-r2511-edit"
DST="$HOME/devel/ara-api-doku"
LOG="$HOME/devel/ara-api-doku-sync.log"
LOCK="$HOME/devel/.ara-api-doku-sync.lock"

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$*" >>"$LOG"; }

# Never let two hourly runs overlap.
if ! mkdir "$LOCK" 2>/dev/null; then
  log "SKIP: another sync is still running"
  exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT

# --- Safety guards -----------------------------------------------------------
# The source lives on /tmp, which macOS purges on reboot. Without these guards a
# purged or half-populated source would propagate straight into the backup and
# --delete would erase it. When in doubt, do nothing and keep the last good copy.

if [[ ! -d "$SRC/.git" ]]; then
  log "ABORT: source $SRC has no .git — refusing to touch the backup"
  exit 0
fi

if [[ ! -f "$SRC/AGENTS.md" || ! -d "$SRC/_src" ]]; then
  log "ABORT: source is missing expected project files — refusing to sync"
  exit 0
fi

# A healthy tree has tens of thousands of files. Anything far below that means
# the source is being purged or rebuilt right now.
# Count the complete tree. Do not cap find with head: under pipefail that gives
# find SIGPIPE and aborts the backup before rsync starts.
SRC_FILES=$(find "$SRC/_src" -type f | wc -l | tr -d ' ')
if (( SRC_FILES < 1000 )); then
  log "ABORT: source looks truncated (only $SRC_FILES files under _src) — refusing to sync"
  exit 0
fi

# --- Mirror ------------------------------------------------------------------
mkdir -p "$(dirname "$DST")"

START=$(date +%s)
rsync -a --delete \
  --exclude='output/' \
  --exclude='node_modules/' \
  --exclude='.playwright-browsers/' \
  --exclude='run.sh' \
  "$SRC/" "$DST/"
END=$(date +%s)

HEAD_INFO=$(git -C "$DST" log -1 --format='%h %s' 2>/dev/null || echo 'unknown')
DIRTY=$(git -C "$DST" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
SIZE=$(du -sh "$DST" 2>/dev/null | cut -f1)

log "OK: synced in $((END - START))s | size=$SIZE | HEAD=$HEAD_INFO | uncommitted=$DIRTY"
