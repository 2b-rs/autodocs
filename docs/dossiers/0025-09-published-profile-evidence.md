# 0025-09 Evidence Dossier: Automotive ECU Management Decision & Published Assessment Profile

- **Task**: `0025-09`
- **Assignee**: `benjamin` (Dispatcher, Team DeepSpace9)
- **Role**: Dispatcher / Implementation
- **Base Commit**: `075959159` (`main`)
- **Status**: `review`
- **Worktree**: `/Users/tobias.anton/devel/autodocs/.worktrees/0025-09`
- **Branch**: `feature-0025-09`
- **Governing Standard**: Automotive SPICE (PAM 3.1 / PAM 4.0), ISO/IEC 33020, `docs/pipeline/ecu-independent-readiness-review.md` (`0025-08`), `docs/pipeline/ecu-reassessment-cycle-record.md` (`0025-07`), `docs/pipeline/ecu-level1-assessment-report.md` (`0025-05`)

---

## 1. Objective & Scope

Task `0025-09` formally records the executive Management Decision and publishes the supported process capability profile for the **`virtualized-automotive-ecu:v0.6.0-rev1`** baseline (`7a1b49e`):
1. **Executive Management Decision**:
   - Formally records `DEC-0025-PUBLISH-20260919-01` authorizing publication of the evidence-backed process capability profile under Project Sponsor (`jadzia`) authority.
2. **Boundary & Anti-Overclaiming Policy Enforcement**:
   - Enforces strict compliance with `NO_BLANKET_LEVEL1_OR_CL2_ENTRY_CLAIM`:
     - Publishes specific per-process performance ratings (`PA 1.1 = F`) across the 15 declared embedded software process instances.
     - Prohibits over-claiming organizational maturity or asserting Automotive SPICE Level 2 (Managed Process) entry.
     - Confirms hardware (`HWE.1-4`) and external kernel acquisition (`ACQ.4`) remain unrated / external.
3. **Comprehensive Publication Metadata**:
   - Organizational & product scope (`Automotive Systems Division`, `virtualized-automotive-ecu`).
   - PAM version (`Automotive SPICE PAM 3.1 / PAM 4.0 Reference Model`, ISO/IEC 33020).
   - Assessment method & date window (`2026-09-12 to 2026-09-19`).
   - 12-month validity period (`2026-09-19 to 2027-09-19`).
4. **Separate Governance Statements**:
   - **Assessment Disposition Statement**: Lead Assessor (`odo`) certifies the technical achievement of PA 1.1 across 15 processes with zero blocking nonconformances.
   - **Execution Responsibility Statement**: Project Lead (`jadzia`) commits to process adherence, residual risk tracking, and next-cycle execution.
5. **Accepted Limitations & Next-Cycle Improvement Plan**:
   - Records 3 accepted limitations (`LIMIT-0025-01`..`03`).
   - Defines actionable next-cycle roadmap (`PLAN-0025-01`..`03`) covering accredited third-party audit, physical HIL dyno bench testing, and interactive web metric dashboards.

---

## 2. Deliverables Summary

1. **Management Decision & Profile Publication Tool**:
   - [`_src/tools/ecu_published_profile.py`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0025-09/_src/tools/ecu_published_profile.py)
   - Builds published profile payload, enforces claim boundaries, computes SHA-256 digest, and exports JSON/Markdown records.

2. **Machine-Readable Published Assessment Profile**:
   - [`docs/dossiers/assessment/ECU-PUBLISHED-ASSESSMENT-PROFILE-v0.6.0.json`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0025-09/docs/dossiers/assessment/ECU-PUBLISHED-ASSESSMENT-PROFILE-v0.6.0.json)
   - Complete machine-verifiable payload with deterministic SHA-256 digest (`published_profile_sha256`), management decision records, and per-process ratings.

3. **Human-Readable Companion Report**:
   - [`docs/pipeline/ecu-published-assessment-profile.md`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0025-09/docs/pipeline/ecu-published-assessment-profile.md)

4. **Automated Verification Test Suite**:
   - [`_src/tests/test_ecu_published_profile.py`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0025-09/_src/tests/test_ecu_published_profile.py)
   - 8 unit tests verifying management decision structure, claim policy enforcement, 15 process ratings, separate statements, limitations, next-cycle plan, and serialization.

---

## 3. Adversarial Completion Evidence (`DEC-0038-004`)

### AE-1: Applicability
This change delivers the **final management decision and published process capability profile for the Virtualized Automotive ECU Software release**.

### AE-2: Baselines
- Pre-change baseline: `075959159` (`main`)
- Candidate commit: `feature-0025-09`

### AE-3: Falsification Cases (Red-first / Claim Governance & Publication Integrity)
1. **Anti-Overclaiming Policy Enforcement (`test_boundary_and_claim_policy_enforcement`)**:
   - Proves no blanket organizational maturity or CL2 entry claims are made (`NO_BLANKET_LEVEL1_OR_CL2_ENTRY_CLAIM`).
2. **Management Decision Authorization (`test_management_decision_record`)**:
   - Proves formal authorization under `DEC-0025-PUBLISH-20260919-01` by Sponsor (`jadzia`).
3. **Per-Process Performance Completeness (`test_published_process_ratings`)**:
   - Proves 15 in-scope processes are individually rated with `PA 1.1 = F`.
4. **Separate Governance Statements (`test_separate_governance_statements`)**:
   - Proves distinct assessment disposition and execution responsibility statements.
5. **Next-Cycle Roadmap Clarity (`test_next_cycle_improvement_plan`)**:
   - Proves 3 concrete roadmap items (`PLAN-0025-01`..`03`) with owners and milestone dates.
6. **Digest Stability & Serialization (`test_write_and_digest_stability`)**:
   - Proves deterministic JSON serialization and SHA-256 digest computation.

---

## 4. Test Execution & Verification

Executed full test suite across all 7 ECU assessment modules:
```
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/tobias.anton/devel/autodocs/.worktrees/0025-09
configfile: pyproject.toml
collecting ... collected 55 items

_src/tests/test_ecu_assessment_report.py .........                       [ 16%]
_src/tests/test_ecu_evidence_index.py ............                       [ 38%]
_src/tests/test_ecu_finding_triage.py ......                             [ 49%]
_src/tests/test_ecu_process_assessment.py ......                         [ 60%]
_src/tests/test_ecu_published_profile.py ........                        [ 74%]
_src/tests/test_ecu_readiness_review.py ......                           [ 85%]
_src/tests/test_ecu_reassessment_cycle.py ........                       [100%]

============================== 55 passed in 0.38s ==============================
```
