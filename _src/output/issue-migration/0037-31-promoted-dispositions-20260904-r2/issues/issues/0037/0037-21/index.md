---
schema_version: "1.0"
id: "0037-21"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-10"
  - "0037-11"
  - "0037-12"
  - "0037-17"
  - "0037-18"
  - "0037-19"
  - "0037-42"
  - "0037-51"
  - "0038-16.01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2375"
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
---

## Goal

PREREQ: 0037-21:0037-10, 0037-21:0037-11, 0037-21:0037-12, 0037-21:0037-17, 0037-21:0037-18, 0037-21:0037-19, 0037-21:0038-16.01, 0037-21:0037-42, 0037-21:0037-51 Update `SANDBOX.md`, `AGENTS.md`, `PRIVILEGED.md`, `agent-workflow.json`, `docs/pipeline/agent-workflow.md`, `docs/pipeline/tools.md`, `docs/pipeline/reports.md`, `docs/pipeline/README.md`, and maintainer guidance for issue/provenance operations.

## Scope

- **DEC-0037-002 execution model:** Specify direct foreground execution plus a Dispatcher-selected Runner role for Task-ID-bound long jobs, including job control, progress, cancellation, recovery, and agent interfaces. Consumers must use the accepted contract before starting.
  - **Integration review: mandatory.** **Rationale (architect):** this contract governs execution and authority across all future issue-store work.

### Campaign D — Graph, Website, i18n, Pipeline Provenance, and Tree Integration

## Acceptance criteria

- **AC-001** Document exact privileged-versus-sandboxed capabilities, runner request/action IDs, inputs/outputs, authority/signature/claim requirements, side effects, dry-run/candidate/staged behavior, stable errors, report/provenance locations, privacy limits, clean-checkout prerequisites, and recovery/rollback
- **AC-002** make pre/post-cutover applicability explicit and remove or mark historical all direct-edit, `TODO-<agent-id>.md`, user-operated `run.sh`, obsolete tool prohibition, free-form TODO-parser, mtime-only report selection, and dual-authority instructions
- **AC-003** preserve the policy-semantic continuity matrix from `0037-41`, translating legacy-file operations into issue-store-native commands/records without dropping owned-work resumption, parent closure, autonomous repair, human-decision boundaries, suggestion/tooling capture, one-use request semantics, or the prohibition on runner escalation
- **AC-004** every agent-facing entry point gives the same capability detection, runner-backed first-read/doctor/request/recovery sequence and the same legacy-frozen transaction-operator exception

## Definition of Done

Catalog links resolve, examples execute against fixtures, generated help is checked where applicable, and documentation validation reports no contradictory active instruction.
