---
schema_version: "1.0"
id: "0019-06"
level: "task"
parent: "0019"
state: "open"
visibility: "internal"
prerequisites:
  - "0019-05"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:3009"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0019-06:0019-05 Implement S-Core-specific validation and campaign evidence reporting.

## Scope

### Campaign C — Curation, Publication, and Acceptance

## Acceptance criteria

- **AC-001** Validation checks record schema, kind/ID registry conformance, source-ref/SHA integrity, required provenance, traceability, module/component containment, dangling references, malformed Sphinx-needs identities, duplicate versions, and status consistency
- **AC-002** a persisted report provides pass/fail, totals by kind/status, structured exception-candidate counts, tool/version metadata, and actionable findings without claiming candidates are queued before `0019-07`

## Definition of Done

Negative fixtures prove every validation class fails correctly; the validation report is machine-readable and human-readable, retained with the campaign, and meets the validation-evidence conditions in `aspice-level1-score-import.md`.
