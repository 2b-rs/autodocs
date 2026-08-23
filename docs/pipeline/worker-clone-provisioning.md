# Worker Clone Provisioning

**Status:** Normative for Feature `0041` / Task `0041-01`. Replaces the
shared-checkout provisioner `_src/tools/provision_tmp_worktree.sh` (now
SUPERSEDED, kept only for historical reference) with a clone-based one.
Requirements: `RQ-WT-01` … `RQ-WT-05` in
[`../dossiers/re-intake-worker-isolation-and-checkin.md`](../dossiers/re-intake-worker-isolation-and-checkin.md).
Branch naming and parent-branch derivation follow
[`branch-workflow.md`](branch-workflow.md), "Branch topology and naming",
unchanged by this document.

## Why the change

`/tmp/autodocs/.git` used to be a symlink onto the canonical repo's `.git`
(or, via the tool this replaces, a `git worktree` — same failure shape: both
share object store, refs, `HEAD` **and index** with `~/devel/autodocs`). A
commit made in the worker checkout silently moved the canonical tree's
`HEAD` while its working tree stayed put. That alone produced a false "task
never started" reading and a since-withdrawn accusation against the
implementing session. See
[`../dossiers/re-intake-worker-isolation-and-checkin.md`](../dossiers/re-intake-worker-isolation-and-checkin.md),
findings G and J.

The replacement gives each worker checkout its **own** object store, refs,
`HEAD`, and index via a real `git clone`. Work in the clone has zero effect
on the canonical tree. The explicit price of that isolation: **durability
begins at `git push`, not at commit.** A worker's commits that are never
pushed are lost when the clone is reaped or discarded — this is deliberate,
not an oversight (finding J).

## Who runs it, and when

The **privileged host side** runs
[`_src/tools/provision_worker_clone.sh`](../../_src/tools/provision_worker_clone.sh)
once per assigned backlog item, **before** a sandboxed/grunt agent receives
that item to work on (`RQ-WT-05`). Sandboxed agents may not run Git at all
(`SANDBOX.md`) and must never invoke this script themselves; none of the
runner tooling (`runner-host/perplexity-cpu-loop.js`, `runner-host/run-loop.sh`) contains
branch/clone/merge/push functionality, so there is no other legal place for
branch and clone creation to happen (finding I).

Re-running the script against an already-provisioned item is safe and
expected — e.g. after a nightly `/tmp` reap, or simply to confirm the clone
is still healthy before handing off a resumed claim.

## Inputs

| Input | Form | Default |
|---|---|---|
| Item ID (positional arg, required) | `XXXX` (Feature), `XXXX-YY` (Task), or `XXXX-YY.ZZ` (Subtask) | — |
| `AUTODOCS_DEVEL` (env, optional) | path to the canonical repo | `$HOME/devel/autodocs` |
| `AUTODOCS_WORKER_TARGET` (env, optional) | path for the worker clone | `/private/tmp/autodocs-<item-id>` |

The item ID format is validated strictly; anything else is rejected before
any Git command runs.

## What it does

1. Derives the branch name (the bare item ID) and the parent branch per
   `branch-workflow.md`: Subtask → its Task branch, Task → its Feature
   branch, Feature → `main`. If the derived parent branch does not exist yet
   in the canonical repo, it falls back to `main` and prints an explicit
   notice — it never guesses further up the chain.
2. Creates the item's branch in the canonical repo from the parent branch if
   it does not already exist; reuses it unchanged otherwise.
3. Clones the canonical repo (`git clone --no-hardlinks --branch <item>`)
   into the target path, giving the worker checkout its own object store,
   refs, `HEAD`, and index.
4. Prints one final line: target path, branch, and `HEAD` short SHA.

## What it refuses, and why

The script fails closed — non-zero exit, and a message naming exactly what
was found — when the target path already exists as one of:

- **A `.git` symlink.** This is the exact construction that caused the
  original incident; the script names the symlink target and refuses rather
  than silently continuing on a shared object store.
- **A registered `git worktree` of the canonical repository.** Checked
  against `git -C <canonical-repo> worktree list`; the script names the
  canonical repo path and tells the operator how to remove the worktree
  registration if that is really intended.
- **A directory holding local commits, or uncommitted changes, not yet
  present in the canonical repo's object store** — i.e. work that has not
  been pushed. The script never rebuilds a checkout out from under
  unpublished work; it stops and asks for the work to be pushed or manually
  resolved first.

## Idempotence and reap recovery

If the target is already a healthy clone on the correct branch, the script
does not rebuild it. It only restores tracked files that a `/tmp` reap
deleted (`git ls-files -d` → `git checkout --`), and never touches
uncommitted or untracked edits — the same non-destructive reap-recovery
behavior the superseded worktree-based script had, reimplemented on top of
an isolated clone instead of a shared one.

If the target exists but is not a healthy, self-contained clone (e.g. a
partially reaped `.git`, or checked out on an unexpected branch) **and**
carries no unpushed local work, the script removes and re-clones it. If it
does carry unpushed local work, that falls under the refusal above instead.

## Publication

This script only provisions the checkout; it does not push. Publication of
worker results by `git push`, and the item-scoped push guard that refuses a
push whose target branch does not match the assigned item ID, are the
subject of Task `0041-04` (`RQ-WT-03`, `RQ-WT-06`) and are not yet
implemented as of this document.
