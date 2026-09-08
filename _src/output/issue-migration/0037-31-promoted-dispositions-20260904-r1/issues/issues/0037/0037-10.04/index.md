---
schema_version: "1.0"
id: "0037-10.04"
level: "subtask"
parent: "0037-10"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-09"
  - "0037-17.03"
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2293"
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
---

## Goal

PREREQ: 0037-10.04:0037-09, 0037-10.04:0037-17.03 Implement `issuectl validate`, view rendering, graph, list, and trace query command surfaces. **Claim:** `TODO-Gabriel-Burnham-0037-10.04-20260825T092000Z.md` (`agent:gabriel-burnham-20260825t092000z:0037-10.04:20260825T092000Z`). Predecessor claim `TODO-Gabriel-Nhan-0037-10.04-20260825T091000Z.md` (token not reused). **REF:** `7382aea9215de3e5ba60e744993078c8f2efda3c`. **Validation:** `/tmp/autodocs-0037-08-venv-julian/bin/python _src/tests/test_issuectl.py` — 10 tests OK; `py_compile` PASS.

## Scope

- **Requirements covered (reciprocal downstream binding):** CLI exposure of `RQ-TRACE-02`, `RQ-TRACE-03`, and `RQ-TRACE-04` at file and commit level under `DEC-0040-004`.

## Acceptance criteria

- **AC-001** Commands call shared libraries rather than duplicate semantics, are registered as typed runner actions for sandboxed agents, and select authoritative/candidate/staged roots explicitly
- **AC-002** support deterministic JSON and human output
- **AC-003** expose open/blocked/unclear/owner/prerequisite/trace queries
- **AC-004** fail visibly on stale indexes/views
- **AC-005** and never parse a derived legacy view as authority. The trace command exposes the file/commit forward and reverse queries and structured missing, dangling, unresolvable, and redacted results defined by `0037-17.03`, in deterministic JSON and concise human output. It delegates graph traversal and diagnostic semantics to the shared libraries and does not implement a second trace model. The trace surface is read-only and does not create a new project-wide blocking gate

## Definition of Done

Command-contract tests cover help, exit codes, filters, malformed/stale data, privacy, staged candidates, and equivalence with library results. Command-contract tests cover file and commit queries in both directions, broken and missing ends, a renamed file, deterministic output and exit behavior, and exact semantic equivalence with the `0037-17.03` library results.
