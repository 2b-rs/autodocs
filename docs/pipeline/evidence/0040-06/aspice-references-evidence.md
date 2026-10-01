# Task 0040-06 Evidence: Automotive SPICE References in Process Documentation

## Overview

Task `0040-06` governs the inclusion of Automotive SPICE references in the engineering process documentation, strictly distinguishing process support from assessed capability (`RQ-STD-01`, `RQ-STD-02`, REF: `7437905a6a6c0b7987ab6870f19cc5fc45ff774b`).

## Criteria Verification

- **AC-001 (ASPICE References Qualification & ECU Assessment Boundary):**
  - References explicitly state that they represent internal engineering **process support, not assessed capability** or a formal compliance claim.
  - Boundary against the formal ASPICE assessment of the ECU product (Features `0011`–`0032`) is explicitly stated in `docs/pipeline/process-roles.md` (Boundaries section) and role definitions under `docs/pipeline/roles/`.
  - Finding A terminological separation documented: "Evidence Baseline" is an internal repository term decomposed into SUP.8 configuration baselines and SWE/SYS bidirectional traceability practices.
  - Section 7 of `docs/pipeline/process-roles.md` explicitly identifies uncovered responsibilities and confirms no complete ASPICE practice chain is claimed.

## Deliverables
- `docs/pipeline/evidence/0040-06/aspice-references-evidence.md`
