# Work Product Controls & Configuration Management (Feature 0015-02)

## Purpose
This document defines the controls for all work products across the ASPICE lifecycle (SUP.8). It guarantees that each work product is properly identified, versioned, stored, and managed according to its type, sensitivity, and retention requirements.

## 1. Identification & Versioning
Every configuration item (work product) must be uniquely identifiable.
- **Identifier format:** `[Project/Component]-[Type]-[ID]` (e.g., `AUTODOCS-REQ-001`).
- **Versioning:** Semantic versioning or sequential revision integers must be applied. Every change must increment the version and be logged in the provenance graph.
- **Baselining:** A baseline is a frozen, immutable set of specific versions of work products. Modifying a baseline requires formal Change Request (SUP.10) approval.

## 2. Status Accounting
Work products transition through defined states:
- **Draft:** Under active development; incomplete.
- **In Review:** Submitted for formal review.
- **Approved:** Passed review and frozen.
- **Released:** Distributed for internal/external use.
- **Archived/Disposed:** Retained for historical purposes but no longer active.

## 3. Review & Approval
Each work product type specifies its required review path (e.g., peer review, QA audit, architect approval).
- **Quality Requirements:** Checklists or static analysis gates must be cleared before transitioning to `Approved`.
- **Signatures:** Reviews must log the actor, timestamp, criteria checked, and explicit `PASS/FAIL` decision.

## 4. Access, Storage & Distribution
- **Storage:** All authoritative records reside in the distributed Git ledger (`issue-store` and `provenance`).
- **Access Controls:** Read access is distributed, but write/merge access to the canonical repository is restricted to authorized roles (e.g., Integrators).
- **Distribution:** Only `Approved` or `Released` work products may be distributed (e.g., via generated static HTML reports).
- **Backup & Recovery:** The distributed nature of the repository ensures inherent backup; central remotes are backed up daily.

## 5. Sensitivity & Licensing
- **Sensitivity Controls:** Work products containing proprietary data, secrets, or sensitive PII must be scrubbed before integration or restricted to private, secure vaults (separate from public provenance).
- **License:** All external distributions must carry the designated open-source or commercial license headers.

## 6. Retention, Archival & Disposal
- **Retention:** Evidence, reviews, and artifacts must be retained for at least the operational life of the product release + 10 years (or as mandated by legal compliance).
- **Archival:** Deprecated work products are marked `Archived` but their cryptographic hashes remain in the ledger to preserve integrity.
- **Disposal:** Physical disposal or data wiping is performed only when legally mandated, ensuring keys and sensitive contents are permanently destroyed while leaving tombstone records in the provenance log.
