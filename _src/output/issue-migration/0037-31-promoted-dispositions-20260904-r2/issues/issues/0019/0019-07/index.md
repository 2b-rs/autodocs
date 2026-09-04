---
schema_version: "1.0"
id: "0019-07"
level: "task"
parent: "0019"
state: "open"
visibility: "internal"
prerequisites:
  - "0019-05"
  - "0019-06"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:3015"
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

PREREQ: 0019-07:0019-05, 0019-07:0019-06 Integrate validated S-Core exception candidates with the unified review and curation lifecycle.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Unsupported, ambiguous, conflicting, missing-provenance, and non-auto-verifiable S-Core records create canonical `curation-item@v1` or review items with source/version evidence
- **AC-002** queue states and allowed actors follow `workflow-lifecycle.md` and `roles.md`
- **AC-003** user-facing reports link from each queue item to its record/version/source locator

## Definition of Done

End-to-end tests demonstrate both `discovered → queued → claimed → proposed → accepted → applied → published` and `discovered → queued → claimed → proposed → rejected → retained/closed without application or publication` for S-Core samples; no tool or AI path can silently perform an `accepted`/`rejected` content decision.
