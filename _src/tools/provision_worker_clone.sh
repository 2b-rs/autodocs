#!/usr/bin/env bash
# Provision an isolated worker checkout for one backlog item by real `git
# clone` — the privileged-host-run replacement for provision_tmp_worktree.sh
# (see that file's header: SUPERSEDED).
#
# Why a clone and not a worktree/symlink: a `.git` symlink or `git worktree`
# checkout shares object store, refs, HEAD *and index* with the canonical
# repo at $AUTODOCS_DEVEL. A commit made in the worker checkout silently
# moves the canonical tree's HEAD while its working tree stays put — this
# produced a false "task never started" reading and a since-withdrawn
# accusation against a grunt session (see
# docs/dossiers/re-intake-worker-isolation-and-checkin.md, finding G/J).
# A real clone has its own object store, refs, HEAD and index: nothing done
# in the clone is visible in the canonical tree, and nothing is durable
# there until an explicit `git push`. That tradeoff is deliberate (finding
# J): durability begins at push, not at commit.
#
# Sandboxed/grunt agents may not run Git (SANDBOX.md). This script is run by
# the privileged host side, once per assigned backlog item, BEFORE the grunt
# receives work (docs/pipeline/branch-workflow.md, RQ-WT-05).
#
# Usage:
#   _src/tools/provision_worker_clone.sh <item-id>
#     item-id: XXXX            (Feature,  e.g. 0041)
#              XXXX-YY         (Task,     e.g. 0041-01)
#              XXXX-YY.ZZ      (Subtask,  e.g. 0038-01.01)
#
# Env overrides:
#   AUTODOCS_DEVEL          canonical repo path (default: $HOME/devel/autodocs)
#   AUTODOCS_WORKER_TARGET  worker checkout path
#                            (default: /private/tmp/autodocs-<item-id>)
#
# Branch derivation (docs/pipeline/branch-workflow.md, "Branch topology and
# naming"): the branch name is the bare item ID. Its parent branch is the
# Task branch for a Subtask, the Feature branch for a Task, and `main` for a
# Feature. If the derived parent branch does not exist yet, this script
# falls back to `main` and prints a clear notice — it never invents a parent
# branch or guesses further up the chain.
#
# Fail-closed refusals (never silently discarded): the target path is
# refused, with a stated reason and non-zero exit, when it already exists as
# a `.git` symlink, as a registered `git worktree` of the canonical repo, or
# as a directory holding local commits (or uncommitted changes) that are not
# yet present in the canonical repo's object store — i.e. not yet pushed.
#
# Idempotent: re-running against a healthy existing clone on the correct
# branch is a no-op beyond restoring any tracked file that a `/tmp` reap
# deleted (never touches uncommitted or untracked edits).
set -euo pipefail

die() { echo "provision_worker_clone: $*" >&2; exit 1; }
note() { echo "provision_worker_clone: $*" >&2; }

DEVEL="${AUTODOCS_DEVEL:-$HOME/devel/autodocs}"

ITEM="${1:-}"
[[ -n "$ITEM" ]] || die "usage: $0 <item-id>  (e.g. 0041-01, 0038, 0038-01.01)"

[[ -d "$DEVEL/.git" ]] || die "canonical repo not found at $DEVEL"

# --- Derive branch name (bare item ID) and parent branch per convention ---
if [[ "$ITEM" =~ ^([0-9]{4})-([0-9]{2})\.([0-9]{2})$ ]]; then
  PARENT_DEFAULT="${BASH_REMATCH[1]}-${BASH_REMATCH[2]}"
elif [[ "$ITEM" =~ ^([0-9]{4})-([0-9]{2})$ ]]; then
  PARENT_DEFAULT="${BASH_REMATCH[1]}"
elif [[ "$ITEM" =~ ^[0-9]{4}$ ]]; then
  PARENT_DEFAULT="main"
else
  die "invalid item ID '$ITEM' — expected XXXX, XXXX-YY, or XXXX-YY.ZZ"
fi

BRANCH="$ITEM"

PARENT="$PARENT_DEFAULT"
if [[ "$PARENT" != "main" ]] && ! git -C "$DEVEL" show-ref --verify --quiet "refs/heads/$PARENT"; then
  note "parent branch '$PARENT' (derived for '$ITEM') not found in canonical repo — falling back to 'main'"
  PARENT="main"
fi

# --- Ensure the item branch exists in the canonical repo ---
if git -C "$DEVEL" show-ref --verify --quiet "refs/heads/$BRANCH"; then
  note "branch '$BRANCH' already exists in canonical repo — reusing as-is"
else
  git -C "$DEVEL" show-ref --verify --quiet "refs/heads/$PARENT" \
    || die "parent branch '$PARENT' does not exist in canonical repo (and 'main' fallback already applied) — cannot create '$BRANCH'"
  git -C "$DEVEL" branch "$BRANCH" "$PARENT"
  note "created branch '$BRANCH' from '$PARENT'"
