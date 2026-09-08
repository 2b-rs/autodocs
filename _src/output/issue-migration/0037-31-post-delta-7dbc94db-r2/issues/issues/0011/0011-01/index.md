---
schema_version: "1.0"
id: "0011-01"
level: "task"
parent: "0011"
state: "closed"
visibility: "internal"
prerequisites:
  - "0020-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2836"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0011-01:0020-01 Align the CL2 assessment purpose, organizational/product boundary, PAM version, process profile/instances, exclusions, target dates, and claim wording with the sponsor/manager and competent-assessor decisions for the concrete ECU scope; record the CL2 extension in a versioned assessment input. REF: `a22b8344267adc05d4ff47dca5056fa473a244bb` (`docs/pipeline/aspice-cl2-assessment-input.md`). No `Acceptance: ✓`.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
