---
schema_version: "1.0"
id: "0037-09.04"
level: "subtask"
parent: "0037-09"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-05"
  - "0037-09.01"
  - "0037-09.02"
  - "0037-09.03"
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2248"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-09.04:0037-05, 0037-09.04:0037-09.01, 0037-09.04:0037-09.02, 0037-09.04:0037-09.03 Implement DAG, sole-writer, freshness, generated-view, determinism, and project-validator integration. **Claim:** `TODO-Gabriel-Pike-0037-09.04-20260825T061300Z.md` (Pike provenance `agent:gabriel-pike-20260825t061300z:0037-09.04:20260825T061300Z`; current `agent:gabriel-chapel-20260825t063000z:0037-09.04:20260825T063000Z`; dispatcher gabriel). Branch `0037-09.04-20260825T061300Z` from parent `0037-09` @ `e0ed8a52b9640c20cd48f7e062f339a1c78ebf37`. **Implementation completion (2026-08-25, Gabriel-Chapel):** REF `dd1e76a0d56434349107bd010be82783053f82f4`. Takeover `7ca4f7af768517413d5dc79a38fc0a04ca958507`. Adopted Pike unstaged product. Validation: `test_issue_validate` 58/58 twice PASS; `py_compile` PASS; `git diff --check` PASS; `automation_safety --json` PASS (0 findings, no suppression). **Acceptance: ✓** (2026-08-28, Integrator `belanna`, independent of Implementers `Gabriel-Pike`/`Gabriel-Chapel`, AE-5 follow-up implementer `tuvok-0037-09-ae5`, and lander `paul`). Product REF `dd1e76a0d56434349107bd010be82783053f82f4`; first-review Review-REF `6dc2b6819` (verdict INCONCLUSIVE, AE-5 gap named); AE-5 follow-up REF `0132afaea`; delta re-verify Review-REF `53fa5ffc9` (verdict ACCEPTED, AE-5 gap closed, Chapel product confirmed byte-identical). AWARD `1787878841540-cf854e0e`. No checkpoint crossed or upward integration performed.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Detect DAG cycles, undeclared/multiple writers, missing required stages, stale/hand-edited outputs, mixed content-generation IDs, byte/semantic comparator violations, self-consuming reports, and unexplained generated files
- **AC-002** integrate all issue checks into `_src/validate.py` with explicit staged/candidate modes

## Definition of Done

Cycle/writer/staleness/determinism fixtures, repeated runs, integration tests, and mutation guards pass without modifying authoritative or generated files.
