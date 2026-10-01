# Campaign Manifest Segregation & Publishing (Feature 0015-05)

## Purpose
This document establishes the architecture for safely wiring lifecycle data (requirements, validations, campaigns) into the extraction and publication systems. Crucially, it defines the strict segregation between synthetic test fixtures and production configuration items (SUP.8).

## 1. Segregation of Synthetic Fixtures
- **Production Stores:** The main repository ledgers (e.g., `provenance/`) must exclusively contain production data—approved requirements, real campaign results, and verifiable code.
- **Synthetic Environments:** All testing fixtures, mock campaign manifests, and synthesized requirement datasets used for CI validation must be completely segregated. They must only exist in isolated paths (e.g., `_src/tests/fixtures/`) and must never be committed to production stores or included in a release baseline.

## 2. Append-Only Requirement Versions
- When requirements are ingested or updated by extraction writers, they must be recorded as **append-only versions**.
- An update to a requirement does not overwrite the old version; it creates a new uniquely identified configuration item (e.g., `REQ-001-v2`), preserving the audit trail of what was reviewed and approved previously.

## 3. Campaign Manifests in Publication
- The release/publication pipeline must read from the controlled, immutable campaign manifests.
- **Extraction Writers:** Scripts extracting data from source/tests into campaign manifests must write deterministically and include content hashes.
- **Validation Gates:** Before any manifest is written to the production store, it must pass schema validation ensuring no unapproved synthetic data has leaked into the production domain.

## 4. Uniquely Reproducible Baselines
- Integrating append-only requirements and validated campaign data enables uniquely reproducible release publication. If a baseline is regenerated, the writers will deterministically produce the exact same extraction results because the inputs (requirements, code, campaigns) are perfectly versioned and immutable.
