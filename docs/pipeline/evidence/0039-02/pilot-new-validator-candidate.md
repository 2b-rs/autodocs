# Pilot P-001 — New Reusable Capability: Candidate Evidence Validator

**Status:** Process pilot only; not qualification, registration, deployment, or production use.

- **Need/baseline:** The prior workflow checked a process package manually against prose. It had no deterministic guard for a missing study binding, absent lifecycle control, or accidental prose that treated a candidate as deployed.
- **Candidate:** `_src/tools/validate_tool_creation_package.py`, a read-only validator with a closed JSON manifest and hermetic tests. Its exact intended profile is repository-source evidence validation only.
- **Safety comparison:** The baseline could omit a mandatory condition silently. The candidate rejects malformed study binding, missing control coverage, missing pilot shape, and `registered`/`deployed` pilot decisions. It has no network, credential, external, registry, or repository mutation path.
- **First-attempt success:** `1/1` representative package validation is recorded by the focused test run; this is a single pilot observation, not a performance claim.
- **Duration/retries/context/maintenance/evidence:** Active implementation time, retries, and token/context volume were not independently instrumented and are recorded as `unknown`; no retry occurred in the retained validation run. Maintenance is one small stdlib validator plus hermetic tests. Evidence is the manifest, reconciliation, two pilot records, test result, and process documents; no source-tree copy is retained.
- **Decision:** `rejected-pending-independent-review`. The candidate remains unregistered and unavailable to the typed-action dispatcher until a separately authorized independent review and registration decision.
- **Recovery:** A failure is a read-only finding; correct the evidence package and rerun. No effect needs rollback.
