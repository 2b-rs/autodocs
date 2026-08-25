#!/usr/bin/env bash
# Provision / idempotently heal a per-item `git worktree` of this repo, and
# reap orphaned scratch worktrees left behind by earlier provisioning
# attempts. Task 0038-22 (Feature 0038).
#
# Scope: this is a **self-service** provisioner for an `unprivileged` or
# `privileged` agent that runs Git directly (SANDBOX.md) and wants an
# isolated working tree for one backlog item, sharing the canonical repo's
# object store and refs the ordinary `git worktree` way. That is exactly the
# `.worktrees/<item>` convention already in wide, live use across this repo
# (e.g. `.worktrees/0019-01`, `.worktrees/0033-01`, `.worktrees/0039-01`,
# `.worktrees/0042-02`, …) by sessions that create and manage their own
# worktree with `git worktree add`.
#
# This is NOT the sandboxed-grunt worker-clone scenario. A sandboxed/grunt
# agent cannot run Git at all (SANDBOX.md) and must never invoke this script;
# a privileged host provisions that agent's isolated checkout with
# `_src/tools/provision_worker_clone.sh` instead, via a real `git clone` with
# its own object store/refs/HEAD/index (docs/pipeline/worker-clone-provisioning.md,
# Feature 0041 Task 0041-01). That script exists because of a real incident
# (docs/dossiers/re-intake-worker-isolation-and-checkin.md, findings G/W1-W3):
# a rogue `.git` *symlink* — not a regular `git worktree`, which this script
# never bypasses — silently shared HEAD/index with the canonical repo and
# produced a false "task never started" reading. `RQ-WT-01..06` in that
# dossier scope the clone requirement specifically to host-provisioned
# sandboxed-grunt checkouts (`RQ-WT-05`); it does not retire `git worktree`
# for an agent managing its own checkout, which is what this script serves.
#
# This script has **worktree lifecycle only**. It provisions/heals a
# worktree for a caller-supplied branch name and reaps disposable scratch
# worktrees; it never merges a prerequisite branch, resolves a merge
# conflict, or otherwise makes a branch/authority policy decision — that is
# owned by Task 0038-20 (the transaction runner's typed branch/merge
# actions). The one mechanical exception, required by this Task's own
# acceptance criteria, is creating a brand-new item branch off its parent
# branch when it does not exist yet (mirroring `provision_worker_clone.sh`'s
# identical, already-accepted precedent) — this is not prerequisite-merge
# policy, it is the same "create ref from a known parent" primitive.
#
# Usage:
#   provision_tmp_worktree.sh <item-branch> [worktree-path]
#     item-branch:   the bare item ID / branch name, XXXX (Feature),
#                     XXXX-YY (Task), or XXXX-YY.ZZ (Subtask) — the
#                     "feature-task.subtask" form named in the Task text.
#     worktree-path: optional explicit target directory. Defaults to
#                     "<worktrees-root>/<item-branch>". Left to the caller's
#                     discretion, matching the acceptance criteria; the
#                     default keeps the existing `.worktrees/` convention.
#
#   provision_tmp_worktree.sh --reap-only [worktrees-root]
#     Runs only the orphan-reap sweep (no provisioning), useful for periodic
#     cleanup. Defaults to the same worktrees root as above.
#
# Env overrides:
#   AUTODOCS_DEVEL           canonical repo path (default: $HOME/devel/autodocs)
#   AUTODOCS_WORKTREES_ROOT  default root under which per-item worktrees are
#                            created/reaped (default: "$DEVEL/.worktrees")
#   AUTODOCS_NO_REAP=1       skip the orphan-reap sweep for this invocation
#
# Idempotence and reap recovery: re-running against a healthy existing
# worktree on the correct branch is a no-op beyond restoring any *tracked*
# file that a reap (e.g. the nightly macOS/BeyondTrust `/tmp` sweep, if the
# caller chose a `/tmp` location) deleted — exactly the same non-destructive
# `git ls-files -d` -> `git checkout --` recovery this script and its sibling
# `provision_worker_clone.sh` have always used. It never touches uncommitted
# or untracked edits.
#
# Never sharing a worktree between agents: `git worktree add` itself refuses
# to check the same branch out into two locations at once, so a genuine
# collision surfaces as a clear Git error rather than silent data loss; this
# script does not attempt to force past that refusal.
#
# Orphan reap: after handling the requested target (if any), this script
# scans every *other* registered worktree under the worktrees root and, for
# each one whose directory still exists:
#   - if it carries an active claim file (any tracked `TODO-*.md` other than
#     `TODO.md`/`DONE.md` at its root) it is left alone unconditionally —
#     that is provenance, not scratch;
#   - else if `git status --porcelain` is non-empty (uncommitted or
#     untracked content) it is SURFACED with a recovery pointer and never
#     deleted;
#   - else (no claim, fully clean) it is reaped via `git worktree remove`.
# Removing a worktree never deletes the branch or its commits — those remain
# safe in the shared object store — so reaping is bounded to disposable
# scratch checkouts, "when in doubt, surface rather than delete."
set -euo pipefail

