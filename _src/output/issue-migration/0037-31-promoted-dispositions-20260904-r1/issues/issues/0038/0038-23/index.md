---
schema_version: "1.0"
id: "0038-23"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-04"
  - "0038-07"
  - "0038-21"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1898"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0038-23:0038-04, 0038-23:0038-07, 0038-23:0038-21 Enforce integration-checkpoint attributes and architect authority in the legacy tooling. REF: 63fdb98e9973aeec5b7a895cdc35fee30ab7948f

## Scope

- **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `seven-corin (0038-23-Commit)`). Abgenommene Baseline `63fdb98e9973aeec5b7a895cdc35fee30ab7948f`; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. 13/13 eigene neue Tests (CheckpointAuthorityTests) + 54/54 legacy_task_doctor-Tests; 11 Fehlschläge in test_legacy_task_editor.py als 100% ererbt von 0038-05.01 bestätigt (keiner der eigenen 0038-23-Tests betroffen).
  - **Backlog repair (2026-08-20):** The declared `PREREQ:` line named only `0038-04`/`0038-07`, but the Task's own acceptance criteria explicitly build on Task `0038-21`'s delivered `integration_readiness` predicate/mechanism in `_src/tools/legacy_task_doctor.py` ("Compute the `integration-ready` predicate per checkpoint ... for the `0038-21` readiness notice") — a missing prerequisite edge and a drafting defect determinable from the Task's own text and repository evidence, not a human decision. Added `0038-23:0038-21`; branch `0038-21` was merged in as the first mutating step so the already-landed predicate is extended rather than reimplemented or conflicted with.
  - **Completion evidence (2026-08-20):** Committed `CheckpointState`/`_checkpoint_findings()` in `_src/tools/legacy_task_doctor.py` (new `checkpoint_states` report field; findings `LTD-CHECKPOINT-MISSING-AUTHORITY`, `LTD-CHECKPOINT-MALFORMED`, `LTD-CHECKPOINT-UNFLAGGED-HIGH-RISK`) and `_enforce_checkpoint_authority()` plus the optional `architect_authority` operation field in `_src/tools/legacy_task_editor.py` (new rules `LTE-CHECKPOINT-AUTHORITY-REQUIRED`, `LTE-CHECKPOINT-MALFORMED`), applied uniformly at the point every one of the nine typed kinds finalizes its rendered Task-block text. Authority is a textual `(architect)`-tagged marker, not capability class (`docs/pipeline/process-roles.md` fixes the architect's minimum class at `sandboxed/grunt`). Also tightened `0038-21`'s `_is_mandatory_checkpoint_line` and the new parser to require the structural attribute-bullet anchor (`^\s*-\s*\*\*integration review\b`), fixing a real false-positive on prose that merely discusses the attribute (found via live-repository testing on `0038-23`'s and `0038-02`'s own text) without changing behavior on any real checkpoint or existing fixture. Added three named doctor fixtures (`checkpoint-well-formed`, `checkpoint-missing-authority`, `checkpoint-unflagged-high-risk`) plus seven focused doctor tests, and a `CheckpointAuthorityTests` class (13 tests) plus `architect_authority` schema tests in the editor suite. Updated `docs/pipeline/legacy-task-doctor.md` ("Checkpoint-attribute rules") and `docs/pipeline/legacy-task-editor.md` ("Checkpoint-attribute authority"). Validation: `py_compile` clean; doctor suite 54/54 passed; editor suite 52/52 passed (`TMPDIR=/private/tmp`; default macOS temp-symlink failure verified pre-existing/unaffected via `git stash`); live `--root .` doctor scan produces 14 `LTD-CHECKPOINT-UNFLAGGED-HIGH-RISK` advisories and zero missing-authority/malformed findings against the real backlog; `automation_safety.py --policy _src/tools/automation_safety_policy.json` on the four changed files returns the same 16 pre-existing unresolved findings (byte-identical rule/severity/status set, confirmed via `git stash`) as before this Task's diff — all in pre-existing test methods this Task did not touch, with stale policy digests predating this change — and zero new findings from this Task's own code. See `TODO-seven-corin-0038-23-20260820T031602Z.md` for the complete claim, branch/merge, and validation record.

## Acceptance criteria

- **AC-001** Extend the read-only `_src/tools/legacy_task_doctor.py` and the digest-bound `_src/tools/legacy_task_editor.py` to recognize, validate, and index the `**Integration review:** mandatory` attribute: verify that every checkpoint records a set-by architect authority plus rationale
- **AC-002** that a node touching an irreversible migration, external effect, credential/security boundary, or public release which is left unflagged carries an explicit architect no-checkpoint justification
- **AC-003** and that no sandboxed/grunt-authored change sets, clears, or moves the attribute. Compute the `integration-ready` predicate per checkpoint (not only per Feature) for the `0038-21` readiness notice, and expose each node's required-integration state (none / pending / passed) alongside its marker. The architect's bounded work-package/context capsule (`0038-07`) records the declared checkpoints and their rationale

## Definition of Done

Fixtures cover a well-formed checkpoint, a checkpoint missing rationale/architect, an unflagged high-risk node missing its no-checkpoint justification, a grunt-authored attribute change (rejected), and per-checkpoint readiness; the doctor's JSON plus ≤10-line summary report checkpoint state deterministically without mutation, and the editor refuses any attribute write not carrying architect authority.
