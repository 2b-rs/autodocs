---
schema_version: "1.0"
id: "0038-05.02"
level: "subtask"
parent: "0038-05"
state: "closed"
visibility: "internal"
prerequisites:
  - "0038-02"
  - "0038-05.01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1680"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
  - id: "AC-005"
    status: "active"
  - id: "AC-006"
    status: "active"
---

## Goal

PREREQ: 0038-05.02:0038-05.01, 0038-05.02:0038-02 Integrate all editor candidate promotion into the durable legacy transaction coordinator and retire its separate regex closure renderer. REF: b70238ad0ea186fcf4c28579515b4ec695f048f1

## Scope

- **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `seven-chell (0038-05.02-Commit)`). Abgenommene Baseline `b70238ad0ea186fcf4c28579515b4ec695f048f1`; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. 7 Fehlschläge/54 bestanden am eigenen REF, exakt zurückgeführt auf denselben ererbten Zustand (Commit datiert vor der 0038-10-Reparatur); dieselben 7 Tests gegen aktuellen main erneut gefahren: 7/7 grün. `runner_transaction.py` selbst von 0038-05.02 nicht modifiziert.
  - **Closed (2026-08-20):** Added the fixed typed `legacy-editor-candidate-v1` profile to `_src/tools/runner_transaction.py`: preflight and a new `materialize_editor_candidate()` both call `legacy_task_editor.verify_candidate_for_promotion` to recheck every candidate manifest/blob/diff/read-set/absent-path preimage against the live repository before any mutation, then write the verified changes into the existing detached candidate worktree so the unmodified promote/rollback/journal/lock/signal/CAS-publish/recovery machinery performs the actual atomic multi-file promotion. `render_task_closure()` now delegates Task/Feature/section-boundary parsing to `legacy_task_editor.parse_backlog` instead of a duplicate regex detector, while intentionally keeping its own narrower precondition set (recorded backlog-repair decision: `close-task-v1`'s coordination claim binds `base_commit` to the current transaction's `expected_base`, not the Task's pickup base, so the editor's stricter claim-pointer cross-check does not apply without changing that unrelated, already-accepted convention). Also fixed a real `--no-renames` gap in `_prepare_commit` that this integration exposed (a delete plus byte-identical create, as claim-finalization/handoff produce, was collapsed by git's rename heuristic and dropped from the computed changed-path set). Validation: `python3 -m unittest _src.tools.test_runner_transaction.EditorCandidateTransactionTests` passed 13/13 new failure-injection tests (success, tampered/drifted-candidate rejection, scope mismatch, and rollback/recovery at the before-materialize/during-promote/after-promote/after-publish boundaries); `python3 -m unittest _src.tools.test_runner_transaction.RunnerTransactionTests` passed 41/48 with the remaining 7 confirmed pre-existing on this macOS environment via `git stash` against the unmodified branch tip (zero regressions); `python3 _src/tools/automation_safety.py --path _src/tools/runner_transaction.py --json` returned `verdict: PASS` with zero unresolved critical findings/policy errors. REF: `b70238ad0ea186fcf4c28579515b4ec695f048f1`.

## Acceptance criteria

- **AC-001** Add a fixed typed editor-candidate action/contract to `_src/tools/runner_transaction.py`
- **AC-002** bind exact operation/candidate/read-set/member digests
- **AC-003** recheck all preimages immediately before publication
- **AC-004** promote multi-file pickup/handoff/finalization with the `0038-02` journal/lock/signal/resume/rollback guarantees
- **AC-005** replace `render_task_closure()` with the editor core rather than a second parser
- **AC-006** and persist candidate/diff/result/recovery evidence. No operation may expose a successful partial claim/TODO state or overwrite a concurrent edit

## Definition of Done

Failure injection before/after every candidate, TODO, claim create/archive/delete, journal, result, and CAS boundary proves all-old/all-new or deterministic recovery; the full historical suite and real two-commit closure flow pass through the coordinator; no direct legacy writer or duplicate semantic renderer remains.
