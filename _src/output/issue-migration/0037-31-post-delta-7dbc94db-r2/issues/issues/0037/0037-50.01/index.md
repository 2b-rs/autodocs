---
schema_version: "1.0"
id: "0037-50.01"
level: "subtask"
parent: "0037-50"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2177"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Record the queue/singleton failover gate decision on current `main`. REF: `0ffac017ef05ef14dd6e622f94bc1580d3e4f1f5`. Claim: `TODO-jean-luc-0037-46.02-governance-20260823T134915Z.md`; owner token: `agent:jean-luc:0037-46.02-governance:20260823T134915Z`.

## Scope

- **Integration review:** not mandatory. **No-checkpoint justification (architect):** Architect `data`, proposal `164890ec3c`: this is the mandatory pre-mutation governance record, not an implementation or deployment boundary; the terminal `.05` package is the one integrating checkpoint.

## Acceptance criteria

- **AC-001** A conforming `decision-record@v1` binds the current user's selection, Datas independent scope review, Geordis rejected baseline, all affected work units/gates, the admission-coupled drain-before-reopen invariant, self-application, rollback and no-grandfathering behavior, considered alternatives, consequences, and `Waiver: none` without implementing the gate

## Definition of Done

`DEC-0037-001` is unique and reachable on `main`; `process_doc_doctor.py --json` reports zero errors; `git diff --check` passes; the exact decision REF and proposal/review pins are recorded.
