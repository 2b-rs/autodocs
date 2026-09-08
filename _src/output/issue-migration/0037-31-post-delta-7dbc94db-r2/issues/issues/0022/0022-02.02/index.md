---
schema_version: "1.0"
id: "0022-02.02"
level: "subtask"
parent: "0022-02"
state: "closed"
visibility: "internal"
prerequisites:
  - "0022-02.01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2706"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0022-02.02:0022-02.01 Implement the lifecycle-trace validator over **explicit candidate roots only**: report stable findings for wrong verification basis, orphan, stale baseline, cross-variant edge, responsibility mismatch, illegal status, and non-ECU evidence substitution, with deterministic output and exit codes, bounded input, and fail-closed handling of malformed input. It must not register `_src/validate.py` or any other default shared gate, must not rewrite evidence, and grants no ECU-process credit from tool execution.

## Scope

- **Integration review:** not mandatory. **No-checkpoint justification (architect):** it is candidate-root-only and not a default shared gate; terminal `0022-03` reviews the composed behavior before Feature integration. Any proposal to register it broadly is a new TK-2 decision (`DEC-0022-001` `CON-02`).

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
