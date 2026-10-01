# Configuration Status Accounting & Baselining (Feature 0015-03)

## Purpose
This document defines the architectural implementation guidelines for Configuration Identification, Baseline Creation, Controlled Change, and Configuration Status Accounting (CSA). These mechanisms ensure compliance with ASPICE SUP.8 requirements for all configuration items (CIs).

## 1. Configuration Identification
Every Configuration Item (CI) must be assigned a unique, immutable identifier that guarantees traceability.
- **Identifier Structure:** CIs must use the format `[Project]-[Category]-[ItemHash/Version]` (e.g., `AUTODOCS-REQ-v1.2.0`).
- **Cryptographic Hashing:** Source code, binary blobs, and external dependencies must be identified by their SHA-256 cryptographic hash to guarantee immutability.

## 2. Baseline Creation & Reproducibility
A baseline is a frozen configuration of CIs at a specific point in time (e.g., a Release candidate or a Campaign execution).
- **Baseline IDs:** Baselines must be tagged with a unique, monotonically increasing semantic version (e.g., `R25-01.00`).
- **Reproducibility:** A baseline ID must uniquely define the entire environment, dependencies, source trees, and generated documentation. It must be possible to reconstruct the exact baseline state from the version control and artifact stores using only the Baseline ID.
- **Completeness Audits:** Automated checks must run prior to freezing a baseline to ensure all required CIs (requirements, designs, test results) are present, approved, and linked.

## 3. Controlled Change
Once a CI is part of a frozen baseline, it cannot be mutated.
- **Change Traceability:** Changes to a CI require creating a new version of the CI.
- **Change Requests (SUP.10):** Altering a CI in an approved baseline requires an approved Change Request. The system must record the link between the new CI version and the authorizing Change Request ID.

## 4. Configuration Status Accounting (CSA)
The system must provide the ability to query and report on the status of any CI or baseline.
- **Status Queries:** It must be possible to query a CI's current state (e.g., Draft, In Review, Approved, Archived) and its full version history.
- **Consistency Audits:** The CSA system must support automated consistency audits, generating reports that highlight orphan CIs, unapproved modifications, or broken dependency links within a baseline.
- **Audit Logs:** All state transitions and baseline creation events must be durably logged with a timestamp and the authenticated actor.
