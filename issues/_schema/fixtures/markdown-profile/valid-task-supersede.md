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

Covers supersession: intent/verification changed, old ID tombstoned, new ID created.

## Acceptance criteria

- **AC-001** ~~The parser rejects overlong lines.~~ (superseded by AC-002, 2026-08-16:
  verification method changed from hard rejection to a warning)
- **AC-002** The parser emits a line-length warning instead of rejecting. (supersedes:
  AC-001)

## Definition of Done

AC-001 is a tombstone pointing forward; AC-002 is active and points back via `supersedes`.

<!-- expected normalized result: criteria = [AC-001 (tombstone, superseded_by=AC-002),
     AC-002 (active, supersedes=AC-001)] -->
