---
schema_version: "1.0"
id: "0037-35.02"
level: "subtask"
parent: "0037-35"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-34.02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2540"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-35.02:0037-34.02 Rehearse rollback and post-cutover event preservation from the mandatory post-cutover reference integration commit in an isolated temporary ref/worktree.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Execute every rollback case in the fixed audit profile using development-test provenance/control events only (authoritative issue writes remain frozen), prove the prepared inverse patch applies to the exact post-reference HEAD and every permitted transaction-ref-only frozen successor, apply it, restore the matching legacy `SANDBOX.md`/`AGENTS.md`/`PRIVILEGED.md`/`agent-workflow.json` authority epoch and instructions, prove issue-store-cached commands are rejected with legacy recovery guidance, export/replay compatible provenance events without duplication/loss, validate exactly one authority, then discard the temporary ref. Do not move the real integration branch, erase immutable events, or claim rollback for an untested path

## Definition of Done

Retained rollback report and before/after artifact sets prove authority restoration, event preservation/exactly-once replay, cleanup, and deterministic recovery; injected conflict/failure cases stop safely; signed completion evidence is appended to the transaction ref without writing issue state.
