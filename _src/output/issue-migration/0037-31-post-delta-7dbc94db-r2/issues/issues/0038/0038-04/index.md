---
schema_version: "1.0"
id: "0038-04"
level: "task"
parent: "0038"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-41"
  - "0038-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1659"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0038-04:0038-01, 0038-04:0037-41 Implement a read-only legacy Task/claim/bootstrap doctor. REF: cc99c1f27a0be1c53357b6aaef829aab8ae36770 **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0038-04-Commit)`). Abgenommene Baseline `cc99c1f27a0be1c53357b6aaef829aab8ae36770`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). 42/42 Tests am eigenen REF; Determinismus durch zwei frische Doctor-Läufe zusätzlich selbst bestätigt (identisches SHA-256).

## Scope

- **Closed (2026-08-17):** Committed the executable stdlib-only read-only doctor, exact normalized JSON and ≤10-line summary contract, safe advisory plans, six clean/historical/negative fixture cases, 42 focused tests, operator/catalog documentation, and compact current-drift evidence. Two live 824,258-byte reports were identical (SHA-256 `0aa6cad564c8d949a6ccb1851d8a9786e6fcda062ea85b6e24d7fa1dd3797850`) with 354 expected findings and zero unsafe plans. Independent review `e1b3420a-c9bf-47b6-ac3e-04c3e187c4c2` returned `ACCEPT` with no blocker/high findings. The isolated clean-HEAD candidate passed focused and automation-safety checks; full project validation passed after explicit candidate-only shims for six pre-existing absent foreign review-UI log targets. Provenance receipt SHA-256 `180e712bb2aff71097088a93ed2b3ab32a36a1d99fc7d450df86e3b0a2ddf020`.

## Acceptance criteria

- **AC-001** Normalize `TODO.md`, `DONE.md`, `agent-workflow.json`, and exact active claims
- **AC-002** detect undefined markers such as `[d]`, malformed/hidden/duplicate/unreachable REFs, Task/claim state disagreement, stale terminal claims, filename/request/token/base/scope mismatches, missing next steps, invalid prerequisites/cycles, eligible parent closures, broken instruction links, and contradictions such as `SENTINTEL.md` versus `SENTINEL.md`/runner-notification policy. It prepares exact-path reconciliation plans but never takes over or deletes a foreign claim

## Definition of Done

Current known drift and historical malformed-claim/REF/marker fixtures produce deterministic JSON plus a summary of at most ten lines; a clean fixture produces zero findings without mutation.
