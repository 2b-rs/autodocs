---
schema_version: "1.0"
id: "0037-26.02"
level: "subtask"
parent: "0037-26"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-17"
  - "0037-19"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2440"
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

PREREQ: 0037-26.02:0037-17, 0037-26.02:0037-19 Extend `_src/spec/campaigns/*.json` writers with immutable campaign snapshots and content manifests.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Adapt `campaign-manifest@v1` without rewriting history
- **AC-002** replace listing/mtime `corpus_hash` as evidence identity with a sorted content artifact set while retaining it only as a staleness hint
- **AC-003** link trigger issue/criterion, runs, queue snapshot, decisions, published reports, source/tool/config commits, and scope

## Definition of Done

Migration and producer tests prove old manifests receive explicit legacy disposition, new snapshots are immutable/queryable, content changes alter identity, and mtime-only changes do not.
