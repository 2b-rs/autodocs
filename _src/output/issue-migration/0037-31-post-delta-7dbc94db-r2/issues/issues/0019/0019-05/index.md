---
schema_version: "1.0"
id: "0019-05"
level: "task"
parent: "0019"
state: "closed"
visibility: "internal"
prerequisites:
  - "0019-04"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:3005"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0019-05:0019-04 Normalize raw S-Core extraction output into canonical versioned records.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Every emitted record conforms to `ECLIPSE/S-CORE/<kind>/<id>@rel:<release>#<content-hash8>`, carries all non-canonical provenance required by `score-identity-scheme.md`, contains source-backed traceability, has an initial status/reason and history entry, and records content hashes deterministically
- **AC-002** identity collisions and source contradictions emit deterministic structured exception candidates for `0019-07` rather than being overwritten or prematurely queued

## Definition of Done

Schema, canonical-ID, version-ID, provenance, and deterministic-content-hash tests pass; a fixture corpus demonstrates each of the four supported kinds plus collision and contradiction handling.
