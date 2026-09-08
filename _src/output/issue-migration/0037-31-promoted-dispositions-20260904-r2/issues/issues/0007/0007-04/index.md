---
schema_version: "1.0"
id: "0007-04"
level: "task"
parent: "0007"
state: "open"
visibility: "internal"
prerequisites:
  - "0007-03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:3076"
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

PREREQ: 0007-04:0007-03 Freeze and enforce the independently approved benchmark as the extraction regression oracle.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** The frozen artifact has a stable ID/content hash and cannot be silently regenerated over reviewed expectations
- **AC-002** a deterministic clean run compares all 200 benchmark entries/cases and reports semantic field/heading/page/completeness drift
- **AC-003** negative tests prove changed, missing, duplicate, or unresolved entries fail

## Definition of Done

The draft status/path is retired or clearly superseded, the automated benchmark gate and operator documentation are committed, and a retained passing report identifies the exact source/tool/benchmark versions.
