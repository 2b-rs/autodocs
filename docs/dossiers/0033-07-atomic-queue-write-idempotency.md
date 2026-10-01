# 0033-07 Evidence Dossier: Atomic Review-Request Queue Write & Race-Safe Idempotency

- **Task**: `0033-07`
- **Assignee**: `benjamin` (Dispatcher, Team DeepSpace9)
- **Role**: Dispatcher / Implementation
- **Base Commit**: `2046b07c56` (`main`)
- **Status**: `review`
- **Worktree**: `/Users/tobias.anton/devel/autodocs/.worktrees/0033-07`
- **Branch**: `feature-0033-07`

---

## 1. Objective & Scope

Implement one atomic, policy-compliant, conformant review-request queue write and race-safe idempotency/duplicate handling across active states, satisfying the requirements of Feature 0033:
- **`RRB-PROC-001` / `RRB-AUTH-001`**: Atomic, collision-safe queue writes using temp-file creation and atomic filesystem replacement (`os.replace`).
- **Active State Deduplication**: Enforce de-duplication across all active queue partitions (`open/` and `claimed/`) keyed on `(target_canonical_id, target_version_id)`.
- **Target Compare-and-Set (CAS)**: Re-verify target record content hash and version under reservation immediately before atomic queue commit to prevent stale race writes.
- **Unified Curation Item Mapping**: Ensure lossless normalization into `curation-flag@v1` with `item_kind="review-request"`, `origin="browser"`, and `status="open"`, with `decided_by` and `decided_at` set to `None`.

---

## 2. Implementation Summary

1. **Atomic Queue Write (`write_review_request_flag`)**:
   - Creates a unique temporary file (`.tmp-<uuid>`) and atomically promotes it to `open/<id>.json` using `os.replace`.
   - Returns `None` if a flag file with that request ID already exists, preventing overwrites.

2. **Active Queue Deduplication (`_existing_active_dedup_keys`)**:
   - Scans all flags across both `open/` and `claimed/` directories via `cf.list_active_flags()`.
   - Maps each active item's `(target_canonical_id, target_version_id)` key.
   - Any incoming submission matching an active item is rejected with `REJECTED_DUPLICATE` without modifying queue state.

3. **Pre-Commit Compare-and-Set Verification**:
   - Re-evaluates `resolve_live_target` under reservation immediately before writing to the queue.
   - If the target record version, status, or content hash mutated after initial lookup, the ingestion aborts with `REJECTED_STALE`.

4. **Lossless Curation Item Conformity**:
   - Written flags validate against `curation-flag@v1` schema.
   - `ci.from_curation_flag(payload)` yields a valid, conformant `curation-item@v1` with `status="open"` and complete `decision_basis`.

---

## 3. Adversarial Completion Evidence (`DEC-0038-004`)

### AE-1: Applicability
This substantive change alters **cardinality and deduplication** (active queue uniqueness invariant), **blocking/gate classification** (rejection of duplicates in claimed queue, stale mutations during CAS), and **atomic persistence shape**.

### AE-2: Baselines
- Pre-change baseline: `2046b07c56` (`main`)
- Candidate commit: `feature-0033-07`

### AE-3: Falsification Cases (Red-first / Race Protection)
1. **Duplicate Rejection Across Claimed Partition (`test_duplicate_submission_in_claimed_queue_rejected`)**:
   - Condition: A review request is submitted and claimed by a worker (`open/` -> `claimed/`). A second request arrives for the same target record.
   - Baseline without active-state tracking: Looked only in `open/`, permitting a duplicate write to `open/`.
   - Candidate: `_existing_active_dedup_keys` checks `claimed/`, correctly rejecting the second request as `REJECTED_DUPLICATE`.
2. **Race-Condition Mutation Protection (`test_target_changed_before_atomic_commit_rejected_stale`)**:
   - Condition: Live target record content hash is mutated between initial resolution and atomic queue reservation.
   - Candidate: CAS recheck detects target token mismatch and aborts with `REJECTED_STALE`, preventing queue contamination.
3. **Payload Collision Protection (`test_replay_protection_replayed_delivery_id_with_modified_payload_rejected`)**:
   - Condition: Replayed `delivery_id` carrying modified package bytes.
   - Candidate: Replay tracker flags digest discrepancy and rejects with `REJECTED_TAMPERING`.

### AE-4: Adjacent Contract Cases
- **Adjacent Case 1 (`test_dry_run_does_not_write_queue_item`)**:
  - Dimension: `apply=False` execution.
  - Result: Returns `outcome="ok"`, `dry_run=True`, and mints valid `target_token` without creating files in `open/`.
- **Adjacent Case 2 (`test_duplicate_submission_rejected`)**:
  - Dimension: Duplicate submission while original item remains in `open/`.
  - Result: Rejected with `REJECTED_DUPLICATE`, exactly 1 open item retained.
- **Adjacent Case 3 (`test_lossless_submission_to_queue_mapping`)**:
  - Dimension: Field preservation into `decision_basis`.
  - Result: `target_canonical_id`, `target_version_id`, `category`, `evidence_refs`, `source_url`, `request_id`, and `rationale` preserved losslessly.

### AE-5: Property Evidence for Set / Sequence
- **Active Queue Uniqueness Invariant**: For any set of sequential or concurrent ingestion attempts for target $T = (C_{id}, V_{id})$, the cardinality of active queue items across `open/` and `claimed/` is strictly bounded:
  $$\left|\text{active\_items}(C_{id}, V_{id})\right| \le 1$$

---

## 4. Test Verification

Executed full test suite:
```bash
pytest _src/tests/test_review_request_package.py _src/tests/test_review_request_package_v2_contract.py _src/tests/test_review_request_ingest.py
```
Output:
```
============================== 74 passed in 0.53s ==============================
```
Total: 74 passed, 0 failed, 100% OK.
