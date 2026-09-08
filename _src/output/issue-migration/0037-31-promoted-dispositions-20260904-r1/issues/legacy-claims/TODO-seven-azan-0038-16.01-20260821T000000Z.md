# Claim — Task 0038-16.01

- agent: `Seven-Azan`
- owner_token: `agent:seven-azan:0038-16.01:20260821T000000Z`
- capability_class: `unprivileged` (direct execution; **no** acceptance/integration authority; runner protocol not used)
- branch: `0038-16.01`
- worktree: `.worktrees/0038-16.01` (root checkout is never written — `DEC-0044-009`)
- base_commit: `7b2e2ce9983321901a388e19fc3d13a8f8c9c6aa` (`main`)
- startup_review: `AGENTS.md`, `SANDBOX.md`, `TODO.md` header, `docs/pipeline/branch-workflow.md`

## Task (verbatim from `TODO.md`)

- [ ] **0038-16.01** PREREQ: 0038-16.01:0038-05, 0038-16.01:0038-07, 0038-16.01:0038-13, 0038-16.01:0038-14, 0038-16.01:0038-15, 0038-16.01:0038-19, 0038-16.01:0038-20, 0038-16.01:0038-21, 0038-16.01:0038-23, 0038-16.01:0037-37 Produce the versioned pre-activation handoff manifest consumed by the Feature `0037` queue implementation.
  - **Acceptance criteria:** Bind the exact `0037-37` review-package digest and map every surviving legacy action, schema, result, scope, evidence, recovery, context, validation, and approval-readiness primitive to a specific `0037-46.01` typed action/contract or an explicit `0037-46.02` retirement trigger; identify ownership, compatibility, test fixtures, and removal conditions without activating the queue or changing authority.
  - **Definition of Done:** A deterministic machine/human-readable manifest validates with zero unmapped or multiply authoritative primitives, names every required queue consumer and legacy retirement point, preserves the active singleton, and is ready for direct consumption by `0037-46.01`.

## Base-and-merge discovery

`AGENTS.md` step 10 / `branch-workflow.md` require basing a Subtask branch off its Task branch and
merging in every done-but-unintegrated prerequisite branch. Verified before the first mutation:

- Task branch `0038-16` does not exist (parent Task unstarted); Feature branch `0038`
  (`6491e5609`) **is already an ancestor of `main`**.
- Every prerequisite branch is already an ancestor of `main`: `0038-05-closure`, `0038-07`,
  `0038-11`, `0038-12`, `0038-13`, `0038-14`, `0038-14-repair`, `0038-15`, `0038-19`, `0038-20`,
  `0038-21`, `0038-22`, `0038-23`, `0038-27`. `0037-37`'s REF `927da0690` is an ancestor of `main`.
- Therefore basing `0038-16.01` off `refs/heads/main` at `7b2e2ce99` satisfies the base-and-merge
  rule with an empty merge set; no `--no-ff` absorption under `DEC-0044-007` was needed, and none
  was performed. Recorded rather than silently deviated.

## Integration checkpoint

`0038-16.01` carries **no** `Integration review: mandatory` attribute (verified in `TODO.md`).
No acceptance record is created by this session; `Acceptance: ✓` is outside this class's authority.

## Write scope

