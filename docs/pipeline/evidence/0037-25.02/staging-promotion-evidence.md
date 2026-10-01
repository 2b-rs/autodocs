# Subtask 0037-25.02: Run-Scoped Staging and Realizable Immutable-Tree Promotion Evidence

## Overview

Subtask `0037-25.02` establishes and validates run-scoped staging and realizable immutable-tree promotion within the DAG orchestrator (`_src/tools/issue_regenerate.py`).

## Criteria Verification

- **AC-001 (Run-Specific Temporary Root):**
  - All declared outputs (`_stage_public`, `_stage_internal`, `_stage_graphs`, `_stage_pages`, `_stage_html`, `_stage_report`) are synthesized in an isolated temporary staging root.

- **AC-002 (Artifact Validation):**
  - Complete artifact set validated in `_stage_validate` before any promotion step is attempted.

- **AC-003 & AC-004 (Immutable Tree / Atomic CAS Promotion):**
  - Outputs are materialized as immutable content-addressed directory trees with atomic CAS lease locking (`output_root_lease`, `assert_output_cas`, `_promote`).
  - Staged tree replaces destination atomically via rename/CAS switch without intermediate torn state.

- **AC-005 (Rollback & Clean Staging):**
  - Staging directories are cleaned up only after recorded promotion success; prior tree is retained on failure to ensure rollback and determinism.

## Validation

Verified via `_src/tests/test_issue_regenerate.py`.
