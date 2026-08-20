#!/usr/bin/env bash
# Legacy incremental publisher: pushes a curated set of generated public
# artifacts into a persistent local clone of an explicitly configured
# destination repository, then fast-forward-pushes it.
#
# No publication identity or destination is silently assumed: PUBLISH_REMOTE,
# PUBLISH_IDENTITY_NAME, and PUBLISH_IDENTITY_EMAIL must be set explicitly by
# the caller under reviewed operator/service credential policy. There is no
# default that resolves to the public repository.
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

: "${PUBLISH_REMOTE:?PUBLISH_REMOTE is required: the exact reviewed publish destination URL. There is no default; it must never silently resolve to the public repository.}"
: "${PUBLISH_IDENTITY_NAME:?PUBLISH_IDENTITY_NAME is required: the reviewed operator/service commit author/committer name.}"
: "${PUBLISH_IDENTITY_EMAIL:?PUBLISH_IDENTITY_EMAIL is required: the reviewed operator/service commit author/committer email.}"

PUBLISH_DIR="${PUBLISH_DIR:-$ROOT_DIR/output/publish-autodocs}"
BRANCH="${PUBLISH_BRANCH:-main}"
SSH_KEY="${GITHUB_SSH_KEY_PATH:-$HOME/devel/aradocs-runner-key/id_ed25519}"
KNOWN_HOSTS="${GITHUB_KNOWN_HOSTS:-$ROOT_DIR/output/github-known_hosts}"
export GIT_SSH_COMMAND="ssh -i $SSH_KEY -o IdentitiesOnly=yes -o UserKnownHostsFile=$KNOWN_HOSTS"
export GIT_AUTHOR_NAME="$PUBLISH_IDENTITY_NAME"
export GIT_AUTHOR_EMAIL="$PUBLISH_IDENTITY_EMAIL"
export GIT_COMMITTER_NAME="$PUBLISH_IDENTITY_NAME"
export GIT_COMMITTER_EMAIL="$PUBLISH_IDENTITY_EMAIL"

# Durable per-phase outcome/recovery journal: every mutating step below
# records its exit status here immediately, so a crash or early exit under
# `set -e` still leaves a durable record of the last completed phase.
RESULT_LOG="${PUBLISH_RESULT_LOG:-$ROOT_DIR/output/publish-result.log}"
mkdir -p "$(dirname "$RESULT_LOG")"
printf 'phase=init status=%s\n' "$?" >> "$RESULT_LOG"

PUBLIC_DIRS=(ar classes en es flags fr hi ko modules namespaces pt ru services zh)
PUBLIC_FILES=(index.html style.css fold.js review.js)

[[ -d "$PUBLISH_DIR/.git" ]] || git clone "$PUBLISH_REMOTE" "$PUBLISH_DIR"

git -C "$PUBLISH_DIR" remote set-url origin "$PUBLISH_REMOTE"
printf 'phase=remote_set_url status=%s\n' "$?" >> "$RESULT_LOG"

git -C "$PUBLISH_DIR" checkout "$BRANCH"
printf 'phase=checkout status=%s\n' "$?" >> "$RESULT_LOG"

git -C "$PUBLISH_DIR" pull --ff-only origin "$BRANCH"
printf 'phase=pull status=%s\n' "$?" >> "$RESULT_LOG"

for dir in "${PUBLIC_DIRS[@]}"; do
  [[ -d "$ROOT_DIR/$dir" ]] || { echo "Missing generated directory: $dir" >&2; exit 1; }
  mkdir -p "$PUBLISH_DIR/$dir"
  printf 'phase=mkdir_%s status=%s\n' "$dir" "$?" >> "$RESULT_LOG"
  rsync -a --delete "$ROOT_DIR/$dir/" "$PUBLISH_DIR/$dir/"
done

for file in "${PUBLIC_FILES[@]}"; do
  [[ -f "$ROOT_DIR/$file" ]] || { echo "Missing public artifact: $file" >&2; exit 1; }
  cp -f "$ROOT_DIR/$file" "$PUBLISH_DIR/$file"
  printf 'phase=cp_%s status=%s\n' "$file" "$?" >> "$RESULT_LOG"
done
touch "$PUBLISH_DIR/.nojekyll"
printf 'phase=touch_nojekyll status=%s\n' "$?" >> "$RESULT_LOG"

# Safety guard: source and build directories must never enter the public repo.
for private_path in _src output .gitignore; do
  [[ ! -e "$PUBLISH_DIR/$private_path" ]] || {
    echo "Refusing publish: private path present in artifact repo: $private_path" >&2
    exit 1
  }
done

if [[ -z "$(git -C "$PUBLISH_DIR" status --porcelain)" ]]; then
  echo "No publish changes."
  printf 'phase=complete status=0 result=no_changes\n' >> "$RESULT_LOG"
  exit 0
fi

git -C "$PUBLISH_DIR" add -A
printf 'phase=add status=%s\n' "$?" >> "$RESULT_LOG"

git -C "$PUBLISH_DIR" commit -m "Publish regenerated HTML documentation"
printf 'phase=commit status=%s\n' "$?" >> "$RESULT_LOG"

git -C "$PUBLISH_DIR" push origin "$BRANCH"
printf 'phase=push status=%s\n' "$?" >> "$RESULT_LOG"

echo "Published via explicitly configured PUBLISH_REMOTE/PUBLISH_BRANCH; result journal: $RESULT_LOG"
printf 'phase=complete status=0\n' >> "$RESULT_LOG"
