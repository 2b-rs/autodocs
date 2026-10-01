# Subtask 0037-34.01 Evidence: Authority-Switch Patch Preparation and Rollback Package

## Overview

Subtask `0037-34.01` prepares the exact authority-switch patch, final authority tree, and rollback package without mutating live authority (`DEC-0037-002`, `DEC-0037-038`).

## Criteria Verification

- **AC-001 & AC-002 (Final Authority Tree & Generated Projections):**
  - Final authority tree derived from candidate plus deterministic ledger closure delta for `0037-31` and `0037-34.01`.
  - `TODO.md` and `DONE.md` preserved as read-only generated projections.

- **AC-003 & AC-004 (Activation Staging & Authority Artifacts):**
  - Validation/regeneration activation staged while ordinary claim writes remain frozen under `issue-store-frozen`.
  - Future instructions bundle defined in `docs/pipeline/agent-instructions/future/index.md` targeting `issue-store-writable` epoch under signed `0037-40` activation.

- **AC-005 through AC-007 (Rollback & Ledger Packaging):**
  - Rollback and inverse event replay commands prepared in detached worktree context.
  - Integration control-base commits and artifact digests pinned in cutover ledger records.
  - Zero modification made to live authority or main branch.

## Deliverables
- `docs/pipeline/evidence/0037-34.01/authority-switch-patch-evidence.md`
