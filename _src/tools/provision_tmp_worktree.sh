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
#     Runs only the conservative accepted-worktree reap sweep (no
#     provisioning), useful as a periodic fleet fallback. Defaults to the
#     same worktrees root as above.
#
#   provision_tmp_worktree.sh --finalize-accepted <item> [worktree-path]
#     After current Acceptance is recorded, renames only that item's root
#     claim files from TODO-* to byte-identical DONE-* paths. This stages no
#     commit and removes no worktree; the accepting agent reviews and commits
#     the rename with the Acceptance record.
#
#   provision_tmp_worktree.sh --remove-completed <item> [worktree-path] [accepted-ref]
#     Removes the caller's exact completed item worktree after checking its
#     accepted backlog state, DONE claim, clean/unlocked state, live-process
#     absence, durable branch ref, and accepted authority ref (default: main).
#     It never deletes a branch or tag.
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
# Accepted-worktree reap: after handling the requested target (if any), this
# script scans every *other* registered worktree under the worktrees root.
# It removes only an exact item branch whose own claims have been renamed to
# DONE-* at Acceptance, whose backlog block contains current `Acceptance: ✓`,
# whose HEAD is both pinned by its branch ref and reachable from `main`, and
# whose tree is clean, unlocked, and unused as a process cwd. Historical
# prerequisite TODO-* claims do not count as the item's live lease. Anything
# ambiguous is kept; dirty candidates are surfaced with a recovery pointer.
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

claim_names_item() {
  local file="$1" item="$2"
  awk -F ':' -v want="$item" '
    $1 == "task_id" || $1 == "item_id" {
      value = substr($0, index($0, ":") + 1)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
      if (value == want) found = 1
    }
    END { exit !found }
  ' "$file"
}

worktree_has_item_claim() {
  local dir="$1" prefix="$2" item="$3" f
  for f in "$dir"/"$prefix"-*.md; do
    [[ -f "$f" ]] || continue
    claim_names_item "$f" "$item" && return 0
  done
  return 1
}

item_is_accepted() {
  local dir="$1" item="$2"
  python3 - "$dir" "$item" <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
item = re.escape(sys.argv[2])
header = re.compile(rf"^- \[[xw]\] \*\*{item}\*\*", re.MULTILINE)
next_item = re.compile(r"^- \[[ xwpdu]\] \*\*[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?\*\*", re.MULTILINE)
matches = []
for name in ("TODO.md", "DONE.md"):
    path = root / name
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8")
    for match in header.finditer(text):
        following = next_item.search(text, match.end())
        block = text[match.start():following.start() if following else len(text)]
        matches.append(bool(re.search(r"Acceptance:(?:\*\*)?\s*✓", block)))
sys.exit(0 if len(matches) == 1 and matches[0] else 1)
PY
}

ref_has_item_claim() {
  local ref="$1" prefix="$2" item="$3" item_regex
  # Escape the validated subtask separator so the anchored ERE matches exact identity.
  item_regex="${item//./[.]}"
  git -C "$DEVEL" grep -q -E \
    "^(task_id|item_id):[[:space:]]*${item_regex}[[:space:]]*$" \
    "$ref" -- ":(top)${prefix}-*.md"
}

