---
schema_version: "1.0"
id: "0037-16"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-04"
  - "0037-11"
  - "0037-13"
  - "0037-14"
  - "0037-15"
  - "0037-17.01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2356"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-16:0037-04, 0037-16:0037-11, 0037-16:0037-13, 0037-16:0037-14, 0037-16:0037-15, 0037-16:0037-17.01 Implement `_src/tools/issue_migration_report.py` and `provenance/_schema/issue-migration-report-v1.schema.json` as the source/target cutover gate.

## Scope

- **Integration review: mandatory.** **Rationale (architect):** The fail-closed report governs whether the source-to-target authority migration may cross cutover, so its declared cross-item reach requires a privileged integration boundary rather than Task-local review. **Authority:** `DEC-0037-004` at `183d836367617980473798fa93d8753f59cc5730`; Architect determination `9c6a886a154fa6e5cfb9792f7f66cb4db6657357`; marker-projection AWARD `agent-inbox:1787812844887-60ba633e`.

### Campaign C — Canonical Process and Regeneration Documentation

## Acceptance criteria

- **AC-001** Write retained JSON and Markdown to `provenance/migrations/issue-store/<run-id>/report.{json,md}` with source/candidate commits/artifact sets, schema/tool versions, counts and SHA-256 hashes by item/state/type, normalized semantic comparisons, LF-normalized byte comparisons for preserved text, IDs/edges/criteria/DoD/refs/claims/archives, provenance completeness, anomalies/dispositions, generated-view reconciliation, previous-run/rerun delta, and pass/fail. Finding IDs are `MIG-` plus a truncated SHA-256 of rule, source item, field, and source locator—never observed values—so they persist across reruns. Unresolved error, authority/evidence inflation, fabricated refs, source omission, stale candidate, or undispositioned warning fails
- **AC-002** reruns link prior findings and resolutions

## Definition of Done

Fixtures detect omission, byte and semantic drift separately, edge/state/authority inflation, fabricated refs, stale/self-baselined shadow, unstable finding IDs, and report tampering; reports carry producing run/issue/artifact identity and any failure blocks cutover.
