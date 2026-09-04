---
schema_version: "1.0"
id: "0037-26.06"
level: "subtask"
parent: "0037-26"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-17"
  - "0037-19"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2456"
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

PREREQ: 0037-26.06:0037-17, 0037-26.06:0037-19 Extend validation and build reports with stable findings, common run identity, and artifact manifests.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Migrate build-report `1.0` explicitly
- **AC-002** require shared run ID, source/tool/config commits, exact stage inputs/outputs, stable finding IDs, issue/criterion/campaign trigger, and success/failure
- **AC-003** combining reports requires the same run/artifact lineage and all required stages, never latest mtime

## Definition of Done

Integration tests reject mixed runs, missing/malformed stages, unstable findings, incomplete artifact sets, and self-validating report injection and support reverse trace from final report to trigger/input.
