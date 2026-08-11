#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

PUBLISH_DIR="${PUBLISH_DIR:-$ROOT_DIR/output/publish-autodocs}"
REMOTE="${PUBLISH_REMOTE:-git@github.com:2b-rs/autodocs.git}"
BRANCH="${PUBLISH_BRANCH:-main}"
SSH_KEY="${GITHUB_SSH_KEY_PATH:-$HOME/devel/aradocs-runner-key/id_ed25519}"
KNOWN_HOSTS="${GITHUB_KNOWN_HOSTS:-$ROOT_DIR/output/github-known_hosts}"
export GIT_SSH_COMMAND="ssh -i $SSH_KEY -o IdentitiesOnly=yes -o UserKnownHostsFile=$KNOWN_HOSTS"

PUBLIC_DIRS=(ar classes en es flags fr hi ko modules namespaces pt ru services zh)
PUBLIC_FILES=(index.html style.css fold.js review.js)

[[ -d "$PUBLISH_DIR/.git" ]] || git clone "$REMOTE" "$PUBLISH_DIR"
git -C "$PUBLISH_DIR" remote set-url origin "$REMOTE"
git -C "$PUBLISH_DIR" checkout "$BRANCH"
git -C "$PUBLISH_DIR" pull --ff-only origin "$BRANCH"

for dir in "${PUBLIC_DIRS[@]}"; do
  [[ -d "$ROOT_DIR/$dir" ]] || { echo "Missing generated directory: $dir" >&2; exit 1; }
  mkdir -p "$PUBLISH_DIR/$dir"
  rsync -a --delete "$ROOT_DIR/$dir/" "$PUBLISH_DIR/$dir/"
done

for file in "${PUBLIC_FILES[@]}"; do
  [[ -f "$ROOT_DIR/$file" ]] || { echo "Missing public artifact: $file" >&2; exit 1; }
  cp -f "$ROOT_DIR/$file" "$PUBLISH_DIR/$file"
done
touch "$PUBLISH_DIR/.nojekyll"

# Safety guard: source and build directories must never enter the public repo.
for private_path in _src output .gitignore; do
  [[ ! -e "$PUBLISH_DIR/$private_path" ]] || {
    echo "Refusing publish: private path present in artifact repo: $private_path" >&2
    exit 1
  }
done

if [[ -z "$(git -C "$PUBLISH_DIR" status --porcelain)" ]]; then
  echo "No publish changes."
  exit 0
fi

git -C "$PUBLISH_DIR" add -A
git -C "$PUBLISH_DIR" commit -m "Publish regenerated HTML documentation"
git -C "$PUBLISH_DIR" push origin "$BRANCH"

echo "Published: https://2b-rs.github.io/autodocs/"