fi

TARGET="${AUTODOCS_WORKER_TARGET:-/private/tmp/autodocs-${ITEM}}"

# --- Refusal 1: target .git is a symlink (the exact bug this replaces) ---
if [[ -L "$TARGET/.git" ]]; then
  die "refusing: '$TARGET/.git' is a symlink -> $(readlink "$TARGET/.git")." \
      " That shares object store, refs, HEAD and index with the canonical repo." \
      " Remove it and rerun, or point AUTODOCS_WORKER_TARGET elsewhere."
fi

# --- Refusal 2: target is a registered `git worktree` of the canonical repo ---
if [[ -e "$TARGET" ]]; then
  target_real="$(cd "$TARGET" 2>/dev/null && pwd -P || true)"
  if [[ -n "$target_real" ]]; then
    while IFS= read -r wt_path; do
      if [[ "$wt_path" == "$target_real" ]]; then
        die "refusing: '$TARGET' is a registered 'git worktree' of the canonical repo at '$DEVEL'" \
            " (see: git -C '$DEVEL' worktree list). Remove the worktree registration" \
            " ('git -C \"$DEVEL\" worktree remove ...') or point AUTODOCS_WORKER_TARGET elsewhere."
      fi
    done < <(git -C "$DEVEL" worktree list --porcelain | sed -n 's/^worktree //p')
  fi
fi

# --- Helpers for the "unpushed local work" refusal / idempotence checks ---
clone_healthy() {
  [[ -d "$TARGET/.git" ]] || return 1
  git -C "$TARGET" rev-parse --git-dir >/dev/null 2>&1 || return 1
  # A plain, self-contained clone reports its git-dir as literally ".git".
  # A worktree pointer file resolves to a path inside another repo's .git.
  [[ "$(git -C "$TARGET" rev-parse --git-dir)" == ".git" ]] || return 1
  return 0
}

has_unpushed_commits() {
  local dir="$1" head_sha
  head_sha="$(git -C "$dir" rev-parse HEAD 2>/dev/null)" || return 1
  if git -C "$DEVEL" cat-file -e "${head_sha}^{commit}" 2>/dev/null; then
    return 1  # commit already known to the canonical repo -> already pushed
  fi
  return 0    # commit unknown to the canonical repo -> local-only, unpushed
}

has_uncommitted_changes() {
  [[ -n "$(git -C "$1" status --porcelain 2>/dev/null)" ]]
}

clone_fresh() {
  git clone --no-hardlinks --branch "$BRANCH" -- "$DEVEL" "$TARGET"
}

# --- Refusal 3 / idempotence / rebuild ---
if [[ -e "$TARGET" ]]; then
  if clone_healthy; then
    current_branch="$(git -C "$TARGET" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
    if [[ "$current_branch" == "$BRANCH" ]]; then
      # Idempotent path: restore ONLY reaped (deleted-but-tracked) files so
      # we never clobber uncommitted or untracked edits that survived a
      # /tmp reap. Portable (bash 3.2).
      reaped_count="$(git -C "$TARGET" ls-files -d | wc -l | tr -d ' ')"
      if [[ "$reaped_count" -gt 0 ]]; then
        git -C "$TARGET" ls-files -d -z | xargs -0 git -C "$TARGET" checkout --
        note "restored $reaped_count reaped file(s) in '$TARGET'"
      fi
      note "'$TARGET' is already a healthy clone on '$BRANCH' — reusing"
    else
      if has_unpushed_commits "$TARGET" || has_uncommitted_changes "$TARGET"; then
        die "refusing: '$TARGET' exists on branch '$current_branch' with local commits and/or" \
            " uncommitted changes not present in '$DEVEL' — push or manually resolve before" \
            " re-provisioning it for '$ITEM'."
      fi
      note "'$TARGET' exists on unexpected branch '$current_branch' with no unpushed work — rebuilding on '$BRANCH'"
      rm -rf "$TARGET"
      clone_fresh
    fi
  else
    if [[ -d "$TARGET/.git" ]] && { has_unpushed_commits "$TARGET" || has_uncommitted_changes "$TARGET"; }; then
      die "refusing: '$TARGET' contains local commits and/or uncommitted changes not present" \
          " in '$DEVEL' — push or manually resolve before re-provisioning it for '$ITEM'."
    fi
    note "'$TARGET' exists but is not a healthy self-contained clone — rebuilding"
    rm -rf "$TARGET"
    clone_fresh
  fi
else
  clone_fresh
  note "cloned '$BRANCH' into '$TARGET'"
fi

clone_healthy || die "failed to bring '$TARGET' to a healthy state"

echo "OK: $TARGET on $(git -C "$TARGET" rev-parse --abbrev-ref HEAD) @ $(git -C "$TARGET" rev-parse --short HEAD)"
