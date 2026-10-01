#!/usr/bin/env bash
# Publish one assigned Task/Subtask branch from an isolated worker clone.
# This command is privileged-host tooling. Sandboxed workers must never run Git.
#
# Usage:
#   publish_worker_clone.sh <item-id> <worker-clone-path> [target-branch]
#
# target-branch defaults to item-id. Supplying it lets a host caller state the
# destination explicitly, but it is accepted only when it exactly equals the
# assigned item ID. AUTODOCS_DEVEL identifies the canonical local repository
# and defaults to $HOME/devel/autodocs.
set -euo pipefail

PROGRAM="publish_worker_clone"
die() { echo "$PROGRAM: refusing: $*" >&2; exit 1; }

ITEM="${1:-}"
CLONE="${2:-}"
TARGET_BRANCH="${3:-$ITEM}"
DEVEL="${AUTODOCS_DEVEL:-$HOME/devel/autodocs}"

[[ -n "$ITEM" && -n "$CLONE" ]] \
  || die "usage: $0 <item-id> <worker-clone-path> [target-branch]"
[[ "$#" -le 3 ]] || die "too many arguments"

# Publication is intentionally limited to Task and Subtask branches. Feature
# branches are integration boundaries, not worker publication targets.
[[ "$ITEM" =~ ^[0-9]{4}-[0-9]{2}(\.[0-9]{2})?$ ]] \
  || die "invalid assigned item ID '$ITEM'; expected Task XXXX-YY or Subtask XXXX-YY.ZZ"

if [[ "$TARGET_BRANCH" == "main" || "$TARGET_BRANCH" =~ ^[0-9]{4}$ ]]; then
  die "target '$TARGET_BRANCH' is a protected ref (main and bare Feature branches are never publication targets)"
fi
[[ "$TARGET_BRANCH" == "$ITEM" ]] \
  || die "target branch '$TARGET_BRANCH' does not match assigned item ID '$ITEM'"

[[ -e "$CLONE" ]] || die "worker clone path '$CLONE' does not exist"
[[ ! -L "$CLONE" ]] || die "worker clone path '$CLONE' is a symlink"
[[ ! -L "$CLONE/.git" ]] || die "'$CLONE/.git' is a symlink; shared Git topology is forbidden"
[[ -d "$CLONE/.git" ]] \
  || die "'$CLONE/.git' is not a directory; linked worktrees and non-clone Git layouts are forbidden"

CLONE_REAL="$(cd "$CLONE" 2>/dev/null && pwd -P)" \
  || die "cannot resolve worker clone path '$CLONE'"
TOPLEVEL="$(git -C "$CLONE_REAL" rev-parse --show-toplevel 2>/dev/null)" \
  || die "'$CLONE' is not a Git working tree"
TOPLEVEL_REAL="$(cd "$TOPLEVEL" 2>/dev/null && pwd -P)" \
  || die "cannot resolve Git top-level '$TOPLEVEL'"
[[ "$TOPLEVEL_REAL" == "$CLONE_REAL" ]] \
  || die "worker clone path is not the repository top-level ('$TOPLEVEL_REAL')"
[[ "$(git -C "$CLONE_REAL" rev-parse --git-dir 2>/dev/null)" == ".git" ]] \
  || die "worker checkout does not have its own .git directory"
[[ "$(git -C "$CLONE_REAL" rev-parse --git-common-dir 2>/dev/null)" == ".git" ]] \
  || die "worker checkout shares a Git common directory"
[[ ! -e "$CLONE_REAL/.git/objects/info/alternates" ]] \
  || die "worker clone uses a shared/alternate object store"

CURRENT_BRANCH="$(git -C "$CLONE_REAL" symbolic-ref --quiet --short HEAD 2>/dev/null)" \
  || die "worker clone has detached HEAD"
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" =~ ^[0-9]{4}$ ]]; then
  die "source branch '$CURRENT_BRANCH' is a protected ref"
