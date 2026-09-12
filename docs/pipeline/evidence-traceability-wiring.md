# Evidence Traceability & Invalidation Architecture (Feature 0015-09)

## Purpose
This document establishes the architecture for wiring evidence snippets and tracking dependency edges in the Immutable Evidence Repository. It defines the mechanism for supersession and invalidation of dependent configuration items when upstream baselines change.

## 1. Evidence Dependency Edges
Every piece of collected evidence (e.g., a test result, a code review approval) must explicitly declare its dependencies via cryptographic hashes.
- **Upstream References:** A test result must declare the hash of the test specification it ran against, the runner script used, and the unit/component baseline under test.
- **Trace Graph:** These dependency declarations form a directed trace graph within the immutable store, distinct from the SWE requirement traces.

## 2. Supersession Triggers
When a new version of a configuration item (e.g., a Software Requirement or a Unit Detailed Design) is approved, it creates a supersession event.
- **Superseding Records:** The new item must include a `supersedes: [Hash]` metadata field linking it to the older version.
- **Graph Propagation:** The tooling must traverse the dependency graph and identify all downstream evidence (e.g., old test results, old architectural approvals) that relied on the superseded item.

## 3. Invalidation & Revisit Results
- **Suspect Flags:** All downstream evidence relying on a superseded item is automatically flagged as "suspect" or "invalidated".
- **Revisit Workflow:** The system must generate a Revisit Report identifying which tests need to be re-run, which code needs re-reviewing, and which architectural traces need to be confirmed against the new baseline.
- **Closure:** The suspect flag is cleared only when a new piece of evidence is appended to the ledger that traces to the *new* upstream hash. The invalidation and closure history must be retained in the Revisit Report for compliance auditing.

## 4. Controlled Stores Wiring
- **Writers:** Extraction and publication writers must enforce these rules before writing to the ledger. They must reject any evidence bundle that traces to an obsolete or unapproved baseline hash.
- **Publication Validation:** The final campaign publication must include the full dependency graph and assert that zero "suspect" flags exist in the current release candidate.
