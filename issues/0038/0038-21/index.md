---
schema_version: "1.0"
id: "0038-21"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-04"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1884"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0038-21:0038-04 Add a Feature-integration-readiness predicate and human-triggered readiness notice. REF: d2fa0e17c699a13637da9a11cb35e6a5a8360e5d

## Scope

- **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0038-21-Commit)`). Abgenommene Baseline `d2fa0e17c699a13637da9a11cb35e6a5a8360e5d`; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. 48/48 eigene Tests am eigenen REF.
  - **Closed (2026-08-20):** Extended `_src/tools/legacy_task_doctor.py` with a deterministic per-Feature `integration-ready` predicate (terminal in-scope Task/Subtask set, terminal transitive PREREQ closure, no unaccepted mandatory checkpoint in that closure), a new `integration_readiness` report array covering every evaluated Feature, and an info-severity `LTD-FEATURE-INTEGRATION-READY` finding/advisory-plan emitted only on genuine readiness — realized through the doctor's existing non-mutating findings/plans/summary pipeline as the concrete notification channel, since `SENTINEL.md`'s only mechanism (`run.sh`) is already flagged `LTD-POLICY-CONTRADICTION` against `SANDBOX.md`; design rationale recorded in `docs/pipeline/legacy-task-doctor.md`. Also corrected a coupling defect in `test_tracked_current_determinism_evidence_is_digest_bound` that compared Task `0038-04`'s tracked accepted evidence against live worktree tool bytes instead of the tool blob at `0038-04`'s own recorded REF (0038-04's evidence file itself is untouched). Four new fixtures (not-ready, ready-linear, ready-parallel, blocked-by-unaccepted-high-risk-prerequisite) plus six focused tests. Validation: `py_compile` clean; `python3 -m unittest discover -s _src/tests -p 'test_legacy_task_doctor.py'` 48/48 passed; `python3 _src/tools/automation_safety.py --path _src/tools/legacy_task_doctor.py --json` returns `PASS` with zero findings; a live `--root .` scan is byte-deterministic across two runs and surfaces one real, sensible `LTD-FEATURE-INTEGRATION-READY` finding (Feature `0034`) without mutating anything.

## Acceptance criteria

- **AC-001** Extend the read-only `_src/tools/legacy_task_doctor.py` to compute a deterministic `integration-ready` predicate — every in-scope Task/Subtask `[x]`/`[w]` with a terminal, acceptance-consistent prerequisite closure — and, on transition to ready or during an otherwise-idle global scan, emit a bounded readiness notice through the canonical `SENTINEL` retrigger channel naming the ready Feature and stating it needs an explicitly assigned privileged integrator. The doctor never self-assigns, integrates, or mutates acceptance

## Definition of Done

Fixtures for not-ready, ready-linear, ready-parallel, and blocked-by-unaccepted-high-risk-prerequisite Features produce deterministic JSON plus a ≤10-line summary; the notice is emitted only on genuine readiness, carries no acceptance action, and performs no mutation.
