---
schema_version: "1.0"
id: "0044-19"
level: "task"
parent: "0044"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:3080"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Implement the branch-aware frontier query according to `docs/pipeline/frontier-query-spec.md`. **REF:** `1cd82b57f9b99c4b7583a4db1036809f1308cecb`. Claim: `TODO-benjamin-0044-19-20260829.md`.

## Scope

- **Integration review (2026-08-29, Integrator `obrien`, independent of Implementer `benjamin` and Spec Author `seven`):** Checkpoint passed; frontier query and test suite integrated. Review REF: `039fef24e100ae983574971c26b5278c2e6f4773`; Review evidence: `docs/campaign-evidence/0044-19/integration-review-obrien-20260829.md`. Task Acceptance deferred to feature integration.

## Acceptance criteria

- **AC-001** Implement the query returning a five-state fail-closed partition (available / in-flight / blocked-prereq / held / indeterminate). Must use claim files and commit subjects for item-to-branch resolution, not branch names. Must include the blind-spot declaration. Must distinguish terminal-accepted, terminal-recorded, and terminal-contested prerequisites. Must provide AE-3, AE-4, and AE-5 falsification and property evidence

## Definition of Done

Python script implemented in `_src/tools/` passing all falsification cases, with unit tests covering the five-state matrix, blind-spot printing, and three-state prereq logic.
