---
schema_version: "1.0"
id: "0037-19"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-05"
  - "0037-11"
  - "0037-12"
  - "0037-16"
  - "0037-17"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2367"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-19:0037-05, 0037-19:0037-11, 0037-19:0037-12, 0037-19:0037-16, 0037-19:0037-17 Write the implemented canonical regeneration process in `docs/pipeline/issue-derived-artifacts.md`.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Document authoritative inputs, exact `docs/pipeline/issue-derived-artifacts-v1.json` stage order/commands, sole writers, committed/ephemeral outputs, clean/staged policy, run/issue/campaign identity, staging/atomic promotion, manifests/hashes, public projection, i18n consumption (not external translation authoring), graph DOT/SVG/embed, HTML trees, validation/retained reports, byte versus semantic determinism, stale/missing failure, rollback, and the controlled procedure for adding a stage. Prevent the current “latest report by mtime” behavior from combining unrelated runs

## Definition of Done

One operator recipe regenerates and validates every declared issue-derived artifact from a clean checkout; documentation, executable DAG, tool help, and drift tests agree exactly.
