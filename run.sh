#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$ROOT_DIR"

REMOTE_URL="https://github.com/2b-rs/autodocs.git"
BRANCH="main"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: $ROOT_DIR is not a Git repository." >&2
  exit 1
fi

# Initialize the local repository only; do not add a remote or push.
git branch -M "$BRANCH"
git add .

if git diff --cached --quiet; then
  echo "Nothing new to commit."
else
  git commit -m "Initial import of AUTOSAR HTML documentation project"
fi

echo
echo "Local repository initialized successfully on branch: $BRANCH"
