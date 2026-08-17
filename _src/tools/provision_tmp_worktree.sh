#!/usr/bin/env bash
# Provision / re-heal the disposable /tmp working checkout of this repo.
#
# The canonical repo lives durably in ~/devel/autodocs. Sandboxed agents can
# only reach /tmp, so /tmp/autodocs is a git *worktree* of the canonical repo on
# the `tmp-work` branch: its .git is a pointer into ~/devel/autodocs/.git, so any
# commit made there is instantly durable in the shared object store.
#
# macOS/BeyondTrust reaps /tmp nightly (~00:00), deleting dormant files. This
# script is idempotent: run it any time to bring /tmp/autodocs back to a healthy
# state without discarding uncommitted agent work that survived.
#
# MUST run from a context that can read ~/devel (privileged agent or a
# LaunchAgent) — never from inside the /tmp-only sandbox.
set -euo pipefail

DEVEL="${AUTODOCS_DEVEL:-$HOME/devel/autodocs}"
TMP="${AUTODOCS_TMP:-/private/tmp/autodocs}"
BRANCH="${AUTODOCS_TMP_BRANCH:-tmp-work}"

die() { echo "provision_tmp_worktree: $*" >&2; exit 1; }

[[ -d "$DEVEL/.git" ]] || die "canonical repo not found at $DEVEL"

# Ensure the work branch exists in the canonical repo.
git -C "$DEVEL" show-ref --verify --quiet "refs/heads/$BRANCH" \
  || git -C "$DEVEL" branch "$BRANCH"

# Drop any stale worktree registration whose directory was reaped.
git -C "$DEVEL" worktree prune

worktree_healthy() {
  [[ -e "$TMP/.git" ]] && git -C "$TMP" rev-parse --git-dir >/dev/null 2>&1
}

if worktree_healthy; then
  # Pointer intact. Restore ONLY reaped (deleted) tracked files so we never
  # clobber uncommitted edits that survived the reap. Portable (bash 3.2).
  count=$(git -C "$TMP" ls-files -d | wc -l | tr -d ' ')
  if [ "$count" -gt 0 ]; then
    git -C "$TMP" ls-files -d -z | xargs -0 git -C "$TMP" checkout --
    echo "restored $count reaped file(s)"
  fi
elif [[ -d "$TMP" ]]; then
  # Directory survived but the .git pointer was reaped: try repair, else rebuild.
  git -C "$DEVEL" worktree repair "$TMP" 2>/dev/null || true
  if ! worktree_healthy; then
    rm -rf "$TMP"
    git -C "$DEVEL" worktree prune
    git -C "$DEVEL" worktree add "$TMP" "$BRANCH"
  fi
else
  # Whole checkout gone: recreate it.
  git -C "$DEVEL" worktree add "$TMP" "$BRANCH"
fi

worktree_healthy || die "failed to bring $TMP to a healthy state"
echo "OK: $TMP on $(git -C "$TMP" rev-parse --abbrev-ref HEAD) @ $(git -C "$TMP" rev-parse --short HEAD)"
