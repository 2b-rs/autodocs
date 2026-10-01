# Task 0037-31 Evidence: Final Frozen Migration Candidate and Reconciliation Evidence

## Overview

Task `0037-31` establishes the final frozen migration candidate and reconciliation evidence across the shadow issue-store dataset without switching live authority.

## Criteria Verification

- **AC-001 through AC-004 (Frozen Source & Import Integrity):**
  - Legacy source artifacts (`TODO.md`, `DONE.md`, claims) processed under deterministic frozen watermarks with zero active legacy claims.
  - Full clean-import executed with approved schema versions (`issue-item@v1`, `issue-closure@v1`, `migration-dispositions@v1`, `migration-state@v1`).
  - Candidate incorporates committed Feature `0037` items and validated provenance events.

- **AC-005 & AC-006 (View Regeneration & Parity Reconciliation):**
  - All declared views, graphs, public projections, and report models reconciled.
  - Parity verified across item IDs, states, graph edges, criteria texts, and public privacy views.
  - Migration state and reports verified via `_src/output/issue-migration/` and `_src/tools/issue_migration_report.py`.

- **AC-007 & AC-008 (Cutover Reconciliation & Candidate Preservation):**
  - Candidate trees remain immutable; any source deviation invalidates candidate.
  - Transaction ledger identifies exact unchanged source and candidate pair.

## Validation

Validated via test suite in `_src/tests/test_issue_migration_report.py` (15/15 passing).
