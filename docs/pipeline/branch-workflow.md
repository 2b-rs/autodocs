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

## Exception: governance artifacts live on `main`

Management decision `DEC-0044-012` (2026-08-21) removes one class of file from
the one-branch-per-item rule above. **Changes to governance processes are always
made on `main`, and `main` is always current with respect to governance.**

Governance artifacts are at minimum:

- decision records (`DEC-*`, normally under `docs/dossiers/`);
- the authority files `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `CLAUDE.md`;
- everything under `docs/pipeline/` — including this document;
- the marker and prerequisite contract in the `TODO.md` header.

Everything else — ordinary work products, generated output, tools, tests, and the
per-item backlog entries themselves — is unaffected and travels on item branches
as described throughout the rest of this document.

The reason is that governance is *shared* state, and shared state held on a
private branch cannot be coordinated, only reconstructed after the fact. That is
the same failure class `DEC-0044-008` rejected for provenance. The trigger was
concrete: a decision record drafted on a branch claimed an identifier that a
parallel line of work had already allocated on `main`, leaving two append-only
records under one ID that answered the same question in opposite ways. On `main`
the collision would have been visible at allocation time — `main` is the only
place where an allocation point for identifiers can exist. **Check a new `DEC-`
identifier against `main` before using it.**

Practically this means a governance change is committed directly on `main`
rather than through an item branch and a merge. The provenance trailer from
`DEC-0044-008` still applies (`Policy-Origin-Branch: main`), and the
integrator's ordinary duty of care is unchanged; what disappears is the branch
detour, not the review.

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

## Integration policy precedence

Established by user decision of 2026-08-20 (`DEC-0044-001..003`,
[`docs/dossiers/re-intake-prozessverbesserung-integration-und-capabilities.md`](../dossiers/re-intake-prozessverbesserung-integration-und-capabilities.md)),
effective immediately. Elaboration, the planning-error prevention at breakdown
time, and the mechanical provenance checks are Feature `0044` work
(`0044-01`/`0044-02`); until they land, these rules bind as written:

- **The policy of the target branch governs every integration.** When work moves
  from `B` onto `A`, the policy in force on `A` decides whether the merge is
  permitted — not the policy `B` was implemented under.
- **Non-integrability is triaged by case, not improvised.** When integrating
  `B` onto `A` fails because of `A`'s policy, exactly one of four cases applies
  (table A1–A4,
  [`re-intake-prozessverbesserung-integration-und-capabilities.md`](../dossiers/re-intake-prozessverbesserung-integration-und-capabilities.md)
  §2.1; anchoring decision `DEC-0044-006`,
  [`0044-01-branch-workflow-prose-scope-review.md`](../dossiers/0044-01-branch-workflow-prose-scope-review.md)):
  - **A1 — planning error, pre-existing.** `A`'s policy would already have
    forbidden integrating `B` at branch-out time.
  - **A2 — planning error, order deviation.** `A`'s policy changed because
    implementation proceeded in a different order than the architect planned.
  - **A3 — not a planning error.** `A`'s policy changed because a feature was
    added later or a deviation permit was granted after `B` branched out. The
    integrator may proceed under the **policy replacement** rule below.
  - **A4 — still not integrable after replacement.** This is a **risk
    integration**; see the "Risk integration" bullet below.

  A1 and A2 are **planning errors**: they are reported against the breakdown,
  not worked around by the integrator. `0044-04` (the feature-breakdown
  process instruction) is the prevention point required by `RQ-IP-02`: it must
  check target-branch integrability and capture implementation-order fidelity
  at breakdown/branch-creation time so A1/A2 cannot occur; a deviation from the
  planned order is itself captured there as a recorded decision rather than
  surfacing later as an integration failure.
- **Policy replacement (integrator only, case A3):** for the non-planning-error
  case, the integrator may substitute, for this integration, any policy
  version that was valid at some point since branch-out on **either** of the
  two branches being integrated. Which version was chosen and why is a
  decision with reach beyond the integrator's own work unit and therefore
  requires a recorded decision (`TK-2`, [`process-roles.md`](process-roles.md));
  see `DEC-0044-005` in
  [`0044-01-branch-workflow-prose-scope-review.md`](../dossiers/0044-01-branch-workflow-prose-scope-review.md)
  for the required record shape.
- **Policy provenance is protected:** no agent commits onto a branch policy
  changes that originated on any branch other than the branch being integrated
  or the integration target. Consequently, pulling the **target branch's**
  policy changes into the branch to be integrated is permitted — that is the
  one policy flow that keeps provenance checkable.
- **Risk integration (case A4):** if integration remains impossible even under
  replacement and pull-in, it is a *Risikointegration*. The integrator may
  approve it — and temporarily suspend policies for it — only after a review
  with two further agents (QA and Architect) that reaches **unanimity**, with
  the suspension's scope, duration, and participants recorded. Without
  unanimity, the integration escalates to the user for decision; this composes
  with, and does not replace, the `[u]` integration verdict below.
- **Recorded policy origin (`DEC-0044-008`/`DEC-0044-011`, effective
  2026-08-21T11:20:51+02:00; no retroactive requirement):** Every later commit
  that changes a declared policy path MUST include exactly one Git commit-message
  trailer in this form:

  ```text
  Policy-Origin-Branch: <canonical-branch-name>
  ```

  `<canonical-branch-name>` is the valid Git branch name where the policy change
  was authored. The person introducing the commit supplies this evidence;
  reviewers must not infer origin from topology or a surviving branch name. A
  policy-path commit at or before the effective decision record is legacy history
  and does not need retrofitting. The read-only `check_policy_provenance.py`
  check reports a missing, duplicated, empty, or malformed required trailer as a
  finding. A valid trailer documents origin but does not excuse a foreign-origin
  policy commit.
- **No fast-forward absorption of non-predecessor policy content:** A policy-path
  commit from outside the receiving item direct predecessor/successor chain MUST
  be introduced by an explicit `--no-ff` merge commit, never by `git merge
  --ff-only` or `git update-ref`. The merge commit preserves inspectable topology;
  the introduced policy commit still requires its `Policy-Origin-Branch:` trailer.
  This is the repository-wide recorded-provenance rule and retains the narrower
  `DEC-0044-007` control below.
- **Fast-forward absorption of foreign content is prohibited (mechanical-check
  blind spot, `DEC-0044-007`):** `git merge --ff-only` and `git update-ref`
  advance a branch tip without ever creating a merge commit, so an absorbed
  foreign commit becomes indistinguishable, by topology alone, from one
  authored directly on the receiving branch — `check_policy_provenance.py`
  (the `DEC-0044-002` mechanical check) is therefore structurally unable to
  catch a foreign-branch policy commit absorbed this way. To keep the
  mechanical check meaningful, an agent MUST NOT use `git merge --ff-only` or
  `git update-ref` to advance a Task/Feature/Subtask branch, or `main`, onto
  the tip of any branch other than that item's own direct predecessor/
  successor chain (the base-and-merge chain required above) or its own prior
  tip. Absorbing content from any other branch — including a legitimate
  `DEC-0044-001` target-policy pull-in — MUST instead use an explicit merge
  commit (`git merge --no-ff` or equivalent), so the mechanical check's
  merge-commit-based foreign/pull-in classification has topology to inspect.
  Fast-forwarding a branch (including `main`) to the tip of that item's own
  already-integrated predecessor/successor chain remains permitted and is not
  "absorption" in this sense — the content already passed through the merge
  commits recorded within that chain's own history. See `DEC-0044-007`
  ([`0044-01-branch-workflow-prose-scope-review.md`](../dossiers/0044-01-branch-workflow-prose-scope-review.md))
  for the full analysis and residual-limitation record.

## Merge authority and direction

Merges only ever move work **up** the tree (Subtask→Task→Feature). Authority
follows the **integration checkpoints** the architect declared, not the hierarchy
level (see the `TODO.md` header and [`task-acceptance.md`](task-acceptance.md)):

- **A merge that crosses no checkpoint** may be performed by a **sandboxed/grunt**
  agent — typically Subtask→Task, including subtask branches authored by
  **different** agents when a Task is parallelized. The merger preserves each
  merged branch's claim file and never alters another agent's `owner_token` or
  acceptance state.
- **A merge that crosses a node marked `Integration review: mandatory`** requires
  the **privileged integrator**. Crossing that boundary upward *is* the
  integration checkpoint: the integrator reviews the node's work, records the
  finding, and only then is it integrated. This holds whether the checkpoint is a
  Subtask, a Task, or the Feature — the attribute, not the level, decides. A
  sandboxed/grunt agent must never cross a checkpoint boundary and never sets,
  clears, or moves the attribute (architect-only).
- **Feature → `main`** and the `DONE.md` move are performed only by a privileged
  agent (the closure authority). Whether a mandatory integration *review* happens
  at the Feature depends on whether the Feature node itself is flagged; either
  way, the Feature closes only once every integration checkpoint within it has a
  current passing review ([`task-acceptance.md`](task-acceptance.md)).

**Not every Task is individually merged into the Feature.** In the simplest case
a single grunt works the Tasks one after another, each new Task branch based off
the Feature branch and merging in the previous Task branch (which already carries
all earlier done work). The Feature branch itself is not advanced by the grunt.
The **last** Task branch — which transitively contains the whole chain — is
integrated into the Feature branch by a privileged agent at closure; any
intermediate node the architect marked `Integration review: mandatory` is
reviewed by the integrator as its boundary is crossed. When Tasks were genuinely
parallel and do not form a single chain, the integrator merges each independent
Task branch that is required for the Feature. Merges that cross no checkpoint may
be chained up by a grunt without privileged review.

## Feature integration and sign-off

Feature integration is the privileged step that both merges Task work into the
Feature branch and performs the Feature-level review. The integrator:

1. Confirms current privilege and an explicit assignment to integrate/accept the
   Feature scope (privilege alone is not authority — see
   [`task-acceptance.md`](task-acceptance.md)).
2. Merges the required Task branch(es) into the Feature branch, resolving
   conflicts without discarding any owner's work and carrying up all claim files.
3. Performs the integration review at each node the architect marked
   `Integration review: mandatory` — and the Feature aggregate review if the
   Feature itself is flagged — as defined in
   [`task-acceptance.md`](task-acceptance.md), **adding the review findings and
   acceptance records** on the Feature branch. `Acceptance: ✓` records are created
   at those checkpoints, bottom-up and prerequisite-closed. Unflagged work carries
   no such record.
4. Reconciles and removes the predecessor claim files whose information is now
   captured in acceptance records and check-in provenance
   ([`../../AGENTS.md`](../../AGENTS.md) → *Check-in provenance*).
5. On full approval, integrates the Feature branch into `main` and moves the
   Feature to `DONE.md` via the path-isolated bookkeeping commit that
   [`task-acceptance.md`](task-acceptance.md) requires.

## Integration rejection: the `[u]` verdict

If the integrator **cannot** approve the work at an integration checkpoint — the
evidence shows a material nonconformity or a decision the integrator may not make
alone — it does not silently fix or force it through. Instead it records a `[u]`
integration verdict at that checkpoint and hands resolution to the user. This
applies at any checkpoint the architect declared, not only at the Feature; the
Feature is simply the checkpoint of last resort.

The `[u]` verdict is a structured record placed directly beneath the checkpoint
node (beneath the Feature heading when the checkpoint is the Feature, since a
Feature heading carries no checkbox marker):

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
at checkpoint granularity; it does not introduce a new marker.

Resolution of a `[u]` verdict — including waiving the mandatory integrating task
or overriding the verdict outright — is a **management** decision (the current
user or a registered authority above the process), recorded as an explicit
append-only authorization naming authority, scope, reason, and any compensating
controls. This is the sanctioned path for real-world surprises; the integrator
never clears its own verdict, and no agent circumvents a checkpoint silently.

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

- `_src/tools/provision_tmp_worktree.sh` (Task `0038-22`) is a **self-service**
  per-item `git worktree` provisioner for an `unprivileged`/`privileged` agent
  that runs Git directly: given a caller-supplied item branch, it bases a new
  branch off its derived parent when the branch does not exist yet, provisions
  or idempotently heals a worktree at the caller's chosen location (defaulting
  to the existing `.worktrees/<item>` convention), and reaps orphaned scratch
  worktrees under that root that carry neither an active claim file nor
  uncommitted content — surfacing, never deleting, one that does. It has
  **worktree lifecycle only**: it does not merge the prerequisite closure or
  make any other branch/authority policy decision; that remains the runner
  transaction engine's job below. This is a different tool from
  `_src/tools/provision_worker_clone.sh` (Feature `0041` Task `0041-01`), which
  a privileged host uses to hand a sandboxed grunt — who cannot run Git at all
  — an isolated `git clone` before it receives work
  ([`worker-clone-provisioning.md`](worker-clone-provisioning.md)).
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

## Forward compatibility with the Feature `0037` issue store

This is a **legacy-authority** process: it is layered on the current merge-prone
authoritative `TODO.md`/`DONE.md` database and the `TODO-<agent-id>.md` claim
files. Feature `0037` replaces that database with one schema-enforced Markdown
item per Feature/Task/Subtask at `issues/XXXX/…/index.md`, each with its own
`claim.json` and terminal `closure.json`. This workflow is designed to map onto
that future store rather than compete with it:

- **Claim files → per-item `claim.json`.** "Claim files travel on the item's
  branch and merge upward" becomes "each item's `claim.json` travels with its own
  file." Because every item owns an isolated path, upward merges become far less
  conflict-prone than merging a shared `TODO.md`, which is part of why Feature
  `0037` exists.
- **Branch/merge/integration actions → typed queue actions.** The base-branch,
  merge-prerequisite, and Task→Feature integration operations are *surviving
  legacy primitives*: they must be specified once against the frozen
  request/result contract (`0037-45`), carried into the pre-activation handoff
  manifest (`0038-16.01`), and implemented in the permanent typed-action registry
  (`0037-46.01`) — not re-invented as a second permanent protocol. The legacy
  `runner_transaction` implementation is a bridge that retires at `0037-46.02`.
- **Integration authority → machine-enforced gate.** The privileged-only
  Task→Feature / Feature→`main` boundary and the Feature-level `[u]` integration
  verdict are enforced manually here; their machine-enforced form is owned by the
  non-bypassable integration-policy gate (`0037-43`) and the acceptance
  machine-enforcement/migration Task (`0039-05`), across both the legacy queue and
  the future issue-store lifecycle.

In short: the branch topology and the base-and-merge rule are the *behavior*; the
carriers (`TODO.md`/claim files today, `issues/…/claim.json` after cutover) and
the executors (`runner_transaction` today, the `0037-46.01` queue after cutover)
change beneath it without changing the workflow.

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
