---
schema_version: "1.0"
id: "0099-01"
level: "task"
parent: "0099"
state: "open"
visibility: "internal"
created_at: "2026-08-24"
updated_at: "2026-08-24"
prerequisites:
  - "0098-01"
labels:
  - "parser"
work_type: "implementation"
origin:
  kind: "authored"
authority: "shadow"
limits:
  max_criterion_bytes: 4096
---

## Goal

Parse Unicode issue content deterministically: café and Καλημέρα.

## Scope

Canonical task parsing only; generated views are excluded.

## Acceptance criteria

- **AC-001** Preserve Unicode text and exact source locators.
- **AC-002** ~~An obsolete criterion.~~ (withdrawn, 2026-08-24: replaced by scope)

## Definition of Done

The normalized JSON is byte-stable.
