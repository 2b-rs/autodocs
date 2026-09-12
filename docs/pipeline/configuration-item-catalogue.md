# Work-Product & Configuration-Item Catalogue

**Status:** Normative
**Reference:** Feature 0015-01 (Prerequisite `0011-05`)

This catalogue identifies the controlled configuration items (CIs) required for the ECU profile, extending the baseline process evidence catalogue across all specified artifact classes.

## 1. Classification & Scope
Every controlled work product generated during the software lifecycle MUST fall into one of the following CI classes.

### 1.1 Requirements & Specifications
- **Description:** Documents and structured data defining what the system must do.
- **Examples:** Stakeholder requirements (`docs/dossiers/req-*-*.md`), Software Requirement Specification (SWE.1), Architectural Design (SWE.2).
- **Control Level:** Full version control, mandatory peer review (TK-1), and baseline approval before subsequent phase release.

### 1.2 Plans
- **Description:** Strategic and operational project plans.
- **Examples:** Project Management Plan (MAN.3), Risk Management Strategy (MAN.5), Integration Plan (SWE.5), QA Plan (SUP.1).
- **Control Level:** Versioned baselines, approved by Process Owner/Management.

### 1.3 Records & Traces
- **Description:** Immutable logs of activities, measurements, and audits.
- **Examples:** Risk records (MAN.5), measurement data (MAN.6), process execution logs, traceability matrices.
- **Control Level:** Append-only or strictly versioned; deletion/modification prohibited without explicit authorization.

### 1.4 Source Code
- **Description:** Human-authored implementation files.
- **Examples:** C++, Rust, Python implementation files (`_src/`, `classic/`).
- **Control Level:** Strict branching, automated CI validation, peer review, and integration approval.

### 1.5 Generated Artifacts
- **Description:** Files created by automated toolchains from source or configuration data.
- **Examples:** Compiled binaries, generated `ARXML`, rendered HTML sites.
- **Control Level:** Must be deterministically reproducible. Derived artifacts are either excluded from source control (generated on demand) or stored in controlled release registries.

### 1.6 Schemas & Templates
- **Description:** Structural definitions for validation and generation.
- **Examples:** JSON schemas (`integration-plan.schema.json`), Markdown templates, XSD definitions.
- **Control Level:** Version-controlled; changes require architectural review as they impact validation.

### 1.7 Tests
- **Description:** Executable specifications and validation suites.
- **Examples:** Unit tests (SWE.4), integration tests (SWE.5), qualification tests (SWE.6).
- **Control Level:** Kept in sync with source code; must pass in CI environment before baseline acceptance.

### 1.8 Reports
- **Description:** Generated summaries of process or product states.
- **Examples:** Test execution reports, QA audit summaries, build matrices.
- **Control Level:** Immutable generation bound to a specific source commit hash.

### 1.9 Decisions
- **Description:** Formal architectural, management, or scope decisions.
- **Examples:** `decision-record.md` instances, TK-2 trigger records, architecture breakdowns.
- **Control Level:** Append-only, requires explicit assignment of an Architect or Management authority.

### 1.10 Problems & Changes
- **Description:** Defect reports and change requests.
- **Examples:** GitHub Issues (mirrored as `issue-store` artifacts), SUP.9 problem records, SUP.10 change requests.
- **Control Level:** State-machine tracked; must transition to verified/closed states.

### 1.11 Dependencies
- **Description:** External components, libraries, and environmental constraints.
- **Examples:** Python `requirements.txt`, Rust `Cargo.lock`, pinned build tools.
- **Control Level:** Exact version pinning (hash verification); changes require integration review.

### 1.12 Releases
- **Description:** Formal product baselines intended for delivery.
- **Examples:** Release candidate tags, `SPL.2` release packages, firmware blobs.
- **Control Level:** Cryptographically signed/hashed, retained in persistent storage, requires Release Authority approval.

### 1.13 Assessment Evidence
- **Description:** Collated evidence explicitly structured for formal capability assessment.
- **Examples:** ASPICE assessment input records, evidence mappings (`docs/ASPICE/05-evidence-register.md`), CI catalogues.
- **Control Level:** Frozen during the assessment period; cannot be altered once the assessment baseline is defined.

## 2. Configuration Management Constraints
For all identified items above:
- **Identity:** Each artifact must possess a unique identifier and version.
- **Storage:** Managed centrally within the `autodocs` repository or an authorized binary artifact store.
- **Status Accounting:** The status (draft, proposed, approved, baselined) must be derivable from the CI platform (e.g., commit history, `TODO.md` gates).
