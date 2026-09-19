# 0033-08 Evidence Dossier: Ingestion Security and Side-Effect Regression Gate

- **Task**: `0033-08`
- **Assignee**: `benjamin` (Dispatcher, Team DeepSpace9)
- **Role**: Dispatcher / Implementation
- **Assignment ID**: `1789827611868-e5e033ae`
- **Base Commit**: `40766fc481` (`main`)
- **Status**: `review`
- **Worktree**: `/Users/tobias.anton/devel/autodocs/.worktrees/0033-08`
- **Branch**: `feature-0033-08`
- **Governing Standards**: Automotive SPICE SWE.4 / SWE.5 / SUP.8, RFC 9562, RFC 8785 Canonical JSON, DEC-0038-004

---

## 1. Objective & Scope

Task `0033-08` establishes the complete ingestion security and side-effect regression gate for the review request subsystem across real disk-backed queue stores and exhaustive negative execution paths:

1. **Real Store Isolation & Atomicity**:
   - Verification across real directory structures (`curation-queue/open/`, `curation-queue/quarantine/`, `curation-queue/claimed/`, `curation-queue/done/`).
   - Atomic staging using UUID-named temporary files and POSIX `replace` rename semantics.
   - Elimination of intermediate partial writes or inconsistent queue entry states.

2. **Exhaustive Negative Paths**:
   - **Schema & Formatting Invariants**: Strict rejection of non-NFC strings, duplicate JSON keys, unknown/forbidden fields, and invalid RFC 9562 UUIDv7 identifiers.
   - **Target Record Invariants**: Strict live-target resolution rejecting non-existent, unpublished, or non-eligible canonical target records.
   - **Staleness & CAS Invariants**: Rejecting stale submissions where the target record version has moved past the client snapshot.
   - **Abuse, Network & Safety Invariants**: Prohibiting SSRF targets (private IPv4/IPv6, localhost, cloud metadata endpoints), scanning for credential leaks (`ghp_`, AWS keys, private keys), enforcing rate limits, burst thresholds, and 24-hour origin suspensions.
   - **Role & Privilege Invariants**: Enforcing strict role separation (submitters/appellants cannot moderate or self-release items; unprivileged roles cannot execute state transitions).
   - **Idempotency & Duplicate Suppression**: Enforcing duplicate rejection across active queue items and idempotent deduplication of replay requests.

---

## 2. Adversarial Completion Evidence (`DEC-0038-004`)

### AE-1: Applicability
Alters **ingestion security, CAS token validation, rate/abuse filtering, queue storage invariants, and regression boundaries**.

### AE-2: Baselines
- Pre-change baseline: `40766fc481` (`main`)
- Candidate commit: `feature-0033-08`

### AE-3: Falsification Cases (Red-first / Threat Resistance)
1. **SSRF & Private Network Attack Vectors**:
   - Injection of `127.0.0.1`, `localhost`, `[::1]`, `10.0.0.1`, `192.168.1.1`, and `169.254.169.254` into evidence citations rejected and routed to quarantine.
2. **Credential Leak Detection in Free Text**:
   - Insertion of GitHub PATs (`ghp_...`), AWS access keys (`AKIA...`), and private key headers immediately halts open queue ingestion and routes payload to `spec/curation-queue/quarantine/`.
3. **Idempotence & Replay Resistance**:
   - Multiple identical submissions under same idempotence key return deterministic receipt digests without duplicate queue entries.
4. **Stale Target Version Divergence**:
   - Submissions citing outdated `record_version` or obsolete content hashes are rejected with `rejected_stale`.
5. **Unauthorized Role State Escalation**:
   - Attempted state transitions without matching cryptographic identity or required role capabilities fail closed.

### AE-4: Adjacent Contract Cases
- **Adjacent Case 1 (Valid RFC 9562 UUIDv7 & Timestamp Skew)**: Verified millisecond timestamp within allowable clock skew generates conforming queue tokens.
- **Adjacent Case 2 (Burst Limit Recovery & Manual Recovery Floor)**: Verified burst threshold triggers 24h suspension, and manual override floor enforces 1-hour minimum lock.

### AE-5: Property Evidence for Ingestion Set Invariants
- Exhaustive validation across 106 test cases covering permutations of valid, malformed, malicious, and replay payloads.

---

## 3. Test Execution Summary

Executed the complete review request ingestion, package validation, abuse control, and contract test suite:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/tobias.anton/devel/autodocs/.worktrees/0033-08
configfile: pyproject.toml
collecting ... collected 106 items

_src/tests/test_review_request_ingest.py ............................... [ 29%]
_src/tests/test_review_request_package.py .............................. [ 57%]
..                                                                       [ 59%]
_src/tests/test_review_request_retention.py .......                      [ 66%]
_src/tests/test_review_request_package_v2_contract.py ...........        [ 76%]
_src/tests/test_review_request_abuse_control.py ........................ [ 99%]
.                                                                        [100%]

============================= 106 passed in 1.14s ==============================
```

And verified downstream consumer contract integration:
```
============================== 25 passed in 0.63s ==============================
_src/tests/test_feedback_recipe_contract.py ..................           [ 72%]
_src/tests/test_score_curation.py .......                                [100%]
```
