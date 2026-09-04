---
schema_version: "1.0"
id: "0020-01"
level: "task"
parent: "0020"
state: "open"
visibility: "internal"
prerequisites:
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2632"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Approve the first assessed ECU product/variant and supplied-product boundary, organizational unit, customer/intended use, lifecycle stage, project/release or increment, assessment purpose/timing, target profile, and permitted claim wording; identify whether the unit owns a complete ECU system lifecycle or receives allocated software requirements. The automotive ECU domain is confirmed, but these concrete scope decisions still require sponsor/manager and competent-assessor agreement. Claim: `TODO-michael-0020-01-20260825T183100Z.md`; owner_token: `agent:michael:0020-01:20260825T183100Z`. REF: `b56f44ef75f3a1afce2b101484ec75eb7e9e133a` (`DEC-0020-001`, `docs/dossiers/dec-0020-01-ecu-scope.md`). **Management decision (2026-08-25 18:26 +02, current user, Michael Cursor session), verbatim:** „Wir entwickeln ausschließlich System- und Applikationssoftware für ein virtualisiertes Automotive-Steuergerät. Der Kernel befindet sich noch in Entwicklung und wird später hinzugefügt.“ Follow-up 18:31 +02: „gut, los geht's.“ Recorded by Project Lead `michael`. The unit does not own a complete ECU system lifecycle in this increment; kernel is excluded until a later Management decision. **Prior VERTAGT (2026-08-22, Management, recorded by `kathryn`)** is superseded by that authorization, not deleted. No `Acceptance: ✓`. No Feature `0020` `DONE.md` move.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
