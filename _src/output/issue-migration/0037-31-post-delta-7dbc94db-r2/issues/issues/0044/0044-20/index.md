---
schema_version: "1.0"
id: "0044-20"
level: "task"
parent: "0044"
state: "closed"
visibility: "internal"
prerequisites:
  - "0044-17"
  - "1788"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1296"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0044-20:0044-17 Implement `DEC-0044-033` terminal-claim lifecycle, exact-set finalization, and target-policy validation compatibility.

## Scope

- **Architecture authority:** `docs/dossiers/dec-0044-033-terminal-claim-lifecycle.md`; supporting pre-mutation scope review `docs/dossiers/0044-20-terminal-claim-lifecycle-scope-review.md`. Governance must be reachable from `main` before implementation starts. Implementer and Integrator are distinct from Architect `agent:data:0044-20:1788038395542-d19fafda`.
  - **Implementation scope:** `_src/tools/legacy_task_doctor.py`, `_src/tests/test_legacy_task_doctor.py`, `_src/tests/fixtures/legacy_task_doctor/`, `_src/tools/legacy_task_editor.py`, `_src/tests/test_legacy_task_editor.py`, `_src/tools/runner_transaction.py`, `_src/tools/test_runner_transaction.py`, `docs/pipeline/legacy-task-doctor.md`, `docs/pipeline/legacy-task-editor.md`, own claim, and exact Task bookkeeping. Any additional governance or consumer path requires a separately reconciled scope.
  - **Validation derivation:** Red-first plus adjacent cases cover active `TODO-*`, terminal awaiting-Acceptance `TODO-*`, accepted and premature `DONE-*`, active lease/award, marker divergence, absent/ambiguous claims, two-claim all-or-nothing finalization, and a pre-`0044-17` candidate. Property or exhaustive set-population tests prove no strict subset can pass. Focused Doctor, Editor, and transaction suites plus registered process-doc validation are required.
  - **Migration and rollback:** No bulk rename or history rewrite. Existing accepted records remain. Reconcile legacy inconsistencies only in the next authorized terminal/review/Acceptance transaction. The implementation must be revertible without invalidating the governance rule or Acceptance history.
  - **Integration review: mandatory.** **Rationale (Architect):** this changes a blocking validator and the atomic terminal transition used by every Task. A false positive can prevent integration indefinitely; a false negative can leave live ownership or manufacture accepted provenance.

## Acceptance criteria

- **AC-001** A terminal, lease-free exact-item `TODO-*` matching its `[x]`/`[w]` Task is valid awaiting-Acceptance provenance
- **AC-002** `DONE-*` without current Acceptance, terminal state with an active lease/award, marker/claim divergence, missing or ambiguous participating claims, and partial multi-claim finalization fail closed. The supported finalization transaction discovers the complete exact-item root-claim set and aligns marker, real REF, every claim state, lease release, and terminal coordination atomically. Policy-sensitive validation of legacy candidates records and uses the canonical target integration-policy validator ref and digest instead of stale branch-local semantics

## Definition of Done

Code, fixtures, and registered documentation agree with `DEC-0044-033`; validator provenance is machine-verifiable; negative-path evidence is committed; no `0020` product or claim is mutated; the mandatory checkpoint passes before activation.
