---
schema_version: "1.0"
id: "0037-26.05"
level: "subtask"
parent: "0037-26"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-17"
  - "0037-19"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2452"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-26.05:0037-17, 0037-26.05:0037-19 Extend curation items, queues, decisions, and findings with the common provenance envelope.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Link stable finding, source report/evidence/version, issue/criterion/run/campaign, claim/queue transitions, curator decision/authority, applied change, invalidation/supersession, and published result without treating requester identity as approval

## Definition of Done

Lifecycle integration tests trace open→claim→decision→apply/publish and reject unauthorized, stale, duplicate, fabricated, or orphaned transitions.
