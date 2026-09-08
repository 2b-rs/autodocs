---
schema_version: "1.0"
id: "0038-16.02"
level: "subtask"
parent: "0038-16"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1938"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
---

## Goal

Execute post-activation rollout, reconcile legacy drift, and verify retirement. REF: `f3522aaaa80d851f3ba28744b08956a52eb63275`.

## Scope

- **DEC-0037-002 disposition:** Superseded; no future queue activation or singleton-retirement rollout is performed. History remains evidence only.

## Acceptance criteria

- **AC-001** Reconcile current marker/claim/REF/bootstrap/artifact findings without appropriating owners
- **AC-002** verify the activated queue implements the handoff manifest and rejects legacy mutation while preserving evidence/recovery access
- **AC-003** update legacy bridge/tool catalogs and prepare the exact canonical-guidance delta consumed by `0037-21`
- **AC-004** and prove docs/catalogs identify one active mechanism

## Definition of Done

Historical failure fixtures and two concurrent disjoint sandboxed-agent requests pass through the active queue; legacy `run.sh` accepts no mutation; stale clients receive one actionable bootstrap diagnostic; all retained bridge artifacts have an owner and retirement disposition; and before/after safety, duration, retry, context, and evidence-volume measurements are committed.
