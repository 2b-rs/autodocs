---
schema_version: "1.0"
id: "0021-02"
level: "task"
parent: "0021"
state: "open"
visibility: "internal"
prerequisites:
  - "0021-01"
labels:
  - "legacy-terminal-unverified"
  - "archived-not-accepted"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:324"
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

PREREQ: 0021-02:0021-01 Specify the versioned browser request-package schema and deterministic request identity for a re-curation flag. REF: 3cfdbe72

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Schema includes request ID/version, target canonical and version ID, content/text hash, source URL/locator, status snapshot, actor claim, authoritative transport-derived identity/trust metadata, category, rationale, optional field/evidence references, timestamps, and client/schema version
- **AC-002** downloaded JSON is always self-declared until a trusted ingestion envelope proves otherwise
- **AC-003** duplicate identity, canonical serialization, stale-hash, sensitive-field, and retention rules are unambiguous

## Definition of Done

JSON Schema or equivalent validator, valid/invalid examples, and deterministic-ID fixtures are committed; the same semantic package supports GitHub-Issue submission and JSON export/later transfer without conflating their lifecycle states.
