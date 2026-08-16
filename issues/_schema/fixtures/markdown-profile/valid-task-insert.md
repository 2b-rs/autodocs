---
id: "0099-01"
level: "task"
parent: "0099"
state: "open"
visibility: "internal"
---

## Goal

Sample Task used only as a Markdown-profile fixture.

## Scope

Covers the insert operation for AC-NNN allocation.

## Acceptance criteria

- **AC-001** First criterion, allocated at creation time.
- **AC-002** Second criterion, inserted after AC-001 already existed (append-only: next ID
  is max+1, not reused).

## Definition of Done

Both criteria are verifiable independently.

<!-- expected normalized result: criteria = [AC-001 (active), AC-002 (active)] -->
