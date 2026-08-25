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

## Where agents mutate: item-owned worktrees only

Decisions `DEC-0044-010`, `DEC-0044-012` and `DEC-0044-015` fix **where** a
mutation may happen, independently of which branch it belongs on.

**The rule.** An agent mutates only inside a **worktree it owns for its item**
— normally `.worktrees/<item-id>` or an equally isolated path it provisioned
itself (see `_src/tools/provision_tmp_worktree.sh`). The shared root checkout
`/Users/tobias.anton/devel/autodocs` is **not written to**: no authoring there,
no `git add`, no `git commit`, no `commit -a`, no cleanup, no reset. It is a
read reference and the place where `main` happens to be checked out. This
applies to governance artifacts too: "governance lives on `main`" says which
branch, not which directory. A governance change is authored and committed in an
item-owned worktree on a branch cut from `main`, and only the final ref advance
touches the root.

**Why.** The damage that produced this rule was never in Git history and no
history-based control could have found it. The root checkout carried a staged
tree from before Feature `0040`'s closure — 138 files, 28683 deletions — and its
files on disk matched that same old state (`DONE.md` on disk held zero mentions
of `0040`, against 88 in `HEAD`). An unrestricted `git commit -a` there would
have silently reverted a closed Feature. It was found by hand.

**Confirmed mechanism.** Task `0044-14` reproduced the suspected cause in a
hermetic fixture: `git update-ref refs/heads/main <new> <old>` executed from a
detached worktree advances the ref **past** the index and files of the worktree
where `main` is checked out. That worktree is then left with `HEAD` at `<new>`
while its index and files still hold `<old>` — reported by the check below as
`INDEX_NOT_HEAD` plus `STALE_AFTER_REF_MOVE`. The fixture is
`_src/tools/test_check_integration_hygiene.py::test_update_ref_reproduces_stale_worktree_signature`.
The finding is stated as a *signature*, not as proof that this exact command ran:
any equivalent low-level ref move produces the same observable state.

**The required remedy, per `DEC-0044-015`.** Do not refresh the stale checkout
after the fact; avoid creating it. `git update-ref` on `refs/heads/main` is
**prohibited**. `main` is advanced **from the root checkout itself**, because a
`git merge` there moves ref, index and files in one step and therefore cannot
leave the root stale:

1. Author and commit the change in an item-owned worktree, on a branch cut from
   `main`, with the `DEC-0044-008` provenance trailer.
2. **Machine hard preflight in the root:**
   `python3 _src/tools/check_integration_hygiene.py --repo <root> --root-preflight`.
   The shared executable verifies the root is on `main`, its index equals
   `HEAD`, and its tracked working-tree divergence satisfies the same
   `DEC-0044-021` classifier used by the hygiene check below. Any failure means
   **abort** — do not "tidy up" the root; recovery is separately authorized.
3. Advance from the root: `git -C <root> merge --ff-only <branch>`, or `--no-ff`
   when `DEC-0044-008` requires a real merge commit because the branch is not on
   the direct predecessor chain.
4. Remove the helper worktree and branch.

Only the expressly assigned **privileged Integrator** performs the hygiene
verdict and step 3. The Project Lead coordinates the baseline and authority but
does not run the gate or merge `main`. No unprivileged worker moves
`refs/heads/main` at all.

## Pre-integration hygiene check

Before any integration — and mandatorily before the ref advance above — run the
machine-runnable check:

```bash
python3 _src/tools/check_integration_hygiene.py --repo <integration-worktree> --candidate-ref <candidate> [--json]
```

It is strictly read-only (no files, refs, indexes or objects are written) and
inspects **every** worktree registered against the shared repository. Exit code
`0` means clean, `1` means findings, `2` means the check itself could not run —
and a `2` is a failed check, never a pass. Findings:

| Code | Meaning |
|---|---|
| `INDEX_NOT_HEAD` | the integration worktree's own index differs from its `HEAD` |
| `FOREIGN_STAGED_TREE` | some *other* registered worktree still holds a staged tree after one bounded 2.0-second re-sample; the finding includes index mtime and age |
| `MAIN_WORKTREE_DIRTY` | tracked files in the worktree checking out `main` differ from its index; this is a blocking root-quiescence finding, not a rule for live item worktrees |
| `CANDIDATE_MEMORY_OVERLAP` | the candidate changes a currently allowed dirty Memory path; overlap blocks even when bytes are equal |
| `STALE_AFTER_REF_MOVE` | a worktree's branch ref advanced while its index and files still match the previous reflog tip — the signature described above |
| `WORKTREE_UNAVAILABLE` | a registered worktree path no longer exists |

