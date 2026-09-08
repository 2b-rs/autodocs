---
schema_version: "1.0"
id: "0037-27.04"
level: "subtask"
parent: "0037-27"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-17"
  - "0037-19"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2476"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-27.04:0037-17, 0037-27.04:0037-19 Extend i18n segment/title/diagram registers and translation runs with common provenance.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Record source ID/hash/locale, protected tokens, target locale, translator/model/policy/config, issue/criterion/run, merge decision, output digest, stale/invalidation relation, and fallback
- **AC-002** preserve human-authored translations as authoritative inputs to deterministic builds

## Definition of Done

Tests trace translated prose/title/diagram labels to exact source and translation run, reject protected-token/source-hash mismatch, and report stale/missing language work.
