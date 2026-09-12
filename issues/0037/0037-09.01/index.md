---
schema_version: "1.0"
id: "0037-09.01"
level: "subtask"
parent: "0037-09"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-02"
  - "0037-08"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2232"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-09.01:0037-02, 0037-09.01:0037-08 Implement structural, schema, path, criterion, prerequisite, and dependency-graph validation. **Claim:** `TODO-julian-0037-09.01-20260824T171000Z.md` (`agent:julian:0037-09.01:20260824T171000Z`). **REF:** `7b36370e84c5c793e705a1d418e2b5db2b7cc965`. **Acceptance: ✓** (2026-08-28, Integrator `paul`, unabhängig von Implementierer `Julian` / `agent:julian:0037-09.01:20260824T171000Z`). Abgenommene Baseline `7b36370e84c5c793e705a1d418e2b5db2b7cc965`; Review-REF `9f12aba9ba382c2c2c5b596dfc06aa6b761fd137`; evidence `debf8e26c41897453366330dd1032cdde2bdba7b`; C land `6b4f8bab94042246ca2a352210f0bda43bba9017` is not the review; AWARD `1787872639856-13be7faa`. No checkpoint crossed or upward integration performed.

## Scope

- **Implementation evidence (2026-08-24, Julian):** The side-effect-free validator, deterministic negative fixtures, fixed-seed graph checks, resource limits, and staged-index/working-tree coverage are committed at the REF above. Post-commit validation passed: `test_issue_validate` 8/8, carried `test_issue_store` 10/10, `py_compile`, automation-safety (zero findings), and `git diff --check`.

## Acceptance criteria

- **AC-001** Detect unknown/duplicate/malformed IDs and criteria, reused tombstones, parent/prefix/path mismatch, invalid fields/Markdown, cycles/self-dependencies, missing endpoints, and Feature-closure versus start-gate misuse
- **AC-002** diagnostics name item/path/line/field/rule and use stable exit codes

## Definition of Done

One negative fixture per rule plus fixed property/fuzz seeds and resource limits pass deterministically for working-tree and staged-index inputs.