die() { echo "provision_tmp_worktree: $*" >&2; exit 1; }
note() { echo "provision_tmp_worktree: $*" >&2; }

# Physical (symlink-resolved) path of an existing directory. `git worktree
# list --porcelain` always reports physical paths (e.g. macOS resolves
# /tmp -> /private/tmp, /var -> /private/var); comparing against a
# caller-supplied logical path would silently never match, which would make
# the reap sweep either skip everything it should protect or fail to
# recognize its own just-created target. Only call this on a directory that
# is known to already exist.
realpath_dir() { ( cd "$1" && pwd -P ); }

DEVEL_LOGICAL="${AUTODOCS_DEVEL:-$HOME/devel/autodocs}"
[[ -d "$DEVEL_LOGICAL/.git" ]] || die "canonical repo not found at $DEVEL_LOGICAL"
DEVEL="$(realpath_dir "$DEVEL_LOGICAL")"

WT_ROOT="${AUTODOCS_WORKTREES_ROOT:-$DEVEL/.worktrees}"

# --- Branch/parent derivation (same convention as provision_worker_clone.sh
#     and docs/pipeline/branch-workflow.md, "Branch topology and naming") ---
derive_parent() {
  local item="$1"
  if [[ "$item" =~ ^([0-9]{4})-([0-9]{2})\.([0-9]{2})$ ]]; then
    echo "${BASH_REMATCH[1]}-${BASH_REMATCH[2]}"
  elif [[ "$item" =~ ^([0-9]{4})-([0-9]{2})$ ]]; then
    echo "${BASH_REMATCH[1]}"
  elif [[ "$item" =~ ^[0-9]{4}$ ]]; then
    echo "main"
  else
    return 1
  fi
}

# --- Worktree health/claim/cleanliness helpers ---
worktree_healthy() {
  local dir="$1"
  [[ -e "$dir/.git" ]] || return 1
  git -C "$dir" rev-parse --git-dir >/dev/null 2>&1
}

# Is $1 (an existing directory) registered as a worktree of $DEVEL? Compares
# physical paths so a caller-supplied logical path (e.g. under a symlinked
# /tmp or /var on macOS) still matches Git's own resolved registration.
worktree_is_registered() {
  local target_real
  target_real="$(realpath_dir "$1")" || return 1
  git -C "$DEVEL" worktree list --porcelain \
    | awk -v want="$target_real" '/^worktree /{if (substr($0,10)==want) found=1} END{exit !found}'
}

worktree_branch() {
  git -C "$1" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?'
}

worktree_is_clean() {
  [[ -z "$(git -C "$1" status --porcelain 2>/dev/null)" ]]
}

worktree_has_claim() {
  local dir="$1" f
  for f in "$dir"/TODO-*.md; do
    [[ -e "$f" ]] || continue
    case "$(basename "$f")" in
      TODO.md|DONE.md) continue ;;
      *) return 0 ;;
    esac
  done
  return 1
}

# Parses `git worktree list --porcelain` (blank-line-separated records) and
# prints one path per line for every worktree that is NOT locked. A separate
# awk pass (rather than a shell `case`/`while` nested inside process
# substitution) avoids a known Bash parser ambiguity between an unescaped
# case-pattern `)` and the enclosing `<( ... )` substitution's own paren
# matching.
list_unlocked_worktree_paths() {
  git -C "$DEVEL" worktree list --porcelain | awk '
    /^worktree / { path = substr($0, 10); locked = 0; next }
    /^locked/    { locked = 1; next }
    /^$/         { if (path != "" && !locked) print path; path = ""; locked = 0 }
    END          { if (path != "" && !locked) print path }
  '
}

restore_reaped_tracked_files() {
  local dir="$1" count
  count=$(git -C "$dir" ls-files -d | wc -l | tr -d ' ')
  if [[ "$count" -gt 0 ]]; then
    git -C "$dir" ls-files -d -z | xargs -0 git -C "$dir" checkout --
    note "restored $count reaped tracked file(s) in '$dir'"
  fi
}

# `git worktree add` for a branch that may or may not exist yet: reuse it if
# it does, else create it off the given (already-validated) parent branch —
# mechanical "new ref from a known parent" primitive, not prerequisite-merge
# policy; see header.
add_worktree_for_branch() {
  local target="$1" branch="$2" parent="$3"
  if git -C "$DEVEL" show-ref --verify --quiet "refs/heads/$branch"; then
    git -C "$DEVEL" worktree add "$target" "$branch"
  else
    git -C "$DEVEL" worktree add "$target" -b "$branch" "$parent"
    note "created branch '$branch' from '$parent'"
  fi
  note "provisioned '$target' on '$branch'"
}

