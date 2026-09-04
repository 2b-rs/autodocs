---
schema_version: "1.0"
id: "0037-25.03"
level: "subtask"
parent: "0037-25"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-25.02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2428"
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

PREREQ: 0037-25.03:0037-25.02 Implement freshness, byte/semantic determinism, manifest, and unexplained-diff validation.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Recompute source/schema/tool/config/artifact digests
- **AC-002** apply each stage's declared byte or semantic comparator
- **AC-003** fail on missing/stale/hand-edited output, fallback translation, undeclared file, differing repeated clean run, or unexplained working-tree change
- **AC-004** retain run/stage reports externally rather than injecting a report into the candidate it validates

## Definition of Done

Two clean full-tree runs satisfy declared determinism and mutation guards; negative fixtures catch stale/missing stages, semantic-only normalization, byte drift, undeclared files, and self-referential report cycles.
