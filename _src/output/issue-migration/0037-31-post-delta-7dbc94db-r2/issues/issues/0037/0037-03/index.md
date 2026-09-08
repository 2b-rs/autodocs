---
schema_version: "1.0"
id: "0037-03"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-03.01"
  - "0037-03.02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2022"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-03:0037-03.01, 0037-03:0037-03.02 Complete the review-ready lifecycle, authority, closure, and claim contract. **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `(Aggregation)`). Abgenommene Baseline `f3adcde91487f774d29b80985f54a5736da556bd`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). Reine Aggregation; beide Kinder als Vorfahren bestätigt.

## Scope

- **Closure (2026-08-16):** Aggregates lifecycle/closure/decision contract `f3adcde91487f774d29b80985f54a5736da556bd` and cross-clone claim/recovery contract `536c824f095f1563b9c565378afecabb4ff07bf1`; both child closures were verified reachable. This is a local review-ready consistency closure, not architecture approval. Task `0037-37` independently verifies and incorporates this package; approval remains gated by `0037-07`.

## Acceptance criteria

- **AC-001** Lifecycle and live-claim protocols agree on state, authority, evidence, recovery, and event semantics and do not promise cross-clone guarantees Git cannot provide

## Definition of Done

Both Subtasks are complete and included in the architecture review package; artifacts are review-ready, not described as approved before `0037-07`.
