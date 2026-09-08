---
schema_version: "1.0"
id: "0037-35.01"
level: "subtask"
parent: "0037-35"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-34.02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2536"
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

PREREQ: 0037-35.01:0037-34.02 Rebuild every derived issue view, graph, i18n artifact, page model, language tree, index, and validation artifact from a clean checkout of the mandatory post-cutover reference integration commit.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Install only locked/tracked dependencies and approved system-tool versions
- **AC-002** use a fresh sandboxed-agent fixture to read bootstrap state and submit the qualified runner request before the documented DAG
- **AC-003** compare instruction/source/catalog/view/public/tree/artifact counts and hashes
- **AC-004** prove a fresh agent discovers only `issues/`, every legacy cached instruction/command is rejected actionably, and there is no source mutation, fixture leakage, absent stage, network-only dependency, fallback translation, mixed run, or unexplained diff

## Definition of Done

Retained clean-run report exits zero, a second run satisfies declared byte/semantic determinism, and all output artifact sets link to the exact post-reference integration HEAD and cutover; signed completion evidence is appended to the transaction ref without writing issue state.
