# Typed Branch/Merge/Integration Action Contract

**Status:** Specification for Task `0038-19`. Defines, against the frozen
Task `0037-45` request/result contract
([`agent-execution.md`](agent-execution.md) plus
`issues/_schema/agent-capability-v1.schema.json`,
`issues/_schema/runner-request-v1.schema.json`, and
`issues/_schema/runner-result-v1.schema.json`), the fixed typed actions that
formalize the manual procedure
[`branch-workflow.md`](branch-workflow.md) already describes in prose:
**`base-branch`**, **`merge-prereqs`**, and the **Task→Feature /
Feature→`main` integration action** (`integrate-checkpoint`). This document
makes **no executable change**. Nothing in it runs; it specifies the request
and result shape a later implementation must produce. Implementation in the
legacy transaction runner is Task `0038-20`; the permanent typed-action
registry is Task `0037-46.01`.

This document does not restate or change any authority meaning already
defined by [`AGENTS.md`](../../AGENTS.md), [`SANDBOX.md`](../../SANDBOX.md),
[`branch-workflow.md`](branch-workflow.md), or
[`task-acceptance.md`](task-acceptance.md). Where a rule below repeats one of
those documents, that document remains authoritative; this document only adds
the machine-checkable *shape* those rules must take when carried as a
`runner-request@v1`/`runner-result@v1` pair.

## 1. Why a mapping is needed, not a schema change

`issues/_schema/runner-request-v1.schema.json` is frozen (`0037-45` is
`[x]`), `additionalProperties: false`, and its `action` enum has exactly
seven fixed values: `read_only_discovery`, `focused_validation`,
`generation`, `external_service_configuration`, `signing_verification`,
`path_limited_commit`, `bookkeeping_commit`. None of them is named
`base-branch`, `merge-prereqs`, or an integration verb, and this document's
write scope does not include editing that frozen schema file. Branch/merge
operations are therefore **typed sub-protocols carried inside the existing
generic envelope**, distinguished by a mandatory naming convention on
`idempotence_key` and by documented conventions inside the existing
`read_scopes`, `write_scopes`, `preflight`, and `dependencies` arrays — never
by a new schema property. This mirrors how `SANDBOX.md` already treats branch
operations: *"Branch, base, and merge operations are Git operations and route
through the runner under the same preflight, scope, provenance, and
fail-closed rules as commits."*

Each typed action below states which of the seven frozen `action` enum
values it uses and how it fills the generic fields. A conformant instance
must be **fully valid** against `runner-request-v1`/`runner-result-v1` as
written — the typed-action layer is additive convention on top of a
schema-valid instance, never a relaxation of it.

## 2. Common conventions

These apply to all three actions.

- **Typed-action discriminator.** `idempotence_key` MUST start with
  `<typed-action>:` where `<typed-action>` is exactly `base-branch`,
  `merge-prereqs`, or `integrate-checkpoint`, followed by `<item-id>:` and a
  disambiguator (e.g. the resulting tip or a content-derived suffix). This is
  the sole machine-readable way to recover which typed action a generic
  `runner-request@v1` instance represents, since the frozen `action` field
  cannot itself enumerate branch-specific operations.
- **Target-branch declaration.** `preflight` MUST contain exactly one entry
  `target-branch:refs/heads/<branch>` naming the branch being advanced by
  this request (the branch that will point at the new commit/ref on
  success). This is what the authority check in §6 keys off.
- **Pinned ref-scope convention.** A pinned branch reference is written as
  `ref:refs/heads/<branch>@<40-hex-tip>` inside `read_scopes` (source of
  truth to merge from or base off) or `write_scopes` (ref being created or
  advanced with no tracked-file diff, i.e. `base-branch`). `<40-hex-tip>` is
  the exact commit the action's preflight must observe at that ref before
  mutating; a mismatch is a stale-base/stale-tip rejection (§5).
