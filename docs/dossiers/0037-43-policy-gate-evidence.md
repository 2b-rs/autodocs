# Feature 0037 Task 0037-43: Integration-Policy Gate Verification & Non-Bypass Evidence

## I43-BLOCK-004 additive repair

- Authorized repair base: `dc0acb2e497a63d30be31e0439ae8731d5ec9749`.
- The base remains a transparent rejected intermediate; this repair claims no
  retroactive approval. Signed incident record: `e1f32379f` on the retained
  recovery branch.
- The gate now requires explicit immutable base and candidate refs, resolves
  both commits, proves ancestry, and derives paths only from that boundary.
- Only the exact legacy-writable v1 tuple admits the known all-`a`
  transitional digest. Every other mismatch or placeholder rejects.
- V2 requires the canonical phase, version, direct execution model, capability,
  bundle path, complete member map, and selector digest, checked against
  candidate bytes through the shared bootstrap bundle walker.

## 1. Executive Summary & Governance
Task `0037-43` provisions and proves a non-bypassable integration-policy gate before migration freeze in accordance with `DEC-0037-002`, `DEC-0044-014`, and resolved Management decision `decision-0037-43-hosted-enforcement-20260903` (receipt on `main@5357e0af0f1647897fd18ddf41c640f91c805735`).

## 2. Temporary Local / No-Push Exception (`temporary_local_no_push`)
Per Architect review and Management decision `decision-0037-43-hosted-enforcement-20260903`:
- Remote repository-hosting administrator access is unavailable in the execution environment.
- In accordance with the accepted `temporary_local_no_push` exception:
  1. No remote hosted branch-protection rules or bypass disabling are claimed or asserted on the hosting remote.
  2. Integration policy enforcement operates strictly locally via assigned-integrator-only `main` advance verification, `_src/tools/issue_integration_policy.py`, and CI workflow `.github/workflows/issue-policy.yml`.
  3. Direct push and external publication are prohibited until remote administrative access is established and formal hosted policy enforcement is configured.
  4. This exception expires prior to any public release or remote push.

## 3. Implemented Components & Strict Selector Contract (I43-BLOCK-002 / I43-BLOCK-003 Resolution)
- **Integration Policy Gate**: `_src/tools/issue_integration_policy.py`
  * Strictly validates `agent-workflow.json` schema (`agent-workflow-bootstrap@v1` / `v2`) and required fields without loose defaults.
  * Rejects all placeholder, sentinel, all-identical, or mismatched selector digests.
  * Validates `authority_profile`, `authority_epoch`, `write_phase`, and instruction bundle consistency (source, digests, members).
  * Accepts only supported profile/phase combinations: `(legacy-lists, legacy-writable)`, `(legacy-lists, frozen)`, `(legacy-lists, legacy-restored)`, `(issue-store, issue-store-writable)`, `(issue-store, write-frozen)`.
  * Requires explicit valid base+candidate boundary and rejects derivation failure without fallback.
  * Rejects direct modifications to generated backlog views (`TODO.md`, `DONE.md`) and legacy claim files (`TODO-*.md`) under `issue-store` profile.
  * Enforces fail-closed behavior (exit 1 on rejection across human CLI and `--json` invocations).
- **Workflow Protection Gate**: `.github/workflows/issue-policy.yml`
  * Executes `_src/tools/issue_integration_policy.py --root . --base ${{ github.event.pull_request.base.sha || 'main' }}` on PRs and pushes to `main` and `0037-*`.
- **Automated Adversarial Test Suite**: `_src/tests/test_issue_integration_policy.py`
  * 9/9 unit and subprocess tests verifying conforming changes, schema rejections, phase contradictions, placeholder/mismatched digest rejections, boundary derivation rejections, generated view rejections, claim rejections, and CLI exit codes.