fi
[[ "$CURRENT_BRANCH" == "$ITEM" ]] \
  || die "source branch '$CURRENT_BRANCH' does not match assigned item ID '$ITEM'"

[[ -z "$(git -C "$CLONE_REAL" status --porcelain --untracked-files=all)" ]] \
  || die "worker clone is dirty; commit or remove all tracked and untracked changes before publication"

git -C "$DEVEL" rev-parse --git-dir >/dev/null 2>&1 \
  || die "canonical repository not found at '$DEVEL'"
DEVEL_REAL="$(cd "$DEVEL" 2>/dev/null && pwd -P)" \
  || die "cannot resolve canonical repository path '$DEVEL'"

FETCH_URLS="$(git -C "$CLONE_REAL" remote get-url --all origin 2>/dev/null)" \
  || die "origin remote is missing"
PUSH_URLS="$(git -C "$CLONE_REAL" remote get-url --push --all origin 2>/dev/null)" \
  || die "origin push URL is missing"
[[ -n "$FETCH_URLS" && "$(printf '%s\n' "$FETCH_URLS" | wc -l | tr -d ' ')" == "1" ]] \
  || die "origin must have exactly one fetch URL"
[[ -n "$PUSH_URLS" && "$(printf '%s\n' "$PUSH_URLS" | wc -l | tr -d ' ')" == "1" ]] \
  || die "origin must have exactly one push URL"

resolve_local_repo() {
  local url="$1" path
  case "$url" in
    file://*) path="${url#file://}" ;;
    *://*|*:*) return 1 ;;
    /*) path="$url" ;;
    *) path="$CLONE_REAL/$url" ;;
  esac
  [[ -d "$path" ]] || return 1
  (cd "$path" 2>/dev/null && pwd -P)
}

FETCH_REAL="$(resolve_local_repo "$FETCH_URLS")" \
  || die "origin fetch URL '$FETCH_URLS' is not the canonical local repository"
PUSH_REAL="$(resolve_local_repo "$PUSH_URLS")" \
  || die "origin push URL '$PUSH_URLS' is not the canonical local repository"
[[ "$FETCH_REAL" == "$DEVEL_REAL" ]] \
  || die "origin fetch URL resolves to '$FETCH_REAL', expected canonical '$DEVEL_REAL'"
[[ "$PUSH_REAL" == "$DEVEL_REAL" ]] \
  || die "origin push URL resolves to '$PUSH_REAL', expected canonical '$DEVEL_REAL'"

REMOTE_REF="refs/heads/$ITEM"
REMOTE_LINE="$(git -C "$CLONE_REAL" ls-remote --refs origin "$REMOTE_REF")" \
  || die "cannot inspect canonical target '$REMOTE_REF'"
if [[ -n "$REMOTE_LINE" ]]; then
  git -C "$CLONE_REAL" fetch --quiet --no-tags origin "$REMOTE_REF" \
    || die "cannot fetch canonical target '$REMOTE_REF' for fast-forward verification"
  REMOTE_HEAD="$(git -C "$CLONE_REAL" rev-parse FETCH_HEAD)"
  git -C "$CLONE_REAL" merge-base --is-ancestor "$REMOTE_HEAD" HEAD \
    || die "publication would be non-fast-forward; update '$ITEM' from canonical origin before retrying"
fi

# The fully qualified, non-forced refspec bypasses push.default and configured
# remote push refspecs. Git performs a second atomic fast-forward check, so a
# race after the preflight is also refused rather than overwritten.
if ! git -C "$CLONE_REAL" push --porcelain origin \
  "refs/heads/$ITEM:refs/heads/$TARGET_BRANCH"; then
  die "normal push failed (non-fast-forward and force semantics are never retried)"
fi

echo "OK: published '$ITEM' from '$CLONE_REAL' to canonical origin '$DEVEL_REAL'"
