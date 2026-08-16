---
id: "0099-01"
level: "task"
parent: "0099"
state: "open"
visibility: "internal"
---

## Goal

Sample Task, invalid case.

## Scope

Covers illegal renumbering: a later edit changed AC-002 to AC-001 after AC-001 was deleted
(rather than tombstoning AC-001 and leaving AC-002's ID untouched).

## Acceptance criteria

- **AC-001** What was originally AC-002, incorrectly renumbered down to fill a gap left by
  a deleted AC-001 with no tombstone.

## Definition of Done

N/A (fixture is intentionally invalid; the history/diff shows the renumbering, which a
deterministic parser/validator must reject given the prior committed state as context).

<!-- expected: HARD REJECT when validated against prior committed state —
     AC-NNN IDs never change once allocated, per issue-store.md §11.4 -->
