---
schema_version: "1.0"
id: "0037-18"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-01"
  - "0037-03"
  - "0037-10"
  - "0037-42"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2363"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0037-18:0037-01, 0037-18:0037-03, 0037-18:0037-10, 0037-18:0037-42 Write the implemented canonical collaboration process in `docs/pipeline/issue-lifecycle.md`.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Define creation/decomposition, prerequisites, `AC-NNN`, claims/leases/write scopes, cross-clone limitations, handoff, decisions/signatures/authority, findings, criterion evidence, closure/wontfix/supersession/not-accepted archive, provenance/privacy links, conflict recovery, autonomous intent-preserving backlog repair, parent-package aggregation/closure, semantic-deadlock correction, `[u]` boundaries, append-only collaboration/tooling suggestions, and separation from curation/problem/change lifecycles. Treat `SANDBOX.md`, `AGENTS.md`, `PRIVILEGED.md`, and `agent-workflow.json` as the tested bootstrap bundle
- **AC-002** update them, TODO/DONE headers, and other contradictory instructions only in the controlled cutover path
- **AC-003** until then label future-state sections clearly

## Definition of Done

Normative role/action/tool tables, examples, failure/recovery recipes, and conformance checklist match implemented schemas/commands/transitions; links and example commands validate.
