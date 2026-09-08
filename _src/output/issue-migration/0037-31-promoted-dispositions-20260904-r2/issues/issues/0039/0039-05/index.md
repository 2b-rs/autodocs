---
schema_version: "1.0"
id: "0039-05"
level: "task"
parent: "0039"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-42"
  - "0037-51"
  - "0038-05"
  - "0038-10"
  - "0039-04"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1569"
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

PREREQ: 0039-05:0039-04, 0039-05:0038-05, 0039-05:0038-10, 0039-05:0037-42, 0039-05:0037-51 Implement and migrate machine-enforced Task/Feature acceptance across the legacy queue and future issue-store lifecycle. **MANAGEMENTENTSCHEIDUNG (2026-08-23, historisch):** Die damalige Zurueckstellung bis zur Queue-Nachbesserung ist durch `DEC-0037-002` ueberholt; der Task ist nach Abschluss von `0037-51` und seinen uebrigen Voraussetzungen wieder startfaehig.

## Scope

- **Reservation gate:** The sole next action after all prerequisites are terminal is a current-user decision naming an explicitly privileged owning session; until then no claim, schema/tool mutation, acceptance promotion, or cutover change is authorized.

## Acceptance criteria

- **AC-001** Extend the existing structural editor/transaction/result path rather than creating a second writer
- **AC-002** add exact acceptance assignment, package, decision, current-state, invalidation, prerequisite-closure, Feature aggregate, signer/authority, and audit contracts
- **AC-003** update the legacy doctor/editor/coordinator, automation policy, tests, issue-item/closure/acceptance schemas, migration/cutover mapping, queue actions, bootstrap/instruction profiles, generated views, and positive/negative/unauthorized fixtures. Preserve `[x]`/`[w]` dispositions, historical `DONE.md`, rejected/inconclusive attempts, unrelated work, and foreign claims
- **AC-004** reject grunt-authored or self-authorized acceptance and any Feature move lacking complete current acceptance

## Definition of Done

A clean legacy and shadow/future profile agree on exact semantics; accepted, rejected, inconclusive, invalidated, changed-prerequisite, wontfix, parent, Feature aggregate, unauthorized-grunt, stale-baseline, concurrent-review, rollback, migration, and historical fixtures pass. The current Feature `0037` review package is refreshed before approval/cutover, one authoritative writer/action path exists, and no unavailable privileged executor is hidden inside grunt implementation Tasks.
