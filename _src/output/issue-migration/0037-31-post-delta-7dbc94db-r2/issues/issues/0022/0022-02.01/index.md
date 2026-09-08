---
schema_version: "1.0"
id: "0022-02.01"
level: "subtask"
parent: "0022-02"
state: "closed"
visibility: "internal"
prerequisites:
  - "0022-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2704"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0022-02.01:0022-01 Define the versioned lifecycle node and edge contracts: separate artifact nodes from verification measure and result nodes; require responsibility origin, product/project/process identity, baseline/revision/variant, status/rationale, and typed source/target roles; preserve distinct `SWE.4`, `SWE.5`, `SWE.6`, `SYS.4`, `SYS.5`, and `VAL.1` bases with canonical serialization, closed node/edge vocabularies, immutable source identity, and explicit version compatibility.

## Scope

- **Integration review:** not mandatory. **No-checkpoint justification (architect):** the mandatory `0022-01` contract checkpoint precedes it and the terminal `0022-03` checkpoint reviews schema plus validator composition; this Subtask has no external effect and no irreversible migration.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
