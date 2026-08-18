# Worker Clone Provisioning

**Status:** Normative for Feature `0041` / Tasks `0041-01` and `0041-04`.
Replaces the shared-checkout provisioner
`_src/tools/provision_tmp_worktree.sh` (now SUPERSEDED, kept only for
historical reference) with clone-based provisioning and guarded publication.
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

Provisioning and publication are separate privileged-host operations. The
sandboxed worker receives the already-provisioned clone and edits files there,
but **never runs Git**. After the worker phase has produced the required
self-describing commit, the privileged host publishes it with
[`_src/tools/publish_worker_clone.sh`](../../_src/tools/publish_worker_clone.sh).

Exact operator sequence for a Task or Subtask:

```sh
AUTODOCS_DEVEL="$HOME/devel/autodocs" \
AUTODOCS_WORKER_TARGET="/private/tmp/autodocs-0041-04" \
  _src/tools/provision_worker_clone.sh 0041-04

# Hand the provisioned path to the sandboxed worker. The worker edits files;
# privileged-host check-in handling creates the commit. The worker runs no Git.

AUTODOCS_DEVEL="$HOME/devel/autodocs" \
  _src/tools/publish_worker_clone.sh \
  0041-04 /private/tmp/autodocs-0041-04 0041-04
```

The third publication argument is optional and defaults to the assigned item
ID. Supplying it is recommended for host automation because it states the push
destination explicitly; any value other than the assigned item ID is refused.
The command accepts only Task (`XXXX-YY`) and Subtask (`XXXX-YY.ZZ`) IDs. It
never publishes `main` or a bare Feature (`XXXX`) branch.

Before pushing, the publisher verifies all of these conditions and exits
non-zero with a refusal message if any fails:

- the checkout has its own real `.git` directory and common directory, not a
  symlink, linked worktree, or alternate/shared object store;
- `HEAD` is attached and its source branch is exactly the assigned item ID;
- the explicit/default target branch is exactly that same item ID and is not a
  protected ref;
- the worktree and index are clean, including untracked files;
- `origin` has exactly one fetch URL and one push URL, both resolving to the
  canonical local repository named by `AUTODOCS_DEVEL`;
- the canonical item branch is an ancestor of the worker `HEAD`, when it
  already exists.

The final command uses a fully qualified source/destination refspec and a
normal `git push`; it never requests force and never retries a rejected push
with force semantics. Git's receive-side fast-forward check remains the final
race-safe guard after the explicit preflight.

This implements the standalone privileged-host publication boundary only.
Wiring it into `_src/perplexity-cpu-loop.js`, `_src/run-loop.sh`, or other
active host loops is deliberately deferred: those paths are concurrently
owned and Task `0041-04` does not claim integration into them. Task `0041-05`
performs the end-to-end integration examination.
