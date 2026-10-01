# Task 0037-32 Evidence: Independent Pre-Cutover Audit of Frozen Candidate and Final Authority Tree

## Overview

Task `0037-32` executes the independent pre-cutover audit of the exact frozen candidate and prepared final authority tree under the single-authority readiness model (`0037-49`, `DEC-0044-014`).

## Criteria Verification

- **AC-001 (Pre-Cutover Audit Verification & Runner Profile):**
  - Evaluated against `issues/_policy/audit-profiles.json` (`feature-0037` profile):
    - Mandatory actions verified (discovery, focused validation, generation, path-limited commits, bookkeeping commits).
    - High-risk cases verified (stale-base, dual-authority-write, approval-ref-tampering, public-projection-leak, partial-mutation-recovery).
    - Parity confirmed across graph, public projection, i18n registers, and HTML views.
    - Exact agent-instruction bundle and authority epoch guards verified (`docs/pipeline/agent-instructions/`).
    - Single-authority governance model (`DEC-0044-014`, `0037-49`) applied.

- **AC-002 (Post-Cutover Reference Integrity):**
  - Exact artifact digests and control-closure delta verified ready for final reference materialization in `0037-40`.

## Deliverables
- `docs/pipeline/evidence/0037-32/pre-cutover-audit-evidence.md`
