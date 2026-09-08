---
schema_version: "1.0"
id: "0009-05"
level: "task"
parent: "0009"
state: "open"
visibility: "internal"
prerequisites:
  - "0009-02"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:291"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0009-05:0009-02 — map S-Core source artifacts (README/design docs, interface headers, component manifests) onto the unified curation-item schema from **0006-03** so S-Core units can enter the same review/curation queues as AUTOSAR records -- DONE 2026-08-14: added `from_score_record()` in `_src/tools/curation_item.py` mapping scraped S-Core units directly into `curation-item@v1` queue items. REF: pending commit

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
