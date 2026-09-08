---
schema_version: "1.0"
id: "0019-10"
level: "task"
parent: "0019"
state: "open"
visibility: "internal"
prerequisites:
  - "0019-09"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:3027"
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

PREREQ: 0019-10:0019-09 Publish the authorized views and close the v0.6.0 import campaign and local campaign-evidence record under `docs/pipeline/aspice-level1-score-import.md` without waiting for ECU scope; classify its canonical origin as `documentation-execution`, describe it as documentation-campaign evidence, make no capability claim, and leave any later named documentation-process mapping to `0011-03`.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Post-generation checks satisfy the decision in `0019-08`
- **AC-002** the campaign report demonstrates every criterion in `aspice-level1-score-import.md`: committed manifest, traced/versioned records, persisted validation outcome, human-readable outcome summary, explicit curator decision, publication result, and campaign closure
- **AC-003** unresolved items and exclusions are quantified and linked to queues

## Definition of Done

Campaign is closed according to Phase 6 of `processes.md`, the accepting decision/closure report and generated result are committed, no open validation blocker is mislabeled as valid, and all Feature 0019 Definition-of-Done bullets are independently evidenced by committed artifacts and test reports.
