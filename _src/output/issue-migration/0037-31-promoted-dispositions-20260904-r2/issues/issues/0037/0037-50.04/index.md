---
schema_version: "1.0"
id: "0037-50.04"
level: "subtask"
parent: "0037-50"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2194"
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

Couple queue and singleton admission paths to the automatic failover state machine. REF: `f3522aaaa80d851f3ba28744b08956a52eb63275`.

## Scope

- **DEC-0037-002 disposition:** Superseded; no dual-admission failover state machine is activated.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** Architect `data`, proposal `164890ec3c`: the qualifying cross-item gate mutation is pre-authorized by `DEC-0037-001` and remains undeployed on its item branch; `.05` immediately integrates and reviews the complete boundary.

## Acceptance criteria

- **AC-001** Add `_src/tools/runner_protocol_health.py`
- **AC-002** wire the shared live-selector/readiness check into the retirement guard, dispatcher CLI, and immediately-before-lease CAS boundary
- **AC-003** remove caller-controlled epoch defaults
- **AC-004** enforce one rollback coordinator, zero post-failure leases, active-claim drain, structured rejection codes, no `pgrep` health predicate, no grandfathering, and fail-closed behavior for indeterminate state. Update exact focused tests, `runner-host/MANIFEST.json`, and `issues/_policy/runner-service.json` within Datas bounded path set

## Definition of Done

Combined guard, rollback, health, and dispatcher tests cover selector races, two workers racing rollback, timeout, sentinel, restored legacy, malformed selector, collision, and full `run-loop.sh --once` wiring; shell syntax, manifest digests, automation-safety, no-mutation canaries, and `git diff --check` pass; no live deployment or checkpoint crossing occurs.
