# Pilot P-002 — Extension/Consolidation Assessment: Process Validators

**Status:** Process pilot only; no existing production validator is changed.

- **Baseline:** `validate_feature_definition_package.py` validates the separate Feature-definition process package. Before this assessment, a new process package would likely duplicate its study-binding, evidence-path, and reconciliation checks.
- **Assessment:** Preserve two semantic cores because their contracts differ (`feature-definition-evidence@v2` versus `tool-creation-evidence@v1`), but consolidate the lifecycle pattern: closed manifests, pinned informative-study digest, English reconciliation, focused hermetic negative tests, and candidate-only status. No generic validator or action wrapper is introduced.
- **Safety comparison:** The consolidation avoids a broad shared parser that could blur distinct authority boundaries. Both validators remain read-only and reject unresolved evidence. No network, credential, external effect, registry change, or production execution occurs.
- **First-attempt success:** `1/1` representative package validation is recorded by the focused suite; this is not a general success-rate claim.
- **Duration/retries/context/maintenance/evidence:** Timing and context were not independently instrumented and are `unknown`; no retry occurred in retained validation. Maintenance cost is explicitly retained as a future measure because two narrow validators require parallel updates if their shared lifecycle semantics change. Evidence volume is bounded to manifests, reconciliation, pilot records, and tests.
- **Decision:** `rejected-pending-independent-review`. The documented consolidation pattern does not register or deploy a shared action; an authority may later retain the split, authorize a carefully scoped shared library, or reject consolidation.
- **Compatibility/recovery:** Existing `0039-01` evidence and validator behavior are untouched. A finding here requires only process-package revision and rerun.