Two properties of the check must be understood, or it will be trusted for more
than it does:

- `FOREIGN_STAGED_TREE` is **not** by itself an accusation. Another agent staging
  work in its own worktree is ordinary. The check waits a bounded 2.0 seconds and
  re-samples every initial foreign candidate once; a commit that completes in
  that interval is not reported. A candidate still divergent on the second
  sample remains the same blocking finding, with structured index mtime and age
  (`index_mtime_utc`, `index_age_seconds`) so fresh and stale state can be told
  apart without another run. The resolution is to have that owner commit or
  stash — never to reset a foreign worktree. Re-sampling does not make any
  persistent foreign staged tree advisory and does not narrow which worktrees
  block.
- `MAIN_WORKTREE_DIRTY` closes the known clean-index blind spot for the worktree
  checking out `main`. Under `DEC-0044-021`, only a non-empty set made entirely
  of unstaged tracked exact children of `logs/agent-memory/` is allowed. The
  directory name itself, prefix lookalikes, case variants, mixed paths, staged
  Memory, and indeterminate output block. Git paths are read with `-z`; newline
  characters are never record separators. Before merge, `--candidate-ref`
  intersects the exact candidate tree-diff paths with the allowed dirty Memory
  paths and blocks every overlap. The same classifier powers `--root-preflight`,
  which is rerun immediately after the root merge. Untracked files and ordinary
  unstaged item-worktree changes remain outside this particular gate.

## Preserved snapshot tags and recovery

When state that exists in no branch has to be cleared — a foreign staged index, a
diverged working tree — it is **captured as a commit and tagged `preserved/*`
before** anything is cleared. These tags are not on any branch and are reachable
only through the tag. **Deleting one can destroy the only copy of something.** Do
not prune, garbage-collect around, or "clean up" `preserved/*` tags; they are
retained indefinitely unless the current user explicitly authorizes removal of a
named tag.

Current tags (`git tag -l 'preserved/*'`):

| Tag | Commit | What it holds |
|---|---|---|
| `preserved/root-index-20260821` | `70e2c4e3e` | root checkout's staged index, captured by Seven before the `0038` integration |
| `preserved/root-unstaged-draft-20260821` | `f074c26b1` | unowned unstaged draft from the root checkout, on its true base `c0a274e66` |
| `preserved/root-worktree-20260821-kathryn` | `88e335c27` | complete root working tree **including untracked files**, taken before the index cleanup; the fallback line for the incident above |
| `preserved/root-worktree-20260821-kathryn-2` | `f8963b833` | root checkout state before the second realignment following a ref move |
| `preserved/0019-staged-index-20260822-kathryn` | `eb0c95f1d` | foreign staged index found in the canonical `0019` worktree |
| `preserved/staged-0043-01-20260822-kathryn` | `05680c5c7` | foreign staged index found in `.worktrees/0043-01` |
| `preserved/staged-0044-01-20260822-kathryn` | `56bc616f4` | foreign staged index found in `.worktrees/0044-01` |
| `preserved/staged-0044-01-task-20260822-kathryn` | `c70c45d5d` | foreign staged index found in `.worktrees/0044-01-task` |
| `preserved/main-incident-6d9a9ba-20260824` | `6d9a9ba116419fc0631412870f9d5914d3fda7c2` | unauthorized root merge of `0037-39` during `0037-08` setup, retained before the explicitly authorized Option-B recovery of `main` to `a3cee63085bdee02521c0437d8696ee1afaa872e` |
| `preserved/root-git-config-incident-20260825-jean-luc` | `1252503ae1cdcad5b387d2351965da9063964d3f` | the three uncommitted physical-root divergences found after repairing the shared `core.worktree`/test-identity contamination; preserved as evidence without adopting their contents into `main` |
| `preserved/as-verify-0038-34-index-20260825` | `d825cff53560878bcfeb4e504113945a21ae0abc` | stale index of the missing worktree `/private/tmp/as-verify-0038-34` (detached HEAD `9bcf87edb`, already `[x]` on branch `0038-34`); captured before authorized removal of that registration only |

