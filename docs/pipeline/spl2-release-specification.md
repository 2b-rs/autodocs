# SPL.2 Product Release Specification (0016-06)

**Status:** Normative
**Reference:** Feature `0016-06` (Prerequisites: `0015-03`, `0015-07`)

This document defines the formal criteria and processes for assembling, approving, and delivering a Product Release (SPL.2) within the project lifecycle.

## 1. Release Identification and Content

Every release must have a unique identifier following semantic versioning combined with a campaign label (e.g., `v1.2.0-CampaignB`).
The release package MUST contain:
1. The executable binary or source code bundle.
2. The complete configuration baseline identifier (`git tag`).
3. Formal Release Notes.
4. Open Source Software (OSS) and Commercial License disclosures.
5. The unified evidence dossier containing QA audits, test results, and risk closures.

## 2. Eligibility and Approval Criteria

A Release Candidate (RC) is eligible for publication ONLY if it meets all the following criteria:
1. **Traceability Complete:** 100% bidirectional coverage from Stakeholder Requirements to Code/Tests verified by preflight.
2. **Verification Passed:** All unit, integration, and qualification tests pass with 0 Critical/High defect findings.
3. **QA Audit Clear:** The SUP.1 QA process confirms adherence to the active `docs/pipeline/` standards.
4. **Known Limitations Approved:** Any known deviations or open non-critical issues (SUP.9) are explicitly approved by the Project Lead and documented in the Release Notes.
5. **Configuration Baseline:** The content matches precisely the SUP.8 configuration baseline without dirty worktrees.

**Approval Authority:** Final release authorization requires formal sign-off (`decision_request` APPROVED) from the **Project Lead**.

## 3. Package Assembly and Release Notes

The release package is assembled from controlled configuration items identified by the `git` release tag.
The **Release Notes** MUST explicitly state:
- New features and requirement IDs fulfilled.
- Defect fixes and corresponding SUP.9 problem ticket IDs.
- Known limitations, workarounds, and residual risks (from `man5-risk-register.md`).
- Applicable licenses and third-party attributions.

## 4. Delivery, Support, and Rollback

### 4.1 Delivery Mechanism
Releases are delivered via automated tag-triggered artifacts to a secure artifact registry. Delivery is verified by checksum validation upon upload.

### 4.2 Support and Service Level
Each release must define its support duration and service level (e.g., "Standard Support for 6 months, critical security patches only").

### 4.3 Rollback Plan
Every release deployment must include a validated rollback procedure. If a deployed release exhibits critical failures, the delivery mechanism must revert the target environment to the previous known-good `git tag` within the defined recovery time objective (RTO).

## 5. Release Record Retention

A permanent JSON release record MUST be retained in `docs/dossiers/releases/` capturing:
- Release ID, Date, and Approver.
- The Git SHA representing the exact baseline.
- Hash of the delivered artifact bundle.
- Support duration and rollback verification.
