# Branch, Merge, and Feature-Integration Workflow

**Status:** Normative legacy-authority process introduced by a user-directed
governance change on 2026-08-17. It governs how agents carry Feature, Task, and
Subtask work on Git branches, how done-but-unaccepted predecessor work is pulled
forward, and how a privileged integrator merges Tasks into a Feature and signs it
off. It complements — and does not replace — the marker/acceptance semantics in
the header of [`../../TODO.md`](../../TODO.md), the collaboration rules in
[`../../AGENTS.md`](../../AGENTS.md), the capability/runner rules in
[`../../SANDBOX.md`](../../SANDBOX.md), and the privileged acceptance procedure in
[`task-acceptance.md`](task-acceptance.md). Where this document adds a branch
mechanic to an existing rule, the existing rule's authority meanings are
unchanged; where it changes the lifetime of a coordination artifact (claim
files), the change is stated explicitly below.

## Purpose and boundary

Backlog markers (`[x]`/`[w]`) already let a Task proceed on an unreviewed
predecessor so that work does not serialize behind privileged review. On disk,
however, that predecessor work must actually be *present* for the successor to
build on it, and the predecessor's coordination and provenance (its claim file)
must not be lost when work moves up the tree. This document makes the carrier for
both explicit: **one branch per backlog item**, merged upward, with claim files
committed alongside work products so they travel with the code.

This document governs *where work lives and how it moves*. It does not grant any
authority. Merging a done-but-unaccepted predecessor into a successor branch does
**not** accept it; task-acceptance `✓` and Feature closure remain exactly as
defined in [`task-acceptance.md`](task-acceptance.md).

## Branch topology and naming

The integration baseline is `main`. Every backlog item has exactly one canonical
branch whose name **is the item's ID**:

| Item | Branch name | Cut from (base) |
|---|---|---|
| Feature `XXXX` | `XXXX` (e.g. `0038`) | `main` |
| Task `XXXX-YY` | `XXXX-YY` (e.g. `0038-01`) | the Feature branch `XXXX` |
| Subtask `XXXX-YY.ZZ` | `XXXX-YY.ZZ` (e.g. `0038-01.01`) | the Task branch `XXXX-YY` |

- A branch is created the first time work on its item begins; it is not created
  speculatively for items no one is working.
- The **parent branch** of a Task is its Feature branch; the parent branch of a
  Subtask is its Task branch. "Base off the parent branch" always means this.
- Branch names are the bare IDs to keep the mapping between backlog and refs
  mechanical. Do not add prefixes, suffixes, timestamps, or agent names to the
  canonical branch; per-attempt scratch worktrees created by the runner are a
  separate, disposable concern (see
  [`runner-transaction.md`](runner-transaction.md)) and are never the canonical
  item branch.

## Claim files and work products travel on the branch

Under this workflow the `TODO-<agent-id>.md` claim file is a tracked artifact on
the item's branch, **committed together with the work products it coordinates**,
and it is carried upward by every merge. This changes the earlier "reconcile and
delete the claim at `[x]`" behavior for branch-based work:

- The implementer commits its claim file on the item's branch alongside the
  deliverables, keeping it current (progress, findings, validation, next step,
  `owner_token`, base commit).
- When a branch is merged into its parent (Subtask→Task, or Task→Feature), the
  claim files on the merged branch are merged in as well. The parent branch
  therefore accumulates the complete set of predecessor claim files, preserving
  who did what and under which authority.
- Claim files are **not** deleted at `[x]`/`[w]`. They are reconciled and removed
  only by the privileged integrator during **Feature integration** (below), after
  their durable information has been folded into the acceptance records and
  check-in provenance. This keeps coordination visible for the whole life of the
  Feature and prevents the "orphaned claim, code committed elsewhere" split.

Everything else about claim files — immutable `owner_token`, no cross-session
appropriation, no ownership inferred from a shared display name or filename —
continues to apply exactly as in [`../../AGENTS.md`](../../AGENTS.md).

## Starting a Task or Subtask: the binding base-and-merge rule

Because a worker may start on a predecessor that is done (`[x]`/`[w]`) but **not
yet accepted and not yet integrated into the parent branch**, and because two
different prerequisites may sit on two different branches, every worker MUST, as
the first mutating step of an item:

