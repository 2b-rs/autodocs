---
schema_version: "1.0"
id: "0044-08"
level: "task"
parent: "0044"
state: "open"
visibility: "internal"
prerequisites:
  - "0044-01"
  - "0044-02"
  - "0044-03"
  - "0044-04"
  - "0044-05"
  - "0044-06"
  - "0044-07"
  - "0044-12"
  - "0044-13"
  - "0044-14"
  - "0044-17"
  - "0044-18"
  - "0044-20"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1305"
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

PREREQ: 0044-08:0044-01, 0044-08:0044-02, 0044-08:0044-03, 0044-08:0044-04, 0044-08:0044-05, 0044-08:0044-06, 0044-08:0044-07, 0044-08:0044-12, 0044-08:0044-13, 0044-08:0044-14, 0044-08:0044-17, 0044-08:0044-18, 0044-08:0044-20 Integrate the Feature and prove the improved process on one real feature end to end.

## Scope

- **Integration review: mandatory.** **Rationale (architect):** the Feature's integrating task and review floor. Process rules that are individually correct but contradictory in composition are exactly the defect this Feature exists to remove.

## Acceptance criteria

- **AC-001** One real feature is broken down under the new instruction, its tasks matched to agents by the deterministic matcher, at least one integration performed under the policy-precedence rules, and every requirement ID of `RQ-SRC-04`'s derivation has a disposition
- **AC-002** contradictions between authority documents are reported, not smoothed over
- **AC-003** the two customer-confirmation points flagged in the intake dossier (`RQ-CB-06`/`RQ-CB-07` interpretation) are resolved with the user

## Definition of Done

Committed; the end-to-end evidence is retained; `AGENTS.md`, `SANDBOX.md`, `process-roles.md`, `branch-workflow.md`, and `task-acceptance.md` agree.
