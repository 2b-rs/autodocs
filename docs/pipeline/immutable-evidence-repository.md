# Immutable Evidence Repository (Feature 0015-06)

## Purpose
This document defines the architecture for the immutable evidence repository. It replaces the reliance on transient, unversioned `output/` directories with a strictly controlled, append-only store for runner scripts, test/QA results, decisions, approvals, and release records.

## 1. Segregation from Transient Output
Historically, test results and temporary artifacts were written to local `output/` directories which were ignored by version control. This architectural change prohibits the use of unversioned directories for compliance-critical evidence.
- **Transient Data:** Temporary files (e.g., intermediate build objects) may still use `output/`, but they hold no evidentiary value.
- **Evidence Repository:** All formal test results, subreports, logs, and approval records must be committed to the `provenance/` ledger (or a dedicated immutable store).

## 2. Immutable, Append-Only Storage
The evidence repository operates as a cryptographic ledger.
- **Append-Only:** Existing evidence records cannot be deleted or modified. If an error is found or a test is re-run, a new record is appended that supersedes the previous one (via an explicit `supersedes: [Hash]` relationship).
- **Cryptographic Hashes:** Every evidence artifact (test log, approval signature) is stored based on its SHA-256 hash.

## 3. Correlated Subreports & Artifacts
A test execution or campaign run generates multiple artifacts (e.g., runner scripts, raw stdout logs, parsed XML test results, coverage metrics).
- **Correlation:** The system must generate an overarching **Evidence Bundle Manifest** that explicitly links all these sub-artifacts together via their content hashes.
- **Reproducibility:** Runner scripts and environmental logs (e.g., OS version, dependency hashes from Feature 0015-04) must be included in the bundle to guarantee that the test execution can be audited or reproduced.

## 4. Decisions, Approvals, & Releases
All human and automated decisions (e.g., Architect approvals, QA sign-offs, Release Records) must be cryptographically signed (or durably recorded with authenticated actor IDs) and committed directly into the evidence repository. A release baseline is only valid if its corresponding Release Record exists in the immutable store and all prerequisites (tests, reviews) trace back to successful, unmodified evidence bundles.
