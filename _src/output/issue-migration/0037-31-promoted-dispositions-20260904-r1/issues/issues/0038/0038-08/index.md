---
schema_version: "1.0"
id: "0038-08"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-01"
  - "0038-04"
  - "0038-09"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1699"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0038-08:0038-01, 0038-08:0038-04, 0038-08:0038-09 Implement Task validation profiles with coverage canaries and aggregate verdicts. REF: `fb78fde07`.

## Scope

- **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0038-08-Commit)`). Abgenommene Baseline `fb78fde07`; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. 10/10 eigene Tests am eigenen REF.
  - **Completion evidence (2026-08-17):** Added `task-validation-profile@v1` and `task-validation-report@v1` schemas, deterministic evaluator, seven named fixtures, and operator documentation in `fb78fde07`; focused Task-validation plus environment-doctor regression suite passed 33 tests; compilation and both schema JSON parses passed; automation-safety scan returned `verdict: PASS` with zero findings/policy errors.

## Acceptance criteria

- **AC-001** Profiles declare required stages, exact inputs/outputs, freshness/run identity, expected counts/invariants, allowed mutations, time/resources, structured findings, and known-bad canaries proving each detector ran. Required failure, missing stage, mixed/stale runs, baseline-only checks, unexpected zero coverage, or error findings fail even when child processes exit zero
- **AC-002** statuses are PASS/FAIL/SKIP/INCONCLUSIVE, never ambiguous success

## Definition of Done

Fixtures cover the four-URL probe, baseline-only determinism PASS, stale i18n register reporting zero open work, mtime-mixed reports, and Feature `0021`-style synthetic-only green validation; project profiles produce one bounded aggregate verdict.
