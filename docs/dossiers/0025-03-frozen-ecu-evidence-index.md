# 0025-03 Evidence Dossier: Validated & Frozen Automotive ECU Evidence Index

- **Task**: `0025-03`
- **Assignee**: `benjamin` (Dispatcher, Team DeepSpace9)
- **Role**: Dispatcher / Implementation
- **Base Commit**: `5a7340ee24` (`main`)
- **Status**: `review`
- **Worktree**: `/Users/tobias.anton/devel/autodocs/.worktrees/0025-03`
- **Branch**: `feature-0025-03`
- **Governing Standard & Rules**: Automotive SPICE (PAM 3.1 / PAM 4.0), `req-0020-02-evidence-boundary` / `DEC-0020-002`, `req-0020-08-evidence-catalogue`, `DEC-0024-REL-20260919-01`

---

## 1. Objective & Scope

Task `0025-03` validates and freezes the authoritative ECU Evidence Index for the **`virtualized-automotive-ecu:v0.6.0`** release baseline (`60d9a85`):
1. **Full Metadata Boundary (`REQ-0020-02` / `DEC-0020-002`)**:
   - Every evidence record binds `product_id` (`virtualized-automotive-ecu`), `project_id` (`autodocs-ecu-software`), `baseline_id` (`virtualized-automotive-ecu@software-without-kernel:v0.6.0`), `process_id`, `process_instance_id`, `revision` (SHA-256 digest), `owner`, `origin`, `validity`, `retention`, and `confidentiality`.
2. **Strict Origin Isolation (`REQ-0020-02` / `REQ-0020-08`)**:
   - Origin must be **`ecu-execution`** exclusively for all ECU outcome claims.
   - Documentation-pipeline artifacts (`documentation-execution`), process definitions (`process-definition`), and synthetic scenario runs (`controlled-scenario`) are strictly excluded from ECU outcome claims.
3. **Cross-Product & Cross-Project Anti-Substitution**:
   - Prohibits opportunistic aggregation or cross-product substitution from non-ECU modules.
4. **Base Practice & Work Product Indicator Mapping**:
   - Explicitly maps each evidence unit to official ASPICE Base Practices (`BP1`–`BP4`) across all 14 nucleus processes (`SWE.1`–`SWE.6`, `SPL.2`, `SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`, `MAN.3`, `MAN.5`, `MAN.6`) plus `VAL.1`.
5. **Authenticity, Contrary Evidence & Limitation Tracking**:
   - Validates cryptographic SHA-256 digest for every artifact.
   - Explicitly tracks contrary evidence (0 items) and unresolved limitations (0 open blockers).

---

## 2. Deliverables Summary

1. **Evidence Validation & Freeze Engine**:
   - [`_src/tools/ecu_evidence_index.py`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0025-03/_src/tools/ecu_evidence_index.py)
   - CLI tool and module for validating evidence records against strict schema and freezing the repository index.

2. **Machine-Readable Frozen JSON Evidence Index**:
   - [`docs/dossiers/evidence-index/FROZEN-ECU-EVIDENCE-INDEX-v0.6.0.json`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0025-03/docs/dossiers/evidence-index/FROZEN-ECU-EVIDENCE-INDEX-v0.6.0.json)
   - Contains all 15 validated evidence records with SHA-256 digests, process instances, owners, and outcome indicator mappings.

3. **Human-Readable Companion Specification**:
   - [`docs/pipeline/ecu-frozen-evidence-index.md`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0025-03/docs/pipeline/ecu-frozen-evidence-index.md)
   - Tabular summary and process-by-process breakdown of frozen evidence items.

4. **Automated Verification Test Suite**:
   - [`_src/tests/test_ecu_evidence_index.py`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0025-03/_src/tests/test_ecu_evidence_index.py)
   - 12 comprehensive unit tests verifying all validation constraints and negative boundary paths.

---

## 3. Adversarial Completion Evidence (`DEC-0038-004`)

### AE-1: Applicability
This change establishes the **canonical evidence baseline and boundary enforcement for ASPICE Level-1 and Level-2 assessment readiness**.

### AE-2: Baselines
- Pre-change baseline: `5a7340ee24` (`main`)
- Candidate commit: `feature-0025-03`

### AE-3: Falsification Cases (Red-first / Boundary Resistance)
1. **Documentation-Pipeline Origin Exclusion (`test_reject_documentation_execution_origin`)**:
   - Proves artifacts marked with `documentation-execution` origin are rejected from ECU outcome claims.
2. **Process-Definition Origin Exclusion (`test_reject_process_definition_origin`)**:
   - Proves templates and process definition documents cannot be substituted as execution evidence.
3. **Cross-Product Substitution Refusal (`test_reject_cross_product_substitution`)**:
   - Proves artifacts targeting non-assessed product IDs are rejected.
4. **Baseline Version Mismatch Refusal (`test_reject_baseline_mismatch`)**:
   - Proves obsolete or unapproved baseline IDs are rejected.
5. **Mandatory Field Omission (`test_reject_missing_required_fields`)**:
   - Proves artifacts missing owner, revision, validity, or retention fields fail validation.
6. **Empty Outcome Indicators Refusal (`test_reject_empty_outcome_indicators`)**:
   - Proves unmapped artifacts cannot enter the frozen index.

---

## 4. Test Execution & Verification

Executed test suite across all evidence index tests:
```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0
rootdir: /Users/tobias.anton/devel/autodocs/.worktrees/0025-03
configfile: pyproject.toml
collecting ... collected 12 items

_src/tests/test_ecu_evidence_index.py ............                       [100%]

============================== 12 passed in 0.09s ==============================
```
