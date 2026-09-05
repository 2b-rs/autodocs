---
schema_version: "1.0"
id: "0019-02"
level: "task"
parent: "0019"
state: "open"
visibility: "internal"
prerequisites:
  - "0019-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2991"
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

PREREQ: 0019-02:0019-01 Create an immutable local source snapshot and evidence inventory for the v0.6.0 BOM.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Each manifest source resolves to the declared SHA
- **AC-002** immutable source contents or a deterministic local archive/snapshot plus inventory with SHA-256 hashes are retained for every in-scope source
- **AC-003** every source artifact selected for extraction has repository, ref, commit, path, and locator evidence
- **AC-004** absent/unavailable artifacts block completion or are explicitly removed from scope with rationale in `0019-01`, never omitted silently

## Definition of Done

A clean-environment verification reconstructs the same source inventory and hashes without depending on upstream availability; the snapshot/inventory report is committed or retained in an immutable controlled store and linked from the campaign manifest.
