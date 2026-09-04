---
schema_version: "1.0"
id: "0037-34.01"
level: "subtask"
parent: "0037-34"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-20"
  - "0037-21"
  - "0037-31"
  - "0037-42"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2517"
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
  - id: "AC-007"
    status: "active"
---

## Goal

PREREQ: 0037-34.01:0037-20, 0037-34.01:0037-21, 0037-34.01:0037-31, 0037-34.01:0037-42 Prepare the exact authority-switch patch and rollback package without applying it.

## Scope

- **DEC-0037-002 execution model:** The prepared bundle pins the accepted direct-execution role/capability/job-control contract before cutover.

## Acceptance criteria

- **AC-001** In a detached temporary worktree, derive the final authority tree from the unchanged candidate plus the schema-validated transaction-ledger closure delta for `0037-31` and `0037-34.01`
- **AC-002** mark `TODO.md`/`DONE.md` generated
- **AC-003** activate issue validation/regeneration while claims remain frozen
- **AC-004** atomically switch `SANDBOX.md`, `AGENTS.md`, `PRIVILEGED.md`, and `agent-workflow.json` to one new contract version, authority epoch, `issue-store-frozen` capability phase, and qualified grunt-runner protocol/action-registry version and update process/tool entry points
- **AC-005** remove obsolete legacy parser/owner/dual-write paths
- **AC-006** fill every knowable migration-record field
- **AC-007** and generate inverse rollback plus post-cutover event export/replay commands. Record the unchanged integration control-base commit/tree, patch SHA-256, candidate/artifact-set digests, expected file list/modes, instruction-bundle digests/epoch, fresh/stale-agent validation results, approval-ref topology, and the exact post-cutover closure/reference operations excluded from the patch. Do not modify the integration branch or authority

## Definition of Done

Prepared patch/final-authority-tree and rollback artifact sets reproduce byte-for-byte in a clean worktree, validate, differ from the candidate only by the declared closure/authority delta, and are ready for independent audit by `0037-32`.
