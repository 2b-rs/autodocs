---
schema_version: "1.0"
id: "0012-07"
level: "task"
parent: "0012"
state: "closed"
visibility: "internal"
prerequisites:
  - "0012-02"
  - "0012-03"
  - "0012-04"
  - "0012-05"
  - "0012-06"
  - "0012-08"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2856"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0012-07:0012-02, 0012-07:0012-03, 0012-07:0012-04, 0012-07:0012-05, 0012-07:0012-06, 0012-07:0012-08 Extend campaign/project-plan schemas, validators, reports, templates, and controlled retention paths before managed execution so PA 2.1 evidence is generated and correlated through normal work rather than reconstructed retrospectively; add negative checks for missing, stale, cross-process-instance, or retrospectively fabricated stage evidence.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
