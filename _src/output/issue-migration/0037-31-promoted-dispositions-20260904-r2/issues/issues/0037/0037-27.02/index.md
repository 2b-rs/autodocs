---
schema_version: "1.0"
id: "0037-27.02"
level: "subtask"
parent: "0037-27"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-17"
  - "0037-19"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2468"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-27.02:0037-17, 0037-27.02:0037-19 Extend diagram source and rendered SVG workflows with manifests and common provenance.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Record source model/labels/theme/tool/config, issue/criterion/run, rendered artifact digest, language, invalidation/regeneration relation, and source-to-SVG members
- **AC-002** do not inject uncontrolled provenance into SVG markup

## Definition of Done

Source/label/theme changes mark exact SVGs stale, regeneration links replacements, and queries trace canonical and translated diagrams bidirectionally.
