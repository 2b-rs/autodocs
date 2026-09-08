---
schema_version: "1.0"
id: "0044-06"
level: "task"
parent: "0044"
state: "closed"
visibility: "internal"
prerequisites:
  - "0044-04"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1203"
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
---

## Goal

PREREQ: 0044-06:0044-04 Develop and calibrate a method for estimating the cognitive demands of a work package on an AI agent, including handling of nondeterministic capability. *(architect-elaboration)* REF: 942a648fd7e0623a76027aeb0c4c2aa8cf2683d9 (cognitive demand study, AGENTS.md flagging protocol, feature breakdown updates). Claim: TODO-jadzia-0044-06-731dec22.md (owner_token: agent:jadzia:0044-06:731dec22).

## Scope

- **Requirements covered:** `RQ-CB-05`, `RQ-CB-06`.
  - **Context:** No established state of the art exists; the project's own history (reworked tasks, failed runs, token consumption, `[u]`/defect records in `TODO.md`/`DONE.md`) is the available ground truth for calibration.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** an estimation model with recorded mispredictions; wrong estimates degrade scheduling, not authority or data integrity. Re-examined at `0044-08`.

## Acceptance criteria

- **AC-001** A documented estimation method assigns each work package a demand class from observable properties (scope breadth, required reasoning depth, context volume, ambiguity, verification hardness)
- **AC-002** the method is calibrated against at least ten historical tasks with known outcomes and its misprediction cases are analyzed
- **AC-003** the nondeterminism protocol defines how an overwhelmed agent flags its own job, and which orchestrator-side quality gate catches the case where it does not
- **AC-004** predictions are recorded so future outcomes keep improving the calibration

## Definition of Done

Committed as a study plus a normative section consumed by `0044-04`'s instruction and `0044-05`'s schema (demand class field); the flagging protocol is anchored in `AGENTS.md`.
