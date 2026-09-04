---
schema_version: "1.0"
id: "0017-02"
level: "task"
parent: "0017"
state: "closed"
visibility: "internal"
prerequisites:
  - "0017-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2942"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0017-02:0017-01 Establish a maintained risk register for source drift, normative misinterpretation, provenance loss, data quality, nondeterminism, security/privacy/license exposure, AI/external services, resource/competency gaps, verification/validation, and publication; assign owners, treatments, dates, residual risk, and links to plans/changes. Claim: `TODO-benjamin-0017-02-20260829.md`. REF: `docs/pipeline/man5-risk-register.md` (`REG-RSK-20260829-01`). No `Acceptance: ✓`.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