ref_item_is_accepted() {
  local ref="$1" item="$2"
  python3 - "$DEVEL" "$ref" "$item" <<'PY'
import pathlib
import re
import subprocess
import sys

repo, ref, raw_item = sys.argv[1:]
item = re.escape(raw_item)
header = re.compile(rf"^- \[[xw]\] \*\*{item}\*\*", re.MULTILINE)
next_item = re.compile(r"^- \[[ xwpdu]\] \*\*[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?\*\*", re.MULTILINE)
matches = []
for name in ("TODO.md", "DONE.md"):
    result = subprocess.run(
        ["git", "-C", repo, "show", f"{ref}:{name}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if result.returncode:
        continue
    for match in header.finditer(result.stdout):
        following = next_item.search(result.stdout, match.end())
        block = result.stdout[match.start():following.start() if following else len(result.stdout)]
        matches.append(bool(re.search(r"Acceptance:(?:\*\*)?\s*✓", block)))
sys.exit(0 if len(matches) == 1 and matches[0] else 1)
PY
}

worktree_branch_ref_pins_head() {
  local dir="$1" branch="$2" head ref
  head="$(git -C "$dir" rev-parse HEAD 2>/dev/null)" || return 1
  ref="$(git -C "$DEVEL" rev-parse --verify "refs/heads/$branch" 2>/dev/null)" || return 1
  [[ "$head" == "$ref" ]]
}

worktree_has_live_cwd() {
  local dir="$1"
  command -v lsof >/dev/null 2>&1 || {
    note "SURFACE: cannot prove process-cwd absence for '$dir' because lsof is unavailable"
    return 0
  }
  [[ -n "$(lsof -n -a -d cwd +D "$dir" 2>/dev/null || true)" ]]
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

worktree_is_unlocked() {
  local target_real path
  target_real="$(realpath_dir "$1")" || return 1
  while IFS= read -r path; do
    [[ "$path" == "$target_real" ]] && return 0
  done < <(list_unlocked_worktree_paths)
  return 1
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

# Rename the accepted item's own claims in-place. The accepting agent commits
# these renames together with (or immediately after) the Acceptance record;
# this function intentionally neither commits nor removes the worktree.
finalize_accepted_claims() {
  local item="$1" target="$2" f destination count=0
  derive_parent "$item" >/dev/null \
    || die "invalid item '$item' — expected XXXX, XXXX-YY, or XXXX-YY.ZZ"
  worktree_healthy "$target" || die "'$target' is not a healthy worktree"
  worktree_is_registered "$target" || die "'$target' is not registered under '$DEVEL'"
  item_is_accepted "$target" "$item" \
    || die "refusing: item '$item' does not have exactly one current terminal block with Acceptance: ✓"

  # Complete the full preflight before the first rename so a collision cannot
  # leave a partially finalized claim set.
  for f in "$target"/TODO-*.md; do
    [[ -f "$f" ]] || continue
    claim_names_item "$f" "$item" || continue
    git -C "$target" ls-files --error-unmatch -- "$(basename "$f")" >/dev/null 2>&1 \
      || die "refusing: exact-item claim '$f' is not tracked"
    destination="$target/DONE-${f##*/TODO-}"
    [[ ! -e "$destination" ]] \
      || die "refusing: destination '$destination' already exists"
    count=$((count + 1))
  done
  [[ "$count" -gt 0 ]] || die "refusing: no TODO-* claim names exact item '$item'"

  for f in "$target"/TODO-*.md; do
    [[ -f "$f" ]] || continue
    claim_names_item "$f" "$item" || continue
    destination="DONE-${f##*/TODO-}"
    git -C "$target" mv -- "$(basename "$f")" "$destination"
    note "finalized accepted claim '$(basename "$f")' -> '$destination'"
  done
  note "staged $count accepted-claim rename(s); commit them before removing '$target'"
}

remove_completed_worktree() {
  local item="$1" target="$2" authority_ref="$3" target_real root_real current
  derive_parent "$item" >/dev/null \
    || die "invalid item '$item' — expected XXXX, XXXX-YY, or XXXX-YY.ZZ"
  worktree_healthy "$target" || die "'$target' is not a healthy worktree"
  target_real="$(realpath_dir "$target")"
  root_real="$(realpath_dir "$WT_ROOT")"
  case "$target_real" in
    "$root_real"/*) ;;
    *) die "refusing: '$target_real' is outside configured worktrees root '$root_real'" ;;
  esac
  worktree_is_registered "$target" || die "'$target' is not registered under '$DEVEL'"
  worktree_is_unlocked "$target" || die "refusing: '$target' is locked"
  current="$(worktree_branch "$target")"
  [[ "$current" == "$item" ]] \
    || die "refusing: '$target' is on branch '$current', not exact item branch '$item'"
  git -C "$DEVEL" rev-parse --verify "$authority_ref^{commit}" >/dev/null 2>&1 \
    || die "refusing: accepted authority ref '$authority_ref' is not a commit"
  ref_item_is_accepted "$authority_ref" "$item" \
    || die "refusing: authority ref '$authority_ref' has no unique current Acceptance: ✓ for '$item'"
  ! ref_has_item_claim "$authority_ref" TODO "$item" \
    || die "refusing: authority ref '$authority_ref' still carries TODO-* for exact item '$item'"
  ref_has_item_claim "$authority_ref" DONE "$item" \
    || die "refusing: authority ref '$authority_ref' has no finalized DONE-* claim for exact item '$item'"
  worktree_is_clean "$target" || die "refusing: '$target' has uncommitted or untracked content"
  worktree_branch_ref_pins_head "$target" "$item" \
    || die "refusing: branch ref '$item' does not pin '$target' HEAD"
  ! worktree_has_live_cwd "$target" \
    || die "refusing: a live process has its cwd inside '$target'"

  git -C "$DEVEL" worktree remove "$target_real"
  git -C "$DEVEL" show-ref --verify --quiet "refs/heads/$item" \
    || die "postcondition failed: branch '$item' disappeared after worktree removal"
  note "removed completed owned worktree '$target_real'; branch '$item' retained"
}

# --- Accepted-worktree fallback sweep over every OTHER worktree under $WT_ROOT ---
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

    local branch
    branch="$(worktree_branch "$path")"
    derive_parent "$branch" >/dev/null 2>&1 || continue
    ref_has_item_claim main TODO "$branch" && continue
    ref_has_item_claim main DONE "$branch" || continue
    if ! ref_item_is_accepted main "$branch"; then
      note "SURFACE: main has a DONE-* claim for '$branch' but no unique current Acceptance: ✓"
      continue
    fi
    if ! worktree_is_clean "$path"; then
      note "SURFACE: accepted '$path' has uncommitted or untracked content; not reaped"
      continue
    fi
    if ! worktree_branch_ref_pins_head "$path" "$branch"; then
      note "SURFACE: branch ref '$branch' does not pin '$path' HEAD; not reaped"
      continue
    fi
    if ! git -C "$DEVEL" merge-base --is-ancestor "$(git -C "$path" rev-parse HEAD)" main; then
      continue  # accepted but not in main yet; its owner may use explicit self-cleanup
    fi
    if worktree_has_live_cwd "$path"; then
      note "SURFACE: a live process has its cwd inside '$path'; not reaped"
      continue
    fi

    git -C "$DEVEL" worktree remove "$path"
    git -C "$DEVEL" show-ref --verify --quiet "refs/heads/$branch" \
      || die "postcondition failed: branch '$branch' disappeared after worktree removal"
    note "reaped accepted worktree '$path' (clean, unlocked, main-reachable); branch '$branch' retained"
  done < <(list_unlocked_worktree_paths)
}

# --- Entry point ---
if [[ "${1:-}" == "--reap-only" ]]; then
  root="${2:-$WT_ROOT}"
  WT_ROOT="$root"
  reap_sweep ""
  exit 0
fi

if [[ "${1:-}" == "--finalize-accepted" ]]; then
  item="${2:-}"
  [[ -n "$item" ]] || die "usage: $0 --finalize-accepted <item> [worktree-path]"
  target="${3:-$WT_ROOT/$item}"
  finalize_accepted_claims "$item" "$target"
  exit 0
fi

if [[ "${1:-}" == "--remove-completed" ]]; then
  item="${2:-}"
  [[ -n "$item" ]] || die "usage: $0 --remove-completed <item> [worktree-path]"
  target="${3:-$WT_ROOT/$item}"
  authority_ref="${4:-main}"
  remove_completed_worktree "$item" "$target" "$authority_ref"
  exit 0
fi

BRANCH="${1:-}"
[[ -n "$BRANCH" ]] || die "usage: $0 <item-branch> [worktree-path] | --reap-only [root] | --finalize-accepted <item> [path] | --remove-completed <item> [path] [accepted-ref]"
derive_parent "$BRANCH" >/dev/null \
  || die "invalid item branch '$BRANCH' — expected XXXX, XXXX-YY, or XXXX-YY.ZZ"

TARGET="${2:-$WT_ROOT/$BRANCH}"

provision_one "$BRANCH" "$TARGET"

if [[ "${AUTODOCS_NO_REAP:-0}" != "1" ]]; then
  reap_sweep "$TARGET"
fi

echo "OK: $TARGET on $(git -C "$TARGET" rev-parse --abbrev-ref HEAD) @ $(git -C "$TARGET" rev-parse --short HEAD)"
