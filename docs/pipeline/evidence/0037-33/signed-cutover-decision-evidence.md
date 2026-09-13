# Task 0037-33 Evidence: Signed Process/Security/Release Cutover Decision

## Overview

Task `0037-33` verifies the single-authority signed cutover decision under `DEC-0044-014` and `0037-49` for the exact candidate and prepared authority-switch patch.

## Criteria Verification

- **AC-001 (Single Authority Cutover Decision):**
  - Rescoped from distributed signers to the single repository-owner authority (`DEC-0044-014`, `0037-49`).
  - Evaluated candidate, control-base commits, patch/artifact digests, validation/audit reports, and `docs/pipeline/agent-instructions/` epoch switch.
  - Approval ref topology and immutable control ledger verified.

- **AC-002 & AC-003 (Package Integrity & Separation):**
  - Package commit, digest, and validity recorded in approval records (`docs/pipeline/0037-07-approval.json`).
  - No candidate author self-approves.
  - Integration HEAD preserved without dual authority activation.

## Deliverables
- `docs/pipeline/evidence/0037-33/signed-cutover-decision-evidence.md`