1. **Base off the parent branch.** Create or check out the item's branch from its
   parent branch (Task from the Feature branch; Subtask from the Task branch).
   The parent branch is the stable integration point for that level; it is not
   `main` for a Task and not the Feature branch for a Subtask.
2. **Merge in every done-but-unintegrated prerequisite branch.** Compute the
   item's prerequisite closure from `TODO.md`. For each prerequisite that is
   `[x]`/`[w]` and whose work is not already present on the parent branch, merge
   that prerequisite's branch into the item's branch before doing new work. This
   pulls in both the predecessors' **work products** and their **claim files**.
3. **Record the merges in the claim.** List each merged prerequisite branch and
   its tip commit in the item's claim file, so the provenance of the starting
   state is explicit.

Notes and consequences:

- In the common **linear** case the only prerequisite is the immediately
  preceding Task/Subtask; merging its branch is equivalent to continuing from its
  done state. The rule is the same whether work is linear or parallel — always
  base off the parent and merge the closure — so no special case is needed.
- If a prerequisite carries an explicit **acceptance-before-start** gate (see the
  `TODO.md` header and [`task-acceptance.md`](task-acceptance.md)), the worker
  waits for that prerequisite's acceptance; an accepted prerequisite will already
  be integrated into the parent branch, so no extra merge is required.
