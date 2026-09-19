# 0033-06 Evidence Dossier: Authoritative Live-Target Resolution & Trusted-Transport Verification

- **Task**: `0033-06`
- **Assignee**: `benjamin` (Dispatcher, Team DeepSpace9)
- **Role**: Dispatcher / Implementation
- **Base Commit**: `d55c146dd2` (`main`)
- **Status**: `review`
- **Worktree**: `/Users/tobias.anton/devel/autodocs/.worktrees/0033-06`
- **Branch**: `feature-0033-06`

---

## 1. Objective & Scope

Implement authoritative live-target resolution and approved trusted-transport verification that cannot be bypassed by optional caller arguments, addressing baseline audit findings:
- **`RRB-INGEST-001`**: Live-target verification against authoritative `spec/records/` and `spec/versions/` stores before any queue write; caller-supplied arguments cannot bypass, forge, or substitute live store values.
- **`RRB-TRUST-001`**: Structured transport envelopes and cryptographic/API verification replace bare caller actor strings and client-authored 'verified' fields.

---

## 2. Implementation Summary

1. **Authoritative Live-Target Lookup (`resolve_live_target`)**:
   - Resolves target canonical record against approved `spec/records/` and `spec/versions/` filesystem stores.
   - Enforces record eligibility (e.g. `valid/published`, `valid/auto-approved`, `valid/ai-decided`, `valid/curator-decided`) and rejects non-eligible states (`invalid/draft`, `invalid/quarantined`).
   - Mints authoritative `target_token` with canonical SHA-256 hash for downstream atomic compare-and-set queue writes.
   - Detects hard-stale conditions (both version ID and content hash mismatch) and emits warnings for soft-stale mismatches.
   - Enforces `PROC-0033-02-03` (null-version submissions on versioned records are rejected).

2. **Trusted Transport Verification**:
   - **GitHub Webhook HMAC SHA-256 (`verify_github_webhook_hmac`)**: Constant-time signature comparison (`hmac.compare_digest`), rejecting missing, malformed, or tampered signatures.
   - **GitHub API Refetch (`verify_github_api_refetch`)**: Refetches Issue details via authorized API installation adapter, verifying author login and repository allowlisting against `DEFAULT_ALLOWED_REPOSITORIES`.
   - **Local Import (`LOCAL_ENVELOPE_KIND_V1`)**: Always forced to `self_declared` identity; cannot assert `github_authenticated`.
   - **Spoofed Trust Rejection**: Any submission attempting to assert verified trust without verified envelope evidence is rejected with `REJECTED_SPOOFED_TRUST`.

3. **Replay & Tampering Protection (`ReplayTracker`)**:
   - Tracks `delivery_id` and `event_id` mappings against canonical package digests.
   - Distinguishes exact idempotent replays from payload tampering / conflicting payload redeliveries.

4. **Package V2 and Concern Key Alignment**:
   - Implemented `concern_key_preimage` and `compute_concern_key` supporting both v1 and v2 schemas (`review-request-concern@v1`).
   - Validated against pinned vectors in `_src/tests/fixtures/review_request_v2/canonical-vectors.json`.

---

## 3. Adversarial Completion Evidence (`DEC-0038-004`)

### AE-1: Applicability
This substantive change alters **identity matching** (authoritative live-target verification, repository allowlisting, author verification), **blocking/gate classification** (rejection of unknown/ineligible/stale targets, spoofed trust, tampered HMAC signatures, replay conflicts), and **serialization shape / concern projection** (`review-request-concern@v1`).

### AE-2: Baselines
- Pre-change baseline: `d55c146dd2` (`main`)
- Candidate commit: `feature-0033-06` (`3c49df421` + dossier commit)

### AE-3: Falsification Cases (Red-first on Baseline / Green on Candidate)
1. **Bypass Resistance (`test_forged_caller_arguments_cannot_bypass_live_resolution`)**:
   - In pre-change baseline without authoritative lookup, a caller could pass arbitrary `current_content_hash="forged99"` to bypass store validation.
   - On candidate, caller arguments are overridden by the authoritative filesystem store lookup (`3f9a21bc`), producing `target_token` matching the true live store and issuing a warning.
2. **Cryptographic HMAC Tampering (`test_github_webhook_sha256_profile_invalid_signature_rejected`)**:
   - Webhook payloads with modified bodies or bad signatures fail HMAC verification and return `REJECTED_UNTRUSTED_TRANSPORT`.
3. **Spoofed Trust (`test_spoofed_trust_claim_over_json_export_rejected`)**:
   - Unauthenticated JSON export asserting `github_authenticated` actor is rejected as `REJECTED_SPOOFED_TRUST`.

### AE-4: Adjacent Contract Cases
- **Adjacent Case 1 (`test_unknown_target_record_rejected_without_queue_write`)**:
  - Dimension: Non-existent canonical record ID (`AUTOSAR/AP/record/unknown-nonexistent-element`).
  - Expected: Ingestion rejected with `REJECTED_UNKNOWN_TARGET`, zero queue writes.
  - Observed: Correct rejection, open queue remains empty.
- **Adjacent Case 2 (`test_ineligible_record_status_rejected`)**:
  - Dimension: Target record exists but has state `invalid/draft`.
  - Expected: Ingestion rejected with `REJECTED_INELIGIBLE_TARGET`, zero queue writes.
  - Observed: Correct rejection, open queue remains empty.
- **Adjacent Case 3 (`test_obsolete_version_and_hash_rejected_as_stale`)**:
  - Dimension: Target record was updated to newer release/hash (`R26-03` / `deadbeef`).
  - Expected: Ingestion rejected with `REJECTED_STALE`, zero queue writes.
  - Observed: Correct rejection, open queue remains empty.
- **Adjacent Case 4 (`test_replay_protection_replayed_delivery_id_with_modified_payload_rejected`)**:
  - Dimension: Same `delivery_id` sent with a different package payload.
  - Expected: Ingestion rejected with `REJECTED_TAMPERING` / `conflict`.
  - Observed: Correct rejection, replay tracker flags conflicting payload digest.

### AE-5: Property Evidence for Set / Sequence
- Replay tracker invariant: Exact identical redeliveries (`delivery_id` + identical `package_sha256`) succeed idempotently (`idempotent_replay`), whereas mismatched digests under the same `delivery_id` are unconditionally rejected as `conflict`.

---

## 4. Test Execution & Verification

Executed test suite:
```bash
pytest _src/tests/test_review_request_package.py _src/tests/test_review_request_package_v2_contract.py _src/tests/test_review_request_ingest.py
```
Output:
```
============================== 74 passed in 0.48s ==============================
```
Total: 74 passed, 0 failed, 100% OK.
