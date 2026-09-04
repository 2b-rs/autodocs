# Claim: 0037-30 frozen feedback test compatibility

- item: `0037-30-frozen-feedback-test-compat`
- owner: `data`
- owner_token: `agent:data:0037-30-frozen-feedback-test-compat:1788479790003-bb94e52d`
- capability_class: `privileged`
- execution_authority: bounded direct-local test-only implementation
- assignment: `1788479790003-bb94e52d`
- branch: `0037-30-frozen-feedback-test-compat-data-20260904`
- worktree: `/tmp/autodocs-worktrees/0037-30-frozen-feedback-test-compat-data`
- base: `5220d9fdb51a7f3067fa749f1c4415df1fab62e8`
- canonical_main_at_award: `0e7aa8fe37`
- write_scope: `_src/tests/test_review_request_ingest.py`, `TODO-data-0037-30-frozen-feedback-test-compat-20260904.md`
- state: `implementation_complete`

## Contract and evidence

- Atomic award `1788479790003-bb94e52d` requires the existing positive feedback-ingest case to use a hermetic `legacy-writable` selector, and requires bounded proof that `legacy-frozen` rejects with a stable selector incompatibility error without mutating records, versions, or queue state.
- Production code, the selector, Wesley's candidate, root/main, backlog markers, integration, publication, and ref cleanup are excluded.
- Red control on exact base `5220d9fdb51a7f3067fa749f1c4415df1fab62e8`: focused test fails at line 664 because observed `rejected_selector_mismatch` differs from expected `ok`.
- Green validation: the focused integration case passes 1/1, and the complete `_src/tests/test_review_request_ingest.py` module passes 31/31. The positive case uses a hermetic `legacy-writable`/`runner-request@v1` selector; the adjacent frozen probe asserts the exact incompatibility error and unchanged record, version-store, and queue bytes.