- A merge that conflicts is resolved by the worker using the normal rules
  (preserve unrelated work, never overwrite another owner's changes). Claim-file
  conflicts are resolved by keeping **all** predecessor claim records, not by
  dropping one side; the point of carrying them is to retain every predecessor's
  provenance.

## Merge authority and direction

Merges only ever move work **up** the tree (Subtask→Task→Feature). Authority
depends on the level:

- **Subtask → Task** may be performed by a **sandboxed/grunt** agent. Ordinarily
  it is the agent that implemented the subtask, but when a Task is parallelized
  across several agents, the Task owner may merge subtask branches authored by
  **different** agents into the Task branch. The merger preserves each subtask's
  claim file and does not alter another agent's `owner_token` or acceptance
  state.
- **Task → Feature** requires a **privileged** agent — the *integrator*. A
  sandboxed/grunt agent must never merge a Task branch into a Feature branch.
- **Feature → `main`** is performed only by the privileged integrator as part of
  Feature closure, after Feature aggregate acceptance
  ([`task-acceptance.md`](task-acceptance.md)).

**Not every Task is individually merged into the Feature.** In the simplest case
a single grunt works the Tasks one after another, each new Task branch based off
the Feature branch and merging in the previous Task branch (which already carries
all earlier done work). The Feature branch itself is not advanced by the grunt.
The privileged integrator later takes the **last** Task branch — which
transitively contains the whole chain — and integrates it into the Feature
branch in one step. When Tasks were genuinely parallel and do not form a single
chain, the integrator merges each independent Task branch that is required for
the Feature.

## Feature integration and sign-off

Feature integration is the privileged step that both merges Task work into the
Feature branch and performs the Feature-level review. The integrator:

1. Confirms current privilege and an explicit assignment to integrate/accept the
   Feature scope (privilege alone is not authority — see
   [`task-acceptance.md`](task-acceptance.md)).
2. Merges the required Task branch(es) into the Feature branch, resolving
   conflicts without discarding any owner's work and carrying up all claim files.
3. Performs the per-Task and Feature aggregate acceptance review defined in
   [`task-acceptance.md`](task-acceptance.md), **adding the review findings and
   acceptance records** on the Feature branch. Task-acceptance `✓` records are
   created here, bottom-up and prerequisite-closed.
4. Reconciles and removes the predecessor claim files whose information is now
   captured in acceptance records and check-in provenance
   ([`../../AGENTS.md`](../../AGENTS.md) → *Check-in provenance*).
5. On full approval, integrates the Feature branch into `main` and moves the
   Feature to `DONE.md` via the path-isolated bookkeeping commit that
   [`task-acceptance.md`](task-acceptance.md) requires.

## Feature integration rejection: the `[u]` verdict

If the integrator does **not** approve a row of Tasks — the evidence shows a
material nonconformity or a decision the integrator may not make alone — the
integrator does not silently fix or force the Feature through. Instead it records
a **Feature-level `[u]` integration verdict** and hands resolution to the user.

Because a Feature heading (`## Feature: XXXX — …`) carries no checkbox marker, the
`[u]` verdict is rendered as a structured record placed directly beneath the
Feature heading:

```markdown
**Integration verdict:** [u] — pending user approval
- **Verdict by:** `<privileged-integrator-identity>`
- **Authority reference:** `<immutable assignment/authority reference>`
- **Recorded at:** `<ISO-8601 timestamp with timezone>`
- **Rejected/blocked tasks:** `<task IDs>`
- **Reason:** `<why integration cannot be approved as-is>`
- **Integration branch:** `<feature branch tip commit under review>`
```

While a Feature carries an `[u]` integration verdict:

- it is **not** integrated into `main` and is **not** moved to `DONE.md`;
- its Task-level markers and any acceptance records keep their own true state
  (the verdict blocks the Feature, it does not rewrite Task history);
- resolution is an explicit **user interaction with the integrating agent**: the
  user directs whether to rework the blocked Tasks (returning them to `[p]`),
  waive/authorize the contested decision, re-scope, or abandon. The integrator
  acts on that direction and appends the outcome append-only; it never clears its
  own `[u]` verdict without the user's decision.

This uses the existing `[u]` meaning ("a human decision is the sole next action")
at Feature granularity; it does not introduce a new marker.

## Capability-class execution of branch operations

Branch creation, checkout, merge, and conflict resolution are Git operations and
therefore follow the capability rules in [`../../SANDBOX.md`](../../SANDBOX.md):

- A **sandboxed/grunt** agent does not run Git directly. It routes every
  branch/base/merge operation through the runner, in a request that preflights
  the expected base, active claim, `owner_token`, and declared read/write scope;
  preserves unrelated work; carries the required check-in provenance; and fails
  closed if any gate differs from the request contract. Grunt-permitted merges
  are limited to Subtask→Task.
- A **privileged** agent may perform branch/merge/integration directly, but must
  preserve the same scope, validation, provenance, and mutation-safety
  guarantees. Task→Feature, Feature→`main`, acceptance records, and the `[u]`
  integration verdict are privileged-only.

## Machine-enforcement and tooling follow-up

This document is immediately binding as instruction. Full machine enforcement is
explicit downstream work and is not implied to exist yet:

- The disposable `/tmp` worktree provisioner
  (`_src/tools/provision_tmp_worktree.sh`) currently pins sandboxed work to a
  single `tmp-work` branch. Per-item branches require it to provision the item's
  canonical branch (base off the parent, merge the prerequisite closure) instead.
- The runner transaction engine
  ([`runner-transaction.md`](runner-transaction.md),
  `_src/tools/runner_transaction.py`) must gain allowlisted, fail-closed
  branch/merge phases so grunts can perform Subtask→Task merges under the same
  preflight/scope/provenance guarantees as commits, and so leftover per-attempt
  scratch worktrees are reaped rather than orphaned.
- Until those exist, the branch mechanics are followed manually under the
  authority rules above, and any tool that cannot preserve claim files,
  acceptance records, or unrelated work must fail closed rather than rewrite the
  branch.

## Worked examples

**Linear Feature, one grunt.** Feature `0040` branch is cut from `main`. The grunt
bases `0040-01` off `0040`, implements, commits work + claim, marks `[x]`. It then
bases `0040-02` off `0040`, merges `0040-01` (its only prerequisite), continues,
`[x]`; then `0040-03` off `0040` merging `0040-02`; and so on. The privileged
integrator takes `0040-03` (which transitively contains `0040-01..03`), merges it
into `0040`, adds acceptance records and findings, and — on approval — integrates
`0040` into `main` and moves it to `DONE.md`.

**Parallel subtasks.** Task `0041-02` is split into `0041-02.01` and `0041-02.02`,
worked by two different grunts, each branched off `0041-02`. When both are `[x]`,
the Task owner (a grunt) merges both subtask branches into `0041-02`, keeping both
claim files, and completes the Task's own package/aggregation work.

**Two prerequisites on two branches.** Task `0042-05` has `PREREQ:
0042-05:0042-03, 0042-05:0042-04`, both `[x]` but unaccepted and unintegrated. The
worker bases `0042-05` off the Feature branch `0042`, then merges both `0042-03`
and `0042-04` (pulling in both sets of work products and both claim files) before
starting new work, and records both merged tips in its claim.
