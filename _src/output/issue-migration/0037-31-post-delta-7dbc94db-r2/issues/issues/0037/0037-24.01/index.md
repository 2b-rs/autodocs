---
schema_version: "1.0"
id: "0037-24.01"
level: "subtask"
parent: "0037-24"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-02"
  - "0037-23.01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2403"
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
  - id: "AC-005"
    status: "active"
  - id: "AC-006"
    status: "active"
---

## Goal

PREREQ: 0037-24.01:0037-02, 0037-24.01:0037-23.01 Extend `_src/i18n_translate.py` extraction/split/merge/status for public issue titles stored in `_src/i18n/<lang>/issues.json`.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Key by item ID with canonical English `source_locale`, SHA-256 source-title hash, translated title, translator/run metadata, and status
- **AC-002** include only `public-summary` titles
- **AC-003** invalidate on source hash change
- **AC-004** protect IDs/refs/code/placeholders
- **AC-005** require canonical language plus every target in `_src/site.json`
- **AC-006** reject duplicate/stale/wrong-item records. External human/model translation remains an authoring step, not part of hermetic regeneration

## Definition of Done

Schema, extraction/merge fixtures, split round trip, stale invalidation, all-language completeness report, and protected-token tests pass for English/German, representative LTR, and Arabic RTL.
