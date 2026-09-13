#!/usr/bin/env bash
# Provision an isolated worker checkout for one backlog item by real git clone.
# This is the privileged-host replacement for provision_tmp_worktree.sh.
#
# A clone has its own object store, refs, HEAD, and index. Worker commits are
# durable in the canonical repository only after an explicit push. Sandboxed
# agents do not invoke this script because they may not execute Git.
#
# Usage: provision_worker_clone.sh <XXXX|XXXX-YY|XXXX-YY.ZZ>
# Optional environment:
#   AUTODOCS_DEVEL          canonical repository path, default $HOME/devel/autodocs
#   AUTODOCS_WORKER_TARGET  worker clone path, default /private/tmp/autodocs-<item>
#
# The exact branch parent is Feature for a Task, Task for a Subtask, and main
# for a Feature. A missing derived parent is refused; work is never silently
# based on a different branch. Existing targets are never rebuilt automatically:
# a partial reap can leave worker edits that cannot safely be distinguished from
# intentional edits.
set -euo pipefail

die() { echo "provision_worker_clone: $*" >&2; exit 1; }
note() { echo "provision_worker_clone: $*" >&2; }

DEVEL="${AUTODOCS_DEVEL:-$HOME/devel/autodocs}"
ITEM="${1:-}"
[[ -n "$ITEM" ]] || die "usage: $0 <item-id>  (for example 0041-01, 0038, 0038-01.01)"
[[ -d "$DEVEL/.git" ]] || die "canonical repository not found at $DEVEL"
DEVEL="$(cd "$DEVEL" && pwd -P)"

if [[ "$ITEM" =~ ^([0-9]{4})-([0-9]{2})\.([0-9]{2})$ ]]; then
  PARENT="${BASH_REMATCH[1]}-${BASH_REMATCH[2]}"
elif [[ "$ITEM" =~ ^([0-9]{4})-([0-9]{2})$ ]]; then
  PARENT="${BASH_REMATCH[1]}"
elif [[ "$ITEM" =~ ^[0-9]{4}$ ]]; then
  PARENT="main"
else
  die "invalid item ID $ITEM; expected XXXX, XXXX-YY, or XXXX-YY.ZZ"
fi
BRANCH="$ITEM"
git -C "$DEVEL" show-ref --verify --quiet "refs/heads/$PARENT" \
  || die "derived parent branch $PARENT for $ITEM does not exist in canonical repo; refusing to create a branch from a different parent"

TARGET="${AUTODOCS_WORKER_TARGET:-/private/tmp/autodocs-${ITEM}}"
[[ ! -L "$TARGET" ]] \
  || die "refusing: target $TARGET is a symlink; worker targets must be real directories with their own Git metadata"
[[ ! -L "$TARGET/.git" ]] \
  || die "refusing: $TARGET/.git is a symlink to $(readlink "$TARGET/.git"); that shares repository state with another checkout"

if [[ -e "$TARGET" ]]; then
  target_real="$(cd "$TARGET" 2>/dev/null && pwd -P || true)"
  if [[ -n "$target_real" ]]; then
    worktree_listing="$(git -C "$DEVEL" worktree list --porcelain)" \
      || die "cannot inspect registered worktrees in canonical repo $DEVEL"
    while IFS= read -r worktree_line; do
      case "$worktree_line" in
        worktree\ *)
          worktree_path="${worktree_line#worktree }"
          [[ "$worktree_path" != "$target_real" ]] \
            || die "refusing: target $TARGET is a registered git worktree of canonical repo $DEVEL"
          ;;
      esac
    done <<< "$worktree_listing"
  fi
fi

clone_healthy() {
  local metadata metadata_link origin origin_real
  [[ -d "$TARGET" && -d "$TARGET/.git" && ! -L "$TARGET/.git" ]] || return 1
  metadata_link="$(find "$TARGET/.git" -type l -print -quit)" || return 1
  [[ -z "$metadata_link" ]] || return 1
  for metadata in HEAD index objects refs; do
    [[ ! -L "$TARGET/.git/$metadata" ]] || return 1
  done
  [[ ! -e "$TARGET/.git/objects/info/alternates" && ! -L "$TARGET/.git/objects/info/alternates" ]] || return 1
  git -C "$TARGET" rev-parse --git-dir >/dev/null 2>&1 || return 1
  [[ "$(git -C "$TARGET" rev-parse --git-dir)" == ".git" ]] || return 1
  origin="$(git -C "$TARGET" remote get-url origin 2>/dev/null)" || return 1
  origin_real="$(cd "$origin" 2>/dev/null && pwd -P)" || return 1
  [[ "$origin_real" == "$DEVEL" ]]
}

if [[ -e "$TARGET" ]]; then
  clone_healthy || die "refusing: target $TARGET is not a healthy self-contained clone of canonical repo $DEVEL; preserving all surviving bytes for manual recovery"
  current_branch="$(git -C "$TARGET" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  [[ "$current_branch" == "$BRANCH" ]] \
    || die "refusing: healthy target $TARGET is on branch $current_branch, not requested item branch $BRANCH; preserving it unchanged"
  git -C "$DEVEL" show-ref --verify --quiet "refs/heads/$BRANCH" \
    || die "refusing: target $TARGET has item branch $BRANCH but canonical repo does not; preserving the worker clone unchanged"
fi

# Only safe target checks precede canonical branch creation. This updates a ref
# but leaves canonical HEAD, index, working tree, and porcelain status unchanged.
if git -C "$DEVEL" show-ref --verify --quiet "refs/heads/$BRANCH"; then
  note "branch $BRANCH already exists in canonical repo; reusing it unchanged"
else
  if git -C "$DEVEL" branch "$BRANCH" "$PARENT"; then
    note "created branch $BRANCH from exact parent $PARENT"
  else
    die "failed to create item branch $BRANCH from exact parent $PARENT"
  fi
fi

if [[ -e "$TARGET" ]]; then
  note "$TARGET is already a healthy clone on $BRANCH; reusing without modifying worker files"
else
  if git clone --no-hardlinks --branch "$BRANCH" -- "$DEVEL" "$TARGET"; then
    note "cloned $BRANCH into $TARGET"
  else
    die "failed to clone item branch $BRANCH into $TARGET"
  fi
fi

clone_healthy || die "failed to bring $TARGET to a healthy self-contained clone of canonical repo $DEVEL"
echo "OK: $TARGET on $(git -C "$TARGET" rev-parse --abbrev-ref HEAD) @ $(git -C "$TARGET" rev-parse --short HEAD)"
