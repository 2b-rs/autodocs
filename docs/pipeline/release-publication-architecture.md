# Release Publication Architecture (Feature 0016-07)

## Purpose
This document establishes the architecture for the product release process (SPL.2). It enforces that a release can only be published if it strictly traces to a complete, atomic evidence bundle and an approved baseline. It also mandates the retention of approval, delivery verification, and rollback evidence.

## 1. Pre-Publication Verification
Before any artifact is packaged or delivered to the client, the release pipeline must execute a mandatory verification gate.
- **Atomic Evidence Bundle:** The release candidate must reference exactly one immutable evidence bundle hash (Feature 0015-06).
- **Completeness Check:** The tooling must assert that this bundle contains 100% of the required subreports (unit tests, integration tests, QA audit, security scans, etc.).
- **Baseline Approval:** The underlying configuration baseline must be explicitly marked as `Approved` by the designated Release Authority. If the baseline is in a `Draft` or `Suspect` state, the publication must abort immediately.

## 2. Artifact Packaging
Once verification passes, the pipeline packages the release.
- **Configured Languages & Reports:** The packaging step must deterministically compile and assemble all configured target languages, binaries, and user-facing reports.
- **Manifest Inclusion:** The generated release package must embed a digital manifest (e.g., `release-manifest.json`) containing the exact hashes of the evidence bundle and the source baseline, proving its provenance.

## 3. Delivery & Rollback Evidence
The act of publishing/delivering the release must generate its own immutable evidence.
- **Delivery Verification:** The system must record a "Delivery Receipt" confirming that the exact hashed package was successfully transferred to the target environment or client repository.
- **Rollback Readiness:** The delivery record must include the explicit rollback procedure and the hash of the previously known-good release, ensuring that rapid reversion is possible in case of post-deployment failure.
- **Retention:** These publication records (approval, receipt, rollback plan) must be committed back into the Immutable Evidence Repository.
