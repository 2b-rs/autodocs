---
schema_version: "1.0"
id: "0022-02"
level: "task"
parent: "0022"
state: "closed"
visibility: "internal"
prerequisites:
  - "0022-02.01"
  - "0022-02.02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2708"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0022-02:0022-02.01, 0022-02:0022-02.02 Package-level consistency and aggregation for the lifecycle-trace contract: prove that schema, tool, and documentation vocabulary are identical; that every `0022-01` interface field maps to a node or edge or is explicitly recorded as non-graph; that legacy provenance bytes and semantics are unchanged; and record the aggregation manifest, digest list, focused test results, consumer mapping, and complete findings disposition. Child product edits only through a returned finding.

## Scope

- **Integration review:** not mandatory. **No-checkpoint justification (architect):** recorded by Architect `data` in the breakdown proposal — this parent performs consistency and aggregation only, produces no external effect and no irreversible migration, and the terminal `0022-03` checkpoint consumes this package directly.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