- **Owner-token/authority binding.** `claim_owner_token` MUST equal the
  `owner_token:` recorded in the item's own active `TODO-<agent-id>.md` claim
  file at preflight time (`AGENTS.md` §"Starting work" / branch-workflow.md
  §"Claim files … travel on the branch"). The bound `agent-capability@v1`
  record for that token's session determines its `class`
  (`sandboxed-grunt`/`privileged` in the frozen schema; an `unprivileged`
  session performs the identical action directly without ever instantiating a
  `runner-request@v1` object at all, per `SANDBOX.md`'s "does not use the
  runner protocol" — see the note in §7). No request may create, rewrite, or
  claim authorship of another session's claim file; only the auto-union
  merge behavior in §5 may combine bytes from two claim files, and even that
  never rewrites the `owner_token:` line itself.
- **Authority epoch.** `authority_epoch` is `legacy-writable` for all
  branch/merge actions until the Feature `0037` cutover changes the current
  backlog authority (`SANDBOX.md` §"Current backlog authority");
  post-cutover values (`issue-store-writable`, etc.) are unchanged in meaning
  and simply select the successor authority the same action executes under.
- **Limits.** `limits.timeout_seconds`/`cpu`/`memory_mib` are set
  conservatively for a Git ref/commit operation (no generator/validator
  workload); `workers` is omitted.
- **No network, no credentials.** None of these three actions declares
  `network_hosts` or `credential_handles`; they are pure local Git ref/commit
  operations.

## 3. Action: `base-branch`

Bases an item's own branch off its parent branch (`branch-workflow.md`
§"Starting a Task or Subtask" step 1). Never advances any other branch, never
touches tracked file content (identical tree to the parent tip), and
therefore never crosses an integration checkpoint.

- **`action`:** `generation` — the only frozen value describing "produce a
  new declared artifact" without implying a tracked-file diff; the produced
  artifact is the new branch ref itself.
