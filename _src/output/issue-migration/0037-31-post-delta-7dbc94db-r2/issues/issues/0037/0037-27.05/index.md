---
schema_version: "1.0"
id: "0037-27.05"
level: "subtask"
parent: "0037-27"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-17"
  - "0037-19"
  - "0037-27.01"
  - "0037-27.02"
  - "0037-27.03"
  - "0037-27.04"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2480"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-27.05:0037-17, 0037-27.05:0037-19, 0037-27.05:0037-27.01, 0037-27.05:0037-27.02, 0037-27.05:0037-27.03, 0037-27.05:0037-27.04 Extend page generation and final language-tree HTML artifact sets with common provenance.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Manifest page-model/template/AI/diagram/i18n inputs, issue/criterion/run, per-language outputs/tree digest, validation/release relation, and invalidation/regeneration cause
- **AC-002** keep manifests outside generated HTML and prevent mixed-run trees

## Definition of Done

Integration tests trace representative final HTML to every producer family, detect mixed/stale inputs, and regenerate a consistent artifact set after source change.