- `docs/pipeline/legacy-handoff-manifest-v1.json` (new)
- `docs/pipeline/legacy-handoff-manifest.md` (new)
- `_src/tools/legacy_handoff_manifest.py` (new)
- `_src/tests/test_legacy_handoff_manifest.py` (new)
- `docs/pipeline/tools.md` (registration row only)
- `TODO.md` (this Task's marker/history bullets only)
- this claim file

Explicitly **not** in scope: `DONE.md`, `0038-16`, `0038-16.02`, any `Acceptance:` record, any
merge of this branch anywhere, `.runner/`, `_src/runner/`, `run.sh`, the live runner protocol epoch.

## Progress

- `[p]` set; claim created.
- Inventory taken from the living enumerations rather than prose: the
  `## Skript-Ausführungs-Infrastruktur` table of `docs/pipeline/tools.md` (19 mechanisms), the
  `@v1` schema/result identifiers actually declared in each Feature `0038` tool, the four
  `runner_transaction.py` profiles, and the `0038-19` typed branch/merge contract.
- Verified all 17 `0037-37` contract digests still recompute correctly at `main` (zero drift).
- Verified the queue is **not** active: no `.runner/`, no `_src/runner/`; the singleton slot is
  the only accepted mechanism and is left untouched.

## Deliverables

| Path | Role |
|---|---|
| `docs/pipeline/legacy-handoff-manifest-v1.json` | Machine-readable authority (`legacy-handoff-manifest@v1`), 72 primitives |
| `docs/pipeline/legacy-handoff-manifest.md` | Human-readable rendering and rationale |
| `_src/tools/legacy_handoff_manifest.py` | Read-only, stdlib-only checker (`--check [--json]`) |
| `_src/tests/test_legacy_handoff_manifest.py` | 34 tests incl. fault injection for every guard |
| `docs/pipeline/tools.md`, `docs/pipeline/README.md` | Catalog/index registration |

## Design decisions

- **Totality is proven against a living enumeration, not a copy.** The checker parses the
  `## Skript-Ausführungs-Infrastruktur` mechanism table of `docs/pipeline/tools.md` and requires
  every mechanism to be a primitive source or a justified exclusion (rule `LHM074`). This reuses
  the pattern `0038-14` established with `automation_safety.tracked_automation_paths()`: adding a
  legacy mechanism without mapping it fails the gate instead of silently drifting.
- **"Multiply authoritative" is made mechanical** by two uniqueness domains: `authority_key`
  (`LHM048`) and typed action/contract ID (`LHM061`). Schemas and results are expressed as
  `contract.*@v1` / `result.*@v1` IDs so they share the same uniqueness proof as actions.
- **Exactly-one disposition** (`LHM056`) is the "zero unmapped" property; kind and consumer are
  cross-checked (`LHM058`/`LHM063`) so a typed action can never be filed against `0037-46.02`.
- **The singleton is preserved by assertion, not by omission.** The manifest declares
  `activates_queue: false`, `changes_authority: false`, `singleton.state: active`, and the checker
  additionally asserts that `.runner/` and `_src/runner/` do **not** exist (`LHM035`). Root
  `run.sh` is marked `ephemeral`, because its correct steady state is *absent*.
- **The `0038-19` section-10 forward-mapping table is generalized, not duplicated.** Its three
  action IDs (`git.base-branch@v1`, `git.merge-prereqs@v1`, `git.integrate-checkpoint@v1`) are
  carried over verbatim so this manifest cannot become a second, competing authority for them.
- **Retirement never precedes durable queue success.** `recovery.singleton-rollback` is itself a
  primitive, so the rollback window is a mapped obligation rather than an assumption.

## Validation (all run directly; `unprivileged`, no runner)

- `python3 _src/tools/legacy_handoff_manifest.py --check` → **PASS**, 0 findings;
  72 primitives, 65 typed-action mappings owning 74 unique action/contract IDs, 7 retirement
  triggers, unmapped = 0, multiply authoritative = 0, all 9 categories represented.
- `python3 -m unittest _src.tests.test_legacy_handoff_manifest` → **34/34 OK**.
- `python3 -m unittest _src.tests.test_chore_tool_inventory` → **26/26 OK** (no regression).
- `python3 _src/tools/chore_tool_inventory.py --check` → **PASS**, exit 0 (`missing=5` unchanged
  and pre-existing: `candidate_budget`, `check_policy_provenance`, `chore_tool_inventory`,
  `process_doc_doctor`, `task_context_capsule`).
- `python3 _src/tools/automation_safety.py --root . --path _src/tools/legacy_handoff_manifest.py --json`
  → **PASS**, 0 findings on the new tool.
- `python3 _src/tools/automation_safety.py --root . --json` (repository-wide) → **PASS**,
  `policy_errors: 0`, `unresolved_critical: 0` (37 advisory / 24 disposed-critical, all
  pre-existing).
- `python3 _src/tools/process_doc_doctor.py` → 97 documents, **0 errors** (30 pre-existing
  warnings/infos, none naming the new documents).
- All 17 `0037-37` contract digests recompute correctly against the working tree (zero drift).

## Findings dispositioned

- **Carried TK-2 confirmation, recorded not resolved.** `0038-27` and the `0038-22` integrator
  reconciliation re-pointed the `automation_safety_policy.json` dispositions for
  `_src/tools/sync_to_devel.sh` and `_src/tools/provision_tmp_worktree.sh` to `owner_task: 0038-16`
  as durable custodian, flagging it for confirmation when `0038-16` or Feature `0038`'s integrating
  task is worked. This Subtask is not `0038-16` and has no authority to confirm it; it is recorded
  in the manifest under primitive `validation.automation-safety` and in
  `docs/pipeline/legacy-handoff-manifest.md` so the confirmation cannot be lost.
- **`BLOCKING-EXTERNAL-001`** (external approval/signing/hosting credential readiness, owned by
  `0037-49`) is carried as primitive `approval.external-readiness-blocker`, matching the bound
  review package's residual-risk list. Not resolved here; not a `[u]` condition for this Subtask.

## Backlog repair

**None required.** The Acceptance Criteria and Definition of Done are satisfiable entirely with
artifacts owned by this Subtask: the manifest binds only already-committed, already-terminal
predecessor work, and its consumers (`0037-46.01`, `0037-46.02`) verify and incorporate it later
rather than being needed to produce it. No `TODO.md` text other than this Task's own marker and
history bullets was changed.

## Boundaries honoured

- Root checkout `/Users/tobias.anton/devel/autodocs` was never written (`DEC-0044-009`); all
  mutation happened in `.worktrees/0038-16.01`.
- No cross-chain absorption occurred, so `DEC-0044-007`'s `--no-ff` requirement was not engaged.
- Branch `0038-16.01` is left **at rest**: not merged into `0038-16`, `0038`, `main` or anywhere else.
- `DONE.md`, `0038-16`, `0038-16.02` untouched. No `Acceptance: ✓` created, changed or removed.
- No foreign claim, marker or execution request was modified. The stale root-tree untracked files
  observed at session start (`TODO-perplexity-0037-37-…`, `TODO-zed-0038-24-…`, `.review-worktrees/`)
  belong to other sessions and were left untouched — reported to the dispatcher, not repaired.

## Check-in provenance

This session is a **subagent**. No user-authored prompt was delivered to it directly; the durable
trigger is the dispatching session's briefing, whose material content is reproduced in the
"Task (verbatim from `TODO.md`)", "Write scope" and "Boundaries honoured" sections above. Per
`AGENTS.md` ("If no user prompt directly triggered it, state that fact rather than inventing a
prompt"), no user prompt text is fabricated here. Executor: Claude Code subagent `Seven-Azan`,
execution date 2026-08-21 (UTC). The dispatching session retains the user-facing provenance.
