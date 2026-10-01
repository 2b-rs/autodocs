# Task 0040-05 Evidence: Feature-Breakdown Extension and Escalation Path Alignment

## Overview

Task `0040-05` establishes and verifies the extension to the Feature-breakdown process and the `AGENTS.md` autonomous backlog-repair rules to detect the `T1`–`T8` defect class before implementation (`RQ-PROC-01` through `RQ-PROC-04`, `DEC-0040-005`, REF: `f06867e06529469e26452e9cf20d362eb0d9648e` / `063a85998f90197b698b9672e816ffaba7e5fb15`).

## Criteria Verification

- **AC-001 (Gate Declaration & Pre-Mutation Scope Review):**
  - Any task installing a gate capable of blocking other tasks must declare its scope as a named, justified `decision-record@v1` with the `cross-item-blast-radius` trigger.
  - Requires pre-mutation scope review by a Management-instantiated Architect distinct from the Implementer before the first mutation.
  - Escalation path in `AGENTS.md` resolves the conflict with autonomous repair: latent scoping defects with cross-item reach require decision records and Architect support before mutation; difficulty, unfamiliarity, and routine local repairs remain non-escalating.

- **AC-002 (Objective Reach Boundary & Green-Validation Limit):**
  - Operative four-case decision table in `docs/pipeline/process-roles.md` (Section 5) and `AGENTS.md` (Cross-item gate-scope review exception) defines the boundary without subjective judgment calls.
  - Explicitly states that green validation is insufficient evidence of scope correctness or completeness (`T2`).

## Deliverables
- `docs/pipeline/evidence/0040-05/feature-breakdown-extension-evidence.md`
