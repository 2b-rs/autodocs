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
runner tooling (`_src/perplexity-cpu-loop.js`, `_src/run-loop.sh`) contains
branch/clone/merge/push functionality, so there is no other legal place for
branch and clone creation to happen (finding I).

Re-running the script is safe for an existing healthy clone on the assigned
item branch, or after a complete `/tmp` reap that leaves no target directory.
A partial reap with surviving bytes is refused for manual recovery.

## Inputs

| Input | Form | Default |
|---|---|---|
| Item ID (positional arg, required) | `XXXX` (Feature), `XXXX-YY` (Task), or `XXXX-YY.ZZ` (Subtask) | — |
| `AUTODOCS_DEVEL` (env, optional) | path to the canonical repo | `$HOME/devel/autodocs` |
| `AUTODOCS_WORKER_TARGET` (env, optional) | path for the worker clone | `/private/tmp/autodocs-<item-id>` |

The item ID format is validated strictly; anything else is rejected before
any Git command runs.

## What it does

1. Derives the bare item branch and its **exact** parent from
   `branch-workflow.md`: Subtask → Task branch, Task → Feature branch, Feature
   → `main`. The derived parent must already exist. A missing parent is a
   non-zero refusal; the provisioner never falls back to another branch.
2. Checks the requested target before creating an item branch. It rejects every
   unsafe existing target without changing canonical refs, `HEAD`, index, or
   working-tree status.
3. Creates the item branch from that exact parent only when the branch is
   absent. This changes one canonical ref but leaves the checked-out canonical
   branch, index, and porcelain status unchanged.
4. Creates a self-contained checkout with
   `git clone --no-hardlinks --branch <item>` when the target is absent.
5. Reuses an already healthy clone on the requested item branch without any
   checkout, reset, clean, restore, or other worker-file mutation.

## What it refuses, and why

The script fails closed with a non-zero exit and a message identifying the
observed condition when the target is:

- **A target-path symlink or a `.git` symlink.** Either can redirect the
  provisioner to another checkout and defeat independent worker metadata.
- **A registered `git worktree` of the canonical repository.** The target is
  compared to `git -C <canonical> worktree list` after physical-path
  normalization.
- **Anything other than a healthy self-contained clone.** This includes a
  partial reap that removed `.git` while files survived, a worktree metadata
  file, a clone with Git object alternates or any linked Git metadata, an
  unrelated origin, an unexpected directory, or a file. The script preserves
  every byte for manual recovery instead of recursively
  deleting or rebuilding it.
- **A healthy clone on another branch, or one whose item branch is absent from
  the canonical repository.** It preserves the existing worker state and
  requires an explicit operator decision rather than changing branch state.

A missing exact parent is rejected before target or canonical-branch mutation.
An invalid target is rejected before canonical item-branch creation.

## Idempotence and reap recovery

An already healthy clone on the requested branch is a strict no-op with respect
to its index, tracked files, untracked files, staged changes, modifications, and
intentional deletions. The provisioner does not try to infer whether a missing
tracked file was removed by a reap or by its worker.

A complete reap leaves no target directory, so a later invocation safely creates
a fresh clone. A partial reap that leaves any target content is intentionally not
self-healed: the remaining bytes can include uncommitted worker work, and the
only safe automatic behavior is an explicit refusal with recovery instructions.

## Publication

This script only provisions the checkout; it does not push. Publication of
worker results by `git push`, and the item-scoped push guard that refuses a
push whose target branch does not match the assigned item ID, are the
subject of Task `0041-04` (`RQ-WT-03`, `RQ-WT-06`) and are not yet
implemented as of this document.
