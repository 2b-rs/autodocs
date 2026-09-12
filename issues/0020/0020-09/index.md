---
schema_version: "1.0"
id: "0020-09"
level: "task"
parent: "0020"
state: "open"
visibility: "internal"
prerequisites:
  - "0020-05"
  - "0020-06"
  - "0020-08"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2664"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0020-09:0020-05, 0020-09:0020-06, 0020-09:0020-08 Create and validate the selected-profile execution register: for every included base, cybersecurity, safety, or other lifecycle process, identify the exact execution Feature/task and completion gate; for every shared process, record whether it is rated, the assessed unit's exact outcomes/activities and execution gate, and the external input/output/acceptance/feedback gate; for every fully external process, identify the approved interface-evidence gate and prohibit an internal rating. Materialize every conditional predecessor, release, and assessment relationship as a concrete TODO prerequisite or machine-enforced selected-profile edge; reject a profile, release, evidence freeze, or assessment when an included process or selected edge has no executable, satisfied path to valid evidence, or when interface evidence is substituted for the assessed unit's own performance. Claim: `TODO-hguh-0020-09-20260826T131500Z.md`; owner_token: `agent:hguh:0020-09:20260826T131500Z`. REF: `c20891ea020d9ca108390e0282568e1a0b44b6c2` (`docs/dossiers/req-0020-09-execution-register.md`). No capability rating. No `0025` freeze. No `Acceptance: ✓`.

## Scope

- **Define contract (2026-08-26, hguh):** `docs/dossiers/req-0020-09-execution-register.md`. 14 included processes mapped to Features/completion gates. Shared: 0. CS/FS Features: 0. Fully external interface gates from `0020-05`. SYS/VAL not rated. Edges: existing `0020-09` consumers plus `0025-02`/`0025-03` freeze (not implemented here). Refuse-at-use (`DEC-0020-002`). No `Acceptance: ✓`.

## Acceptance criteria

- **AC-001** (1) Each of the 14 included processes names execution Feature, completion Task, and TODO path. (2) Shared set recorded (empty). (3) Fully external processes have interface-evidence gates and no internal rating. (4) CS/FS not in the selected profile. (5) SYS/VAL receive no internal rating and are not unconditional blockers. (6) Relationships materialized as existing TODO prerequisites or named `0025-02`/`0025-03` edges
- **AC-002** no new start-gates and no `_src/validate.py` registration. (7) Register refuses substituted interface evidence and wrong-origin outcome evidence at use. (8) No N/P/L/F assigned

## Definition of Done

Dossier committed on `0020-09` with `0020-08` present; not `Acceptance: ✓`.