- **Inputs:**
  - `expected_base`: the parent branch's current tip (`XXXX` for a Task,
    `XXXX-YY` for a Subtask — see `branch-workflow.md`'s topology table).
  - `read_scopes`: `["ref:refs/heads/<parent>@<expected_base>"]`
    (`minItems: 1` satisfied).
  - `write_scopes`: `["ref:refs/heads/<item-id>"]` (the branch being
    created).
  - `preflight`: `target-branch:refs/heads/<item-id>`,
    `parent-branch-exists:<parent>`,
    `expected-parent-tip:refs/heads/<parent>@<expected_base>`,
    `item-branch-absent-or-fast-forwardable:refs/heads/<item-id>`,
    `owner-token-matches-claim:<claim_owner_token>`.
  - `dependencies`: `[]` (base-branch has no prerequisite closure of its
    own; that is `merge-prereqs`'s job).
- **Expected parent base:** exactly `expected_base` above; a mismatch
  against the observed parent tip is `BMA-STALE-BASE` (§5).
- **Authority:** unconditional for any capability class (`sandboxed-grunt`
  via the runner, `unprivileged`/`privileged` directly) — creating a branch
  never advances an existing checkpointed ref.
- **Result:** `status: succeeded`, `outputs:
  ["ref:refs/heads/<item-id>@<expected_base>"]`, `findings: []`,
  `base_observed` equal to `expected_base`.

## 4. Action: `merge-prereqs`

Merges every declared done-but-unintegrated (`[x]`/`[w]`) prerequisite
branch into the item's **own, not-yet-advanced-anywhere** branch
(`branch-workflow.md` §"Starting a Task or Subtask" step 2). Because the
target is always the item's own new branch — never a Feature branch or
`main` — this action never crosses an integration checkpoint by
construction, independent of whether the *sources* are Subtask- or
Task-level branches (this resolves the apparent tension between
`branch-workflow.md`'s checkpoint-based "Merge authority and direction"
section and its more specific "Grunt-permitted merges are limited to
Subtask→Task" sentence in "Capability-class execution of branch operations":
the destination branch, not the source level, decides checkpoint crossing;
see §8 for the residual documentation note).

- **`action`:** `path_limited_commit` — the merge produces a real 2-parent
  commit whose tree differs from the destination's previous tip by exactly
  the declared, merged paths.
- **Inputs:**
  - `expected_base`: the item's own branch tip immediately before this
    merge (i.e. the `base-branch` result, or the tip after a prior
    `merge-prereqs` call in the same sequential chain — see §4.1).
  - `read_scopes`: one `ref:refs/heads/<source>@<source-tip>` entry **per
    declared prerequisite branch**, `minItems: 1`.
  - `write_scopes`: the exact union of tracked file paths the merge changes
    (each source's work products and claim file(s)), `minItems: 1` (schema
    forces this for `path_limited_commit`).
  - `preflight`: `target-branch:refs/heads/<item-id>`, one
    `expected-source-tip:refs/heads/<source>@<source-tip>` per source,
    `owner-token-matches-claim:<claim_owner_token>`,
    `claim-union-no-foreign-rewrite`.
  - `dependencies`: the exact prerequisite item IDs from the item's `TODO.md`
    `PREREQ:` closure that are `[x]`/`[w]` and not already present on the
    parent branch (`branch-workflow.md` step 2). **Every** entry here MUST
    have a matching `ref:refs/heads/<dependency>@…` entry in `read_scopes`;
    an entry without one is `BMA-UNDECLARED-SOURCE` (§5).

### 4.1 Sequential 2-parent merges, never octopus

When there is more than one prerequisite branch (`branch-workflow.md`'s
"Two prerequisites on two branches" example: `0042-05` merging both
`0042-03` and `0042-04`), the action performs **one standard 2-parent merge
commit per source, in sequence** — never a single octopus (>2-parent)
commit. Each step's first parent is the previous step's resulting commit
(the initial `expected_base` for the first source, then each intermediate
merge tip); each step's second parent is that source's declared tip. This
keeps every merge individually revertable/bisectable and keeps the
recorded-merged-tip evidence (below) unambiguous per source.

- **Recorded-merged-tip evidence:** the result's `outputs` array carries, in
  order, one `merged-branch-tip:refs/heads/<source>@<source-tip>` entry
  immediately followed by the `merge-commit:<sha>` it produced, for every
  source — e.g. for a two-source merge: `merged-branch-tip:…@…`,
  `merge-commit:…`, `merged-branch-tip:…@…`, `merge-commit:…`. This is also
  what the active claim file's "merged prerequisite branch and tip" record
  (`branch-workflow.md` step 3) is populated from.

### 4.2 Conflict and fail-closed behavior

A content conflict on any step aborts that merge step entirely (the
equivalent of `git merge --abort`); the destination branch and working tree
are left exactly as they were before the attempt; no partial merge is ever
published. The transaction fails closed with a structured finding naming the
conflicting paths (`BMA-MERGE-CONFLICT`) and status `failed`; per
`branch-workflow.md`, resolution is manual ("the worker using the normal
rules — preserve unrelated work, never overwrite another owner's changes")
under a fresh request/idempotence key, never an automatic `-X ours`/`-X
theirs` resolution.

**Exception — claim-record conflicts are handled by §5's auto-union rule,
not by generic abort-on-conflict.** A conflict whose only touched hunks are
inside a `TODO-<agent-id>.md` claim file is evaluated by the claim-union rule
first; only a genuine foreign-`owner_token` collision escalates to a hard
failure (`BMA-CLAIM-FOREIGN-TOKEN`), and even then, that failure still
preserves the destination branch unmutated exactly like a generic conflict —
it just uses a distinct rule ID because the cause and required next action
differ (see §5).

## 5. Claim-record append-only auto-union

Because every `TODO-<agent-id>.md` claim filename embeds its own
`owner_token`/request ID (`AGENTS.md` §"Starting work" step 6), two
independently authored claim files essentially never collide at the Git path
level — a normal merge takes both files with no conflict. The auto-union
rule below covers the narrower case where the **same path**, carrying the
**same `owner_token:`**, was independently appended to on both the
destination and a source branch (e.g. the owning session updated its own
claim's status log after the branch was already carried forward by an
earlier merge elsewhere):

- If a merge step reports a conflict on a claim-file path **and** the
  `owner_token:` line is byte-identical on both sides, the action MUST
  auto-union rather than fail: take the destination's existing content, then
  append every line from the source side not already present verbatim
  (exact-duplicate lines are not repeated), preserving each side's original
  order. The claim's `owner_token:` line itself is never altered by this
  process. The result's `findings` array MUST record
  `claim-union:<path>` for every path unioned this way.
- If instead the `owner_token:` differs between the two conflicting versions
  of an identically named claim-file path — meaning applying either side
  verbatim would silently discard or misattribute another session's claim —
  the action MUST fail closed with `BMA-CLAIM-FOREIGN-TOKEN` and MUST NOT
  auto-resolve, pick a side, or rename either file. This is the required
  "claim-union conflict" negative example (see §9).

## 6. Action: `integrate-checkpoint` (Task→Feature / Feature→`main`)

Covers both privileged-only advancing merges `branch-workflow.md` describes:
merging a Task branch into its Feature branch, and merging a Feature branch
into `main` (the `DONE.md` move). Both share this action's shape because both
are, structurally, "a merge whose target branch is a checkpointed integration
boundary" — the split named in this Task's own acceptance criteria
("Subtask→Task versus Task→Feature/Feature→`main`") is exactly the split
between `merge-prereqs` (§4, target is the item's own not-yet-integrated
branch) and this action (target is the Feature branch or `main` itself).

- **`action` (merge step):** `path_limited_commit`, exactly like
  `merge-prereqs` in shape (2-parent merge commit, one source per step), but
  with `target-branch:refs/heads/<Feature-ID>` or `target-branch:refs/heads/main`
  in `preflight` and `capability-class-privileged` as an additional required
  `preflight` entry.
- **`action` (acceptance/reconciliation step):** `bookkeeping_commit`,
  parented on the exact hash the merge step's result returned (never a
  freely chosen or re-derived hash — `agent-execution.md`'s "ensure a
  bookkeeping commit may reference only the actual substantive commit
  returned by the preceding runner result"). This is where
  `branch-workflow.md`'s "adds review findings and `Acceptance: ✓` records"
  and "reconciles and removes the predecessor claim files" steps live; its
  `write_scopes` names exactly `TODO.md`/`DONE.md` and the reconciled claim
  paths, never a work-product path.
- **Authority (unconditional):** `capability_class` for the bound
  `claim_owner_token` MUST be `privileged`. A request/attempt bound to any
  other class is `BMA-AUTHORITY-VIOLATION` regardless of whether the
  specific node the merge targets carries the architect's
  `Integration review: mandatory` flag — `branch-workflow.md` makes
  Task→Feature and Feature→`main` privileged-only unconditionally, while the
  flag additionally *requires the reviewed findings/`Acceptance: ✓` step*
  at flagged nodes.
- **Feature→`main` extra gate:** when `target-branch` is `main`, `preflight`
  MUST additionally contain `all-checkpoints-passed` — the machine-checkable
  stand-in for "every integration checkpoint within the Feature has a
  current passing review" (`task-acceptance.md`); its absence is
  `BMA-CHECKPOINTS-INCOMPLETE`.
- **The `[u]` integration verdict is not a request.** If the integrator
  cannot approve at a checkpoint, no `runner-request@v1` instance of this
  action is ever issued for that boundary; `branch-workflow.md`'s `[u]`
  verdict record is appended directly to `TODO.md` by the privileged
  integrator using ordinary non-execution/direct-commit tooling, not through
  this typed action. `0038-20`'s dependent implementation is required to
  *reject* any manifest that tries to route a Feature `[u]` verdict, an
  acceptance-record mutation, or a Task→Feature/Feature→`main` merge through
  a **sandboxed** request — this document's authority rule is exactly what
  that rejection enforces.

## 7. Result schema

Both actions above (and both `integrate-checkpoint` steps) return a
`runner-result@v1` instance with:

- `status`: `succeeded` on a clean merge/branch creation; `rejected` when a
  business-rule check in §§3–6 fails **before** any mutation is attempted
  (fail-closed preflight rejection); `failed` when a Git-level conflict
  aborts mid-operation (§4.2); `partial_mutation_recovered` only via the
  named recovery transaction the frozen contract already defines
  (`agent-execution.md` §"Threat controls").
- `base_observed`: the actually-observed tip of the branch named by
  `expected_base` at execution time — always compared against the request's
  `expected_base` by the caller, not re-declared by the result.
- `outputs`: the new/advanced ref plus, for merges, the ordered
  `merged-branch-tip:…`/`merge-commit:…` pairs (§4.1).
- `findings`: structured rule-ID strings (`BMA-…`) for every rejection or
  auto-union event; empty on an unremarkable success.
- `result_digest`: the frozen contract's tamper-evident digest of the
  complete result, unchanged in meaning from `agent-execution.md`.

**Note on `agent-capability@v1`.** Its `class` enum is still
`["sandboxed-grunt", "privileged"]` — it predates the third `unprivileged`
capability class introduced by decision `DEC-CAP-001`/`DEC-CAP-002`
(commit `993ceffbc`, "feat(capability): add third capability class
`unprivileged`"; `AGENTS.md`'s "Dispatching a subagent" section cites this
decision but its named path `docs/dossiers/dec-capability-classes.md` does
not exist in this worktree at base — a pre-existing dangling cross-reference
in `AGENTS.md` this Task does not have write scope to repair, noted here
rather than silently linked to as if it resolved). That schema file is frozen and
`[x]` and is out of this Task's write scope; this document does not edit it.
An `unprivileged` session's authority is, per `SANDBOX.md`, identical to
`sandboxed-grunt`'s (no acceptance/integration authority) but its
*execution* is direct — it performs `base-branch`/`merge-prereqs` itself and
never instantiates a `runner-request@v1` object at all for these actions.
This document's business-rule fixtures (§9) still model an `unprivileged`
bound class for schema-validity/authority-check purposes, since the
same authority split applies identically whether the action is requested
through the runner or executed directly; the gap in the frozen enum is
flagged here for the `0037-46.01` owner rather than silently patched.

## 8. Cross-reference consistency note (not amended here)

`branch-workflow.md`'s "Capability-class execution of branch operations"
section states "Grunt-permitted merges are limited to Subtask→Task", which
read literally is stricter than its own "Merge authority and direction"
section's checkpoint-based framing (illustrated by the Task-level "Two
prerequisites on two branches" worked example, where a Task-level
`merge-prereqs` is performed by "the worker" without special privilege).
This document follows the checkpoint/destination-branch framing (§4, §6),
which is also what Task `0038-20`'s already-committed acceptance criteria
commits to ("Enforce Subtask→Task authority for sandboxed manifests and
reject Task→Feature, Feature→`main` … actions" — i.e. the boundary is which
*target* is being advanced, not the source item's level). Making
`branch-workflow.md`'s "Capability-class execution" sentence explicitly say
"whichever merge does not advance a Feature branch or `main`" instead of
"Subtask→Task" would be a single-line clarifying edit; it is out of this
Task's write scope (this document may only add a strictly additive
cross-reference to `branch-workflow.md`, never restructure it) and is
recorded here as a follow-up for the privileged integrator.

## 9. Positive/negative examples

`docs/pipeline/fixtures/0038-19/branch-merge-action-fixtures.json` carries
ten fixtures — six positive (`base-branch`; `merge-prereqs` single-source,
multi-source, and claim-auto-union; `integrate-checkpoint` for both
Task→Feature and Feature→`main`) and four negative, one per required
category:

| Category | Fixture ID | Rule ID |
|---|---|---|
| Authority violation | `authority-violation-neg-01` | `BMA-AUTHORITY-VIOLATION` |
| Undeclared merge source | `undeclared-source-neg-01` | `BMA-UNDECLARED-SOURCE` |
| Stale base/tip | `stale-tip-neg-01` | `BMA-STALE-SOURCE-TIP` |
| Claim-union conflict | `claim-union-conflict-neg-01` | `BMA-CLAIM-FOREIGN-TOKEN` |

`docs/pipeline/fixtures/0038-19/validate_branch_merge_action_fixtures.py`
validates every fixture's `request`/`result` object structurally against
`runner-request-v1`/`runner-result-v1` (all ten must be schema-valid — a
well-formed-but-rejected request is still a schema-valid instance), then
runs this document's business-rule layer and asserts each positive case
passes with no violation and each negative case fails with exactly its
declared rule. Run:

```text
python3 docs/pipeline/fixtures/0038-19/validate_branch_merge_action_fixtures.py
```

Expected output: `PASS: 10 fixtures (6 positive, 4 negative); …`. The script
is read-only against the repository (it only reads the three schema files
and the fixtures file) and performs no mutation.

## 10. Forward mapping: `0037-46.01` typed actions and `0037-46.02` retirement

Zero actions in this contract are left unmapped, and none is claimed by more
than one authoritative implementation at a time:

| This contract's action | Current legacy implementation (sole authority today) | Future `0037-46.01` typed-action ID | `0037-46.02` retirement trigger |
|---|---|---|---|
| `base-branch` | `_src/tools/runner_transaction.py` (Task `0038-20`, not yet implemented) | `git.base-branch@v1` | Legacy phase retires once `0037-46.01` registers `git.base-branch@v1` and the issue-store queue is activated for branch/merge actions |
| `merge-prereqs` | `_src/tools/runner_transaction.py` (Task `0038-20`, not yet implemented) | `git.merge-prereqs@v1` | Legacy phase retires under the same condition as `base-branch` |
| `integrate-checkpoint` (Task→Feature) | Manual privileged procedure per `branch-workflow.md` (no tool today) | `git.integrate-checkpoint@v1`, `target_kind=feature`, privileged-only | Retires once the queue enforces the same privileged-only gate machine-readably, tied to the non-bypassable integration-policy gate `0037-43` |
| `integrate-checkpoint` (Feature→`main`) | Manual privileged procedure per `branch-workflow.md` (no tool today) | `git.integrate-checkpoint@v1`, `target_kind=main`, privileged-only | Retires once `0039-05`'s acceptance machine-enforcement/migration lands across both the legacy queue and the issue-store lifecycle |

This table is the detailed spec `branch-workflow.md`'s "Forward compatibility
with the Feature `0037` issue store" section gestures at ("must be specified
once against the frozen request/result contract (`0037-45`) … and implemented
in the permanent typed-action registry (`0037-46.01`) — not re-invented as a
second permanent protocol"). Task `0038-20` is the sole authoritative legacy
implementation target for `base-branch`/`merge-prereqs`; no other tool or
process may claim to implement them without amending this table.