To recover from a snapshot, inspect and extract it — never check it out over a
live worktree:

```bash
git show --stat preserved/<tag>                      # what is in it
git diff HEAD preserved/<tag>                        # how it differs from now
git worktree add /tmp/recover-<tag> preserved/<tag>  # inspect in isolation
git checkout preserved/<tag> -- <path>               # take back one path, in an item worktree
```

Anyone who captures a new snapshot appends a row to the table above in the same
commit, so the record of what each tag protects never lives only in a message.

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
  replacement and pull-in, it is a *risk integration*. A bounded temporary
  suspension may activate only with the recorded unanimous affirmative votes of
  **three independent privileged decision-makers**. QA Manager and Security
  Manager must always be consulted with evidence: each may sit on that panel or
  be a distinct external specialist, and each has a final veto for that request.
  An external veto is checked after unanimity; an inside-panel specialist's veto
  is inherent in that unanimous vote and is not duplicated. Silence, absence,
  abstention, failed independence, missing evidence, non-unanimity, either veto,
  expiry, or failed restoration is never approval and routes through the existing
  `[u]` integration verdict to Management. A record binds the exact candidate,
  policy clauses, permitted action, exclusions, compensating controls, finite
  duration/restoration event, participants, votes, vetoes, and restoration
  evidence. It cannot grant acceptance, signing, credentials, release, external
  mutation, service-control, or residual-risk authority. The canonical record
  schema and fail-closed state machine are in
  [`risk-integration.md`](risk-integration.md).
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
  clears, or moves the attribute (architect-only). An Architect may add the
  attribute, with recorded rationale, at any time before the affected node has
  current Acceptance, including after `[x]`/`[w]`. Current Acceptance freezes
  that accepted baseline; later addition, removal, or movement first requires
  separately authorized append-only invalidation or reopening. Immediately
  before Acceptance bookkeeping, compare-and-swap protects the pinned Task
  block, checkpoint attribute, contract, prerequisite graph, and Acceptance
  state from a concurrent late designation.
- **Feature → `main`** and the `DONE.md` move are performed only by a privileged
  agent (the closure authority). Whether a mandatory integration *review* happens
  at the Feature depends on whether the Feature node itself is flagged; either
  way, the Feature closes only once every integration checkpoint within it has a
  current passing review and every required transitive `[x]`/`[w]` predecessor
  induced into those Acceptance batches has its own current accepted disposition
  ([`task-acceptance.md`](task-acceptance.md)).

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
2. **Runs the pre-integration hygiene check** (above) against the exact branch:
   `python3 _src/tools/check_integration_hygiene.py --repo <integration-worktree> --candidate-ref <candidate>`.
   A non-zero exit is a stop, not a warning: findings are resolved by their
   owners — or the integration is deferred — before any merge. A foreign
   worktree is never reset by the integrator.
3. Merges the required Task branch(es) into the Feature branch, resolving
   conflicts without discarding any owner's work and carrying up all claim files.
4. Performs the integration review at each node the architect marked
   `Integration review: mandatory` — and the Feature aggregate review if the
   Feature itself is flagged — as defined in
   [`task-acceptance.md`](task-acceptance.md), executing the derived
   integration-test obligation of
   [`integration-test-obligation.md`](integration-test-obligation.md) against
   the exact integrated candidate (staged activation per `DEC-0044-019`), and
   **adding the review findings and
   acceptance records** on the Feature branch. Only the marked node independently
   triggers integration review. Its Task-Acceptance assignment expands through
   every required transitive `[x]`/`[w]` predecessor until current valid
   Acceptance boundaries; every batch member, marked or unmarked, receives its
   own decision and, on approval, its own `Acceptance: ✓` record bottom-up. An
   unmarked node does not independently trigger review, and missing Acceptance
   does not block ordinary successor implementation.
5. Reconciles and removes the predecessor claim files whose information is now
   captured in acceptance records and check-in provenance
   ([`../../AGENTS.md`](../../AGENTS.md) → *Check-in provenance*).
6. On full approval, integrates the Feature branch into `main` — using the
   root-checkout advance procedure of `DEC-0044-015` described above, never
   `git update-ref` — and moves the Feature to `DONE.md` via the path-isolated
   bookkeeping commit that [`task-acceptance.md`](task-acceptance.md) requires.

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
