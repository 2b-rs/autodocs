# SPL.2 Product Release Content, Criteria, and Delivery Specification (0016-06)

## 1. Scope & Purpose
- **Process ID**: `SPL.2` (Product Release)
- **Feature / Task**: `0016-06` (PREREQ: `0015-03`, `0015-07`)
- **Governing Standard**: Automotive SPICE `SPL.2`
- **Objective**: Define requirements for product release content, identification, approval criteria, package assembly from controlled items, release notes, limitations, licenses, and rollback mechanisms.

---

## 2. Release Identification & Packaging Requirements
- **Release Content Structure**:
  1. *Binary Artifacts / Executables*: Pinned, hashed software packages compiled from audited baseline commits.
  2. *Release Notes & Metadata*: Detailed changelog linked to `SUP.10` CRs and `SUP.9` PRBs, versioning metadata, build toolchain hashes.
  3. *Known Limitations & Workarounds*: Documented unresolved non-blocking anomalies and environmental constraints.
  4. *License & Compliance Bundle*: Explicit software licenses (e.g. Apache-2.0), third-party notices, and BOM inventory.
  5. *Support & Service Level Contract*: Support tier, maintenance duration, and security patching lifecycle.

---

## 3. Eligibility, Approval Gates & Delivery
- **Release Eligibility Criteria**:
  - Full qualification battery (`SWE.6`) passes at 100%.
  - Zero open Critical (NC-1) or Major (NC-2) nonconformances in `SUP.1`.
  - Complete configuration audit under `SUP.8` confirms baseline integrity.
  - Release readiness review sign-off by Project Lead (`jadzia`), QA Lead (`jake`), and Software Architect (`kira`).
- **Delivery & Rollback Procedures**:
  - Releases are packaged into atomic, immutable tarballs with accompanying SHA-256 digest manifests.
  - Rollback procedures specify deterministic restoration of the previous approved release baseline within defined operational timeframes.
