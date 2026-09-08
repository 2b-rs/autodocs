---
schema_version: "1.0"
id: "0037-50.03"
level: "subtask"
parent: "0037-50"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2188"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

Implement the digest-bound rollback bundle and coordinated executor. REF: `f3522aaaa80d851f3ba28744b08956a52eb63275`.

## Scope

- **DEC-0037-002 disposition:** Superseded. William released the implementation claim at `0d9d1d6fcef9adfc0b853c6561577fca1980ab06`; preserved evidence tip `dd592742db09bf073cbd5f5bb491d7493cdb76c9`.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** Architect `data`, proposal `164890ec3c`: the executor remains dormant until `.04`; external and integrated effects are reserved for `.05`.

## Acceptance criteria

- **AC-001** Add `issues/_policy/runner-protocol-rollback-v1.json` and its schema
- **AC-002** extend `_src/tools/runner_protocol_rollback.py` and its tests with exclusive rollback markers, active-claim drain, corrected service-first/selector-last restore, verified events, and durable blocked state for digest, write, verify, lock, timeout, or event failures. Preserve or explicitly migrate `--prove` compatibility

## Definition of Done

Schema validation, the full rollback failure matrix, focused unit tests, automation-safety, and `git diff --check` pass; target bytes are pinned to the corrected `46fdd6398` lineage; the executor has no live admission call site or deployment in this package.
