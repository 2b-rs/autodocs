# Claim — `0045-00` Management-gate preparation

- **item:** `0045-00-preparation`
- **task_id:** `0045-00`
- **owner_token:** `agent:data:0045-00-preparation:1788212597555-9ecd6db1`
- **offer / authority:** priority award `1788212597555-9ecd6db1`; supervisor execution wake `1788212615693-b5107628`
- **capability_class:** `privileged`
- **execution_authority:** direct local read/Git/text validation in the item-owned worktree; preparation only
- **coordination_state:** `in_progress`
- **base_commit:** `5c6068537aa4a304c940ca82f62b466a08d72136`
- **branch:** `0045-00`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/0045-00-data-20260831`
- **startup_review:** `AGENTS.md`, `SANDBOX.md`, `TODO.md` Feature `0045` and Task `0045-00`, `docs/pipeline/decision-record.md`, `docs/pipeline/score-feedback-loop.md`, `docs/dossiers/score-feedback-loop-requirements-20260831.md`
- **write_scope:** `docs/dossiers/score-feedback-loop-gate-decision-preparation.md`, `docs/pipeline/score-feedback-loop-approved-baseline.json`, this claim
- **current_phase_scope:** preparation dossier and this claim only; the approved baseline remains forbidden until the supervisor supplies both the resolved Management-decision reference and the distinct Architect-review reference
- **external_resources:** read-only inspection of the current agent-inbox repository selector/assignment Runner contract; mailbox coordination only

## Contract and boundaries

Prepare permanent evidence, affected work products/processes, policy alternatives
and consequences, recommendation, paused action, and exact proposed
interface/selector/Runner digests for the Management decision. Commit and report
the immutable preparation candidate and form-ready inputs to the supervisor,
then hold.

This claim grants no authority to submit or resolve a decision, allocate or
author a `DEC-*` record, author the distinct Architect review, activate the
proposed pipeline, mutate agent-inbox, accept or integrate this work, publish,
move Feature `0045` to `DONE.md`, or advance `main`.

## Assumptions and test derivation

- The authoritative autodocs selector is the exact `agent-workflow.json` blob
  at the assigned base; the agent-inbox Runner evidence is pinned by repository
  commit and file digests, not by mutable-path prose alone.
- The preparation is non-operative and may recommend one option, but only
  Management selects it and only the separately assigned Architect reviews the
  resulting cross-item scope.
- Validation will check exact path scope, Git diff hygiene, all cited commits,
  SHA-256 digests, option completeness, affected unit/gate coverage, explicit
  paused action, and the absence of `DEC-*`, review, baseline, or activation
  artifacts in this phase.

## Recovery

Before commit, discard only this claim's declared-path edits. After commit,
correct by a new commit on this branch; do not rewrite history. The safe stop is
to withhold the preparation candidate and leave every downstream `0045` start
gate closed.

## Progress and validation

- Established the item-owned worktree from the exact assigned branch/base;
  root checkout remained read-only.
- Prepared the permanent dossier with four complete alternatives, a selected
  recommendation, consequences, affected products/processes/units/gates,
  rollback and paused-action boundaries, and form-ready Management inputs.
- Pinned exact autodocs and agent-inbox commits, Git blobs, full-file SHA-256
  values, and a canonical compact Runner-contract projection digest. Later
  agent-inbox `main@01937d6a0` retains the exact pinned evidence blobs.
- Recorded the machine/prose contradiction between the live Runner contract
  and stale README wording; no compatibility or authority was invented.
- `process_doc_doctor.py --root . --json`: PASS, `ok: true`, zero findings for
  the new dossier.
- Exact scope contains only this claim and the preparation dossier;
  `git diff --cached --check` passes. No approved baseline, Architect review,
  `DEC-*` record, Task marker, implementation, activation, Acceptance,
  integration, publication, `DONE.md`, agent-inbox mutation, or `main` advance
  occurred.

## Handoff

Commit the two-path preparation candidate and report its exact immutable ref
plus the dossier's form-ready decision fields to Supervisor. Then transition
the assignment to review/hold. Resume baseline finalization only after
Supervisor supplies both the resolved Management-decision reference and the
distinct Architect-review reference.
