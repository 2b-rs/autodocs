# 0024-01 Evidence Dossier: ECU SPL.2 Product Release Specification

- **Task**: `0024-01`
- **Assignee**: `benjamin` (Dispatcher, Team DeepSpace9)
- **Role**: Dispatcher / Implementation
- **Base Commit**: `e015400b80` (`main`)
- **Status**: `review`
- **Worktree**: `/Users/tobias.anton/devel/autodocs/.worktrees/0024-01`
- **Branch**: `feature-0024-01`
- **Deliverable**: `docs/pipeline/ecu-spl2-product-release-specification.md`

---

## 1. Objective & Scope

Task `0024-01` establishes the authoritative Automotive SPICE `SPL.2` (Product Release) engineering specification for the Automotive ECU software product (`virtualized-automotive-ecu@software-without-kernel:v0.6.0`).

The specification covers all twelve mandatory dimensions defined in the task contract:
1. **ECU Release Content Structure**: Nine controlled categories (Firmware/Executables, Calibration/Configuration, Flashing/Delivery Containers, Release Notes, Known Limitations, Licenses/Notices/SBOM, Support & SLA, Rollback Procedures, and Release Manifest).
2. **Cryptographic Identity & Baselines**: Canonical semantic versioning tag (`v0.6.0-ECU-REL-20260919`), Git commit hash, build environment compiler triple, and signed SHA-256 digest manifests.
3. **Eligibility & Approval Criteria**: Five mandatory quality and governance gates (SWE.6 qualification pass, SUP.8 baseline integrity, SUP.9/SUP.10 defect/change resolution, SUP.1 QA/safety clearance, and formal MAN.3 Project Lead release sign-off).
4. **Hardware, Vehicle & Variant Scope**: ARM Cortex-M4 / QEMU virtual SIL targets, CAN-FD / 100BASE-T1 network interfaces, and three defined variants (`VAR-STD-01`, `VAR-POW-02`, `VAR-SIL-03`).
5. **Firmware & Executable Artifacts**: Stripped binaries (`.elf`, `.bin`, `.hex`) and linker memory maps (`.map`).
6. **Calibration & Configuration Artifacts**: CDFX parameter datasets, ASAM MCD-2MC (A2L) description files, and variant configuration matrices.
7. **Flashing & Delivery Containers**: ASAM ODX-F flash containers, ISO 14229 UDS flashing automation, and encrypted key verification.
8. **Release Notes & Change Traceability**: Traceability to `SWE.1` requirements, `SUP.9` problem tickets, and `SUP.10` change requests.
9. **Known Limitations & Deviations**: Formal waiver records, residual risks (`MAN.5`), and operational constraints.
10. **Licenses, Notices & SBOM**: Software licenses, third-party attributions, and machine-readable SPDX 2.3 Software Bill of Materials.
11. **Support, SLA, Update & Rollback Information**: Dual-bank A/B bootloader fallback, manual in-field UDS recovery routines, and 5-year security patch lifecycle.
12. **Release Record Schema & Retention**: Formal JSON Schema (`ecu-release-record@v1`) and 15-year immutable WORM archive retention for automotive compliance.

---

## 2. Adversarial Completion Evidence (`DEC-0038-004`)

### AE-1: Applicability
This substantive change establishes **release gate criteria, artifact classification, schema constraints, and compatibility boundaries** for the ECU software product lifecycle.

### AE-2: Baselines
- Pre-change baseline: `e015400b80` (`main`)
- Candidate deliverable: `docs/pipeline/ecu-spl2-product-release-specification.md` on branch `feature-0024-01`.

### AE-3: Falsification Cases (Red-first / Gate Enforcement)
1. **Gate Rejection on Incomplete Package**:
   - Condition: Release bundle missing required ODX-F container or A2L database.
   - Evaluation: Fails Gate 2 (`SUP.8` Configuration Baseline Audit) and Gate 5 (Authorization Refused).
2. **Gate Rejection on Open Critical Anomalies**:
   - Condition: Unresolved Severity 1 (`PRB-*`) ticket without signed Project Lead waiver.
   - Evaluation: Fails Gate 3 (`SUP.9`/`SUP.10` Problem Resolution) and blocks release promotion.
3. **Gate Rejection on Failed Qualification**:
   - Condition: Any SWE.6 qualification measure failing (`< 100%`).
   - Evaluation: Fails Gate 1 (`G-SWE6-QUAL`) and unconditionally prevents release tagging.

### AE-4: Adjacent Contract Cases
- **Adjacent Case 1 (Documentation vs ECU Product Release)**:
  - Generic site publication specification (`0016-06` / `spl2-release-specification.md`) addresses static web assets.
  - `0024-01` specifically defines embedded ECU automotive software releases (ODX-F flashing, A/B dual-bank bootloader, ASIL B/D safety mechanisms, ASAM A2L, and 15-year liability retention).
- **Adjacent Case 2 (Specification vs Downstream Release Execution)**:
  - `0024-01` defines the formal requirements, schema, and gates.
  - `0024-02` executes the actual assembly, validation audit, approval, delivery, and receipt verification against these criteria.

### AE-5: Property Evidence for Manifest Integrity
- Invariant: Every artifact listed in `package_manifest.artifacts` must have a valid relative path, non-negative `size_bytes`, and a valid `sha256:` hexadecimal digest matching its canonical binary content.

---

## 3. Verification & Traceability

- Standard: Automotive SPICE PAM 3.1/4.0 `SPL.2.BP1`..`BP7`.
- File Path: [`docs/pipeline/ecu-spl2-product-release-specification.md`](file:///Users/tobias.anton/devel/autodocs/.worktrees/0024-01/docs/pipeline/ecu-spl2-product-release-specification.md).
- Status: Fully specified, reviewed against ASPICE Level 2/3 requirements, and ready for integration.