# --- Provision/heal one target worktree for one item branch ---
provision_one() {
  local branch="$1" target="$2" parent=""

  git -C "$DEVEL" worktree prune

  if git -C "$DEVEL" show-ref --verify --quiet "refs/heads/$branch"; then
    note "branch '$branch' already exists — reusing as-is"
  else
    parent="$(derive_parent "$branch")" \
      || die "invalid item branch '$branch' — expected XXXX, XXXX-YY, or XXXX-YY.ZZ"
    if [[ "$parent" != "main" ]] && ! git -C "$DEVEL" show-ref --verify --quiet "refs/heads/$parent"; then
      note "parent branch '$parent' (derived for '$branch') not found — falling back to 'main'"
      parent="main"
    fi
    git -C "$DEVEL" show-ref --verify --quiet "refs/heads/$parent" \
      || die "parent branch '$parent' does not exist (and 'main' fallback already applied) — cannot create '$branch'"
  fi

  if worktree_healthy "$target"; then
    local current
    current="$(worktree_branch "$target")"
    if [[ "$current" == "$branch" ]]; then
      restore_reaped_tracked_files "$target"
      note "'$target' is already a healthy worktree on '$branch' — reusing"
      return 0
    fi
    if worktree_is_clean "$target"; then
      note "'$target' exists on unexpected branch '$current' with no uncommitted content — rebuilding on '$branch'"
      git -C "$DEVEL" worktree remove --force "$target"
    else
      die "refusing: '$target' exists on branch '$current' with uncommitted content." \
          " Commit/push or manually resolve, or choose a different target path, before" \
          " re-provisioning it for '$branch'."
    fi
  elif [[ -e "$target" ]]; then
    if worktree_is_registered "$target"; then
      # Registered but directory contents were reaped (e.g. /tmp nightly
      # sweep): the .git pointer file itself may or may not have survived.
      git -C "$DEVEL" worktree repair "$target" 2>/dev/null || true
    fi
    if worktree_healthy "$target"; then
      restore_reaped_tracked_files "$target"
      note "repaired '$target' after external reap"
      return 0
    fi
    # Not a healthy/registered worktree at all. Never blow away a directory
    # that might hold uncommitted, non-Git-tracked content we cannot verify.
    if [[ -n "$(find "$target" -mindepth 1 -print -quit 2>/dev/null)" ]]; then
      die "refusing: '$target' exists, is not a healthy Git worktree, and is not empty." \
          " Inspect and clear it manually, or choose a different target path."
    fi
    rmdir "$target" 2>/dev/null || true
    add_worktree_for_branch "$target" "$branch" "$parent"
  else
    add_worktree_for_branch "$target" "$branch" "$parent"
  fi

  worktree_healthy "$target" || die "failed to bring '$target' to a healthy state"
}

# --- Orphan reap sweep over every OTHER worktree under $WT_ROOT ---
reap_sweep() {
  local skip_target="${1:-}"
  [[ -d "$WT_ROOT" ]] || return 0
  # Resolve to physical paths for comparison: `git worktree list --porcelain`
  # always reports physical paths, and a logical caller-supplied path (e.g.
  # under a symlinked /tmp or /var on macOS) would otherwise never match.
  local wt_root_real skip_real=""
  wt_root_real="$(realpath_dir "$WT_ROOT")"
  [[ -n "$skip_target" && -e "$skip_target" ]] && skip_real="$(realpath_dir "$skip_target")"

  git -C "$DEVEL" worktree prune

  local path
  while IFS= read -r path; do
    [[ -n "$path" ]] || continue
    case "$path" in
      "$wt_root_real"/*) ;;
      *) continue ;;  # never touch a worktree outside the configured root
    esac
    [[ -n "$skip_real" && "$path" == "$skip_real" ]] && continue
    [[ "$path" == "$DEVEL" ]] && continue  # never touch the main worktree

    if [[ ! -e "$path" ]]; then
      continue  # gone from disk; `worktree prune` above already handled it
    fi

    if worktree_has_claim "$path"; then
      continue  # active provenance — never reap
    fi

    if worktree_is_clean "$path"; then
      git -C "$DEVEL" worktree remove --force "$path"
      note "reaped orphaned scratch worktree '$path' (no claim, clean)"
    else
      note "SURFACE: '$path' has uncommitted content and no active claim file." \
           " Not reaped. Recovery: inspect with 'git -C \"$path\" status', commit/push" \
           " or discard as appropriate, or add a claim file if this is active work."
    fi
  done < <(list_unlocked_worktree_paths)
}

# --- Entry point ---
if [[ "${1:-}" == "--reap-only" ]]; then
  root="${2:-$WT_ROOT}"
  WT_ROOT="$root"
  reap_sweep ""
  exit 0
fi

BRANCH="${1:-}"
[[ -n "$BRANCH" ]] || die "usage: $0 <item-branch> [worktree-path]  |  $0 --reap-only [worktrees-root]"
derive_parent "$BRANCH" >/dev/null \
  || die "invalid item branch '$BRANCH' — expected XXXX, XXXX-YY, or XXXX-YY.ZZ"

TARGET="${2:-$WT_ROOT/$BRANCH}"

provision_one "$BRANCH" "$TARGET"

if [[ "${AUTODOCS_NO_REAP:-0}" != "1" ]]; then
  reap_sweep "$TARGET"
fi

echo "OK: $TARGET on $(git -C "$TARGET" rev-parse --abbrev-ref HEAD) @ $(git -C "$TARGET" rev-parse --short HEAD)"
