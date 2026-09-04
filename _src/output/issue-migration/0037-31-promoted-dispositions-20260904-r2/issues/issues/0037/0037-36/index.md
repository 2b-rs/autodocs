---
schema_version: "1.0"
id: "0037-36"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-34"
  - "0037-35"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2544"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-36:0037-34, 0037-36:0037-35 Conduct an independent signed post-cutover audit and authorize closure only if authority, views, provenance, claims, and generated trees remain consistent.

## Scope

- **Rescoping pending (`0037-49`, `DEC-0044-014`):** This Task's role/signer requirements below still name distributed roles. When this Task is next worked, rescope them to the single repository-owner authority per `0037-49`'s single-authority model before implementing against them.

## Acceptance criteria

- **AC-001** A sandboxed audit agent submits the exact post-cutover runner profile from `issues/_policy/audit-profiles.json`, including every mandatory grunt-runner/capability/instruction-bootstrap/authority/view/graph/privacy/link/i18n check, fresh/stale-agent fixtures, fixed high-risk trace, deterministic seeded strata, and claim/item-write freeze assertion. A registered independent quality signer reviews the retained results, verifies approval/candidate/cutover/reference/clean-run/rollback lineage, and routes any threshold failure through actual rollback rather than accepting drift

## Definition of Done

SSH-signed audit addendum and command/sample manifest meet every profile threshold, pass signer/role validation, link final authority state/reports/residual limitations/support/rollback obligations/exact commits/artifact sets, and append authorization for the exact `0037-40` activation delta to the transaction ref. This Task remains `[p]` until `0037-40` materializes its closure; it alone authorizes that activation.
