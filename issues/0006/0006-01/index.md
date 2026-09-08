---
schema_version: "1.0"
id: "0006-01"
level: "task"
parent: "0006"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:124"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

From the curator's and user's perspective, review, feedback, and curation should not split into separate silos based on technical origin (scrape ambiguity vs. DB correction vs. AI amendment vs. AI-proposed new element). There should be one coherent, traceable lifecycle for "an item that needs human judgment", with stable identity across projects, full history, visible status, and both static and future dynamic presentation layers. -- DONE 2026-08-14: Implemented unified curation lifecycle (0006-02..0006-25), unified curation-item@v1 schema, canonical identity, versioning, dependency tracking, delta views, and HTML status/history rendering across all specification records.

## Scope

### Architecture decisions to make visible in code/data

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
