# 0018-01 Evidence Dossier: Automotive ECU Managed Pilot Selection & Assessment Plan (CL2)

- **Task**: `0018-01`
- **Assignee**: `benjamin` (Dispatcher, Team DeepSpace9)
- **Role**: Dispatcher / Implementation
- **Base Commit**: `3bd24b06a` (`main`)
- **Status**: `review`
- **Worktree**: `/Users/tobias.anton/devel/autodocs/.worktrees/0018-01`
- **Branch**: `feature-0018-01`
- **Governing Standard**: Automotive SPICE (PAM 3.1 / PAM 4.0) Capability Level 2 (Managed Process), ISO/IEC 33020, `docs/pipeline/ecu-level1-success-cl2-handoff.md` (`0025-10`), `docs/pipeline/ecu-published-assessment-profile.md` (`0025-09`)

---

## 1. Objective & Scope

Task `0018-01` establishes the authoritative selection, planning, sampling protocol, and governance safeguards for the **Automotive SPICE Capability Level 2 Managed Process Pilot** on the **`virtualized-automotive-ecu:v0.7.0-pilot1`** baseline (`8b2c49f`):
1. **Representative Process Instance & Release Selection**:
   - Selects and approves 17 representative process instances spanning the complete automotive software development V-cycle (`SWE.1`–`SWE.6`, `SYS.2`–`SYS.3`, `VAL.1`, `SPL.2`, `SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`, `MAN.3`, `MAN.5`, `MAN.6`).
   - Targets Automotive SPICE Capability Level 2 (Managed Process: GP 2.1 Performance Management & GP 2.2 Work Product Management).
2. **Assessment Schedule & Role-Based Interview Battery**:
   - Establishes 6 structured interview sessions (`SESS-PILOT-01` to `SESS-PILOT-06`) across key functional roles (Project Lead, Requirements Engineer, Architect, Software Developer, Tester, Integrator, QA-Manager, Safety & Security Officer).
3. **Evidence Baseline & Cross-Campaign Isolation Governance**:
   - Enforces strict execution origin rule: `ecu-execution exclusively`.
   - Explicitly establishes that documentation campaigns (such as Feature `0019`) may contribute **reusable definitions, schemas, and procedural mechanisms only**, and **under no circumstances may enter as ECU execution evidence or imported ratings**.
4. **Risk-Informed Adaptive Sampling & Aggregation Rules**:
   - Formulates 3 concrete sampling rules (`SAMP-RULE-01`..`03`):
     - `SAMP-RULE-01`: 100% census audit for safety-critical components (`SWC-SAFETY`, `SWC-CRYPTO`).
     - `SAMP-RULE-02`: Risk-informed representative sampling for general components (`SWC-DIAG`, `SWC-TELEM`).
     - `SAMP-RULE-03`: Strict evidence isolation across documentation and execution baselines.
5. **Assessor Independence & Governance Approvals**:
   - Establishes strict separation of duties and 4-eyes authorization protocols with sign-offs from Project Sponsor (`jadzia`), Lead Assessor (`odo`), QA Authority (`jake`), and Architect (`kira`).

---

## 2. Deliverables Summary

1. **Pilot Assessment Plan Tool**:
   - [`_src/tools/ecu_pilot_plan.py`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0018-01/_src/tools/ecu_pilot_plan.py)
   - Builds pilot plan payload, verifies selection rules, computes SHA-256 digest, and exports JSON/Markdown records.

2. **Machine-Readable Pilot Assessment Plan**:
   - [`docs/dossiers/assessment/ECU-PILOT-ASSESSMENT-PLAN-v0.7.0.json`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0018-01/docs/dossiers/assessment/ECU-PILOT-ASSESSMENT-PLAN-v0.7.0.json)
   - Machine-verifiable payload with deterministic SHA-256 digest (`pilot_plan_sha256`), 17 selected process instances, 6 interview sessions, and 3 sampling rules.

3. **Human-Readable Companion Report**:
   - [`docs/pipeline/ecu-pilot-managed-assessment-plan.md`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0018-01/docs/pipeline/ecu-pilot-managed-assessment-plan.md)

4. **Automated Verification Test Suite**:
   - [`_src/tests/test_ecu_pilot_plan.py`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0018-01/_src/tests/test_ecu_pilot_plan.py)
   - 7 unit tests verifying process selection completeness (17 instances), interview coverage (6 sessions), sampling rules, documentation campaign isolation policy, independence safeguards, and deterministic serialization.

---

## 3. Adversarial Completion Evidence (`DEC-0038-004`)

### AE-1: Applicability
This change delivers the **authoritative planning, process selection, interview battery, evidence baseline definition, and independence governance for the ECU Managed Process Pilot (CL2)**.

### AE-2: Baselines
- Pre-change baseline: `3bd24b06a` (`main`)
- Candidate commit: `feature-0018-01`

### AE-3: Falsification Cases (Red-first / Selection & Evidence Integrity)
1. **17-Process Selection Completeness (`test_selected_pilot_processes_completeness`)**:
   - Proves all 17 target process instances are explicitly selected, categorized, and justified for CL2 entry.
2. **Interview Schedule & Role Coverage (`test_interview_schedule_and_roles`)**:
   - Proves 6 structured sessions covering all engineering, management, and supporting processes with assigned role participants.
3. **Cross-Campaign Isolation Policy Enforcement (`test_sampling_and_evidence_isolation_rules`)**:
   - Proves documentation campaigns (Feature 0019) are restricted to reusable mechanisms only with zero imported ratings or synthetic evidence.
4. **Assessor Independence & Governance Approvals (`test_assessor_independence_and_signoffs`)**:
   - Proves 4-eyes signatures (`jadzia`, `odo`, `jake`, `kira`) and strict reporting independence for assessors.
5. **Digest Stability & Serialization (`test_write_and_digest_stability`)**:
   - Proves deterministic JSON serialization and SHA-256 digest computation.

---

## 4. Test Execution & Verification

Executed full test suite across all 9 ECU assessment and pilot modules:
```
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/tobias.anton/devel/autodocs/.worktrees/0018-01
configfile: pyproject.toml
collecting ... collected 70 items

_src/tests/test_ecu_assessment_report.py .........                       [ 12%]
_src/tests/test_ecu_cl2_handoff.py ........                              [ 24%]
_src/tests/test_ecu_evidence_index.py ............                       [ 41%]
_src/tests/test_ecu_finding_triage.py ......                             [ 50%]
_src/tests/test_ecu_pilot_plan.py .......                                [ 60%]
_src/tests/test_ecu_process_assessment.py ......                         [ 68%]
_src/tests/test_ecu_published_profile.py ........                        [ 80%]
_src/tests/test_ecu_readiness_review.py ......                           [ 88%]
_src/tests/test_ecu_reassessment_cycle.py ........                       [100%]

============================== 70 passed in 0.58s ==============================
```
