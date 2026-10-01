# Task 0040-03 Evidence: Mandatory Decision Record Definition and Schema Verification

## Overview

Task `0040-03` establishes the normative decision record definition (`decision-record@v1`) under `docs/pipeline/decision-record.md`, satisfying `RQ-DEC-01` through `RQ-DEC-05` (REF: `7bca09caeea83b8e26e2d69dd4f837eaa2317f39` / `baeb530b6eeaf03b675bb4abd012020cc9b1fe4c`).

## Criteria Verification

- **AC-001 (Normative Definition & Schema Properties):**
  - Stable ID format (`DEC-[0-9]{4}-[0-9]{3}`).
  - Full ISO-8601 timestamps with explicit timezone.
  - Strict identity grammars (agent tokens, registered authority, legacy authority).
  - Subject, decision, technical justification, considered alternatives with dispositions/reasons, and consequences.
  - Append-only corrections and provenance model.

- **AC-002 (Mandatory Blast-Radius Triggers & Examples):**
  - Reach / blast-radius trigger (`cross-item-blast-radius`).
  - Closed trigger set: `cross-item-blast-radius`, `authority-tailoring-or-waiver`, `material-architecture-or-repository-behavior`, `irreversible-or-external-effect`, `security-or-credential-boundary`, `public-release`, `material-risk-decision`.
  - Positive worked examples (3 positive cases) and negative worked examples (2 negative cases).
  - Migration and compatibility disposition for `DEC-0040-001` through `DEC-0040-004`.
  - Explicit bounded waiver structure (conflict, reason, scope, duration, compensating controls).

## Deliverables
- `docs/pipeline/decision-record.md`
- `docs/pipeline/evidence/0040-03/decision-record-definition-evidence.md`
