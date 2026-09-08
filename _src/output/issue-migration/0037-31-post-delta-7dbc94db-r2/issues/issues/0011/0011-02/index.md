---
schema_version: "1.0"
id: "0011-02"
level: "task"
parent: "0011"
state: "closed"
visibility: "internal"
prerequisites:
  - "0011-01"
  - "0020-07"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2837"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0011-02:0011-01, 0011-02:0020-07 Extend the single approved Level-1 assessment method and worksheets with PA 2.1/PA 2.2 achievements, CL2 aggregation/rating rationale, assessor competence/independence, evidence validation, and report content; do not create a parallel assessment method or duplicate Level-1 outcome worksheets. Claim: `TODO-subagent-0011-02.md`. REF: `docs/dossiers/req-0011-02-cl2-worksheets.md` and `docs/pipeline/aspice-cl2-assessment-input.md`. No `Acceptance: ✓`.

## Scope

- **Define contract:** `docs/dossiers/req-0011-02-cl2-worksheets.md`. Extended single 14-process assessment method with PA 2.1 (GP 2.1.1–2.1.6) and PA 2.2 (GP 2.2.1–2.2.4). CL2 aggregation rule: PA 1.1 >= L AND PA 2.1 >= L AND PA 2.2 >= L per process instance. No cross-process averaging. Refuse-at-use for substituted origins (`DEC-0020-002`, `REQ-0020-02-01..09`). Assessor competence/independence required. Report structure defined. No ratings filled. No `Acceptance: ✓`.

## Acceptance criteria

- **AC-001** (1) Single assessment method and worksheets extended for CL2 across 14 processes without parallel duplication. (2) PA 2.1 and PA 2.2 achievement criteria defined. (3) CL2 aggregation rule (`PA 1.1 >= L`, `PA 2.1 >= L`, `PA 2.2 >= L`) and prohibition of averaging across processes enforced. (4) Evidence validation with `0020-02` metadata and refuse-at-use of non-ECU origins per `DEC-0020-002`. (5) Assessor competence and independence requirements specified. (6) Report content scaffolding specified

## Definition of Done

Dossier `docs/dossiers/req-0011-02-cl2-worksheets.md` and extended `docs/pipeline/aspice-cl2-assessment-input.md` committed with claim file `TODO-subagent-0011-02.md`; not `Acceptance: ✓`.
