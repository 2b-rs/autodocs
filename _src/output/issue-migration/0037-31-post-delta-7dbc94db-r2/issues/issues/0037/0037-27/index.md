---
schema_version: "1.0"
id: "0037-27"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-27.01"
  - "0037-27.02"
  - "0037-27.03"
  - "0037-27.04"
  - "0037-27.05"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2460"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-27:0037-27.01, 0037-27:0037-27.02, 0037-27:0037-27.03, 0037-27:0037-27.04, 0037-27:0037-27.05 Complete provenance integration for AI claims, diagrams, guides, i18n, page composition, and HTML artifacts.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Each artifact family and call site from the exact inventory approved by `0037-37` records inputs/invalidation/regeneration causes under the shared envelope
- **AC-002** each Subtask changes only its enumerated family and generated-file metadata stays in manifests, not uncontrolled HTML/SVG injection

## Definition of Done

All five Subtasks support forward/reverse trace from language-specific HTML to exact issue, trigger, source versions, and producer run.
