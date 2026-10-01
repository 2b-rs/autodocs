---
schema_version: "1.0"
id: "0081-02"
level: "task"
parent: "0081"
state: "blocked"
visibility: "internal"
created_at: "2026-08-25"
updated_at: "2026-08-25"
prerequisites:
  - "0081"
  - "0090-01"
origin:
  kind: "authored"
authority: "shadow"
work_type: "implementation"
relations:
  - type: "blocks"
    target: "0081-01"
---

## Goal

Blocked task with a Feature-closure misuse and a missing endpoint.

## Scope

Missing endpoints must stay visible.

## Acceptance criteria

- **AC-001** Missing endpoints are explicit.

## Definition of Done

The graph keeps the missing node.
