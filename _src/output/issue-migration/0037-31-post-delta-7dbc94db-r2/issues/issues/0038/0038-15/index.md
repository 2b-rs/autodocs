---
schema_version: "1.0"
id: "0038-15"
level: "task"
parent: "0038"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-37"
  - "0038-03"
  - "0038-09"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1862"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
  - id: "AC-005"
    status: "active"
  - id: "AC-006"
    status: "active"
---

## Goal

PREREQ: 0038-15:0038-03, 0038-15:0038-09, 0038-15:0037-37 Productize approval-readiness checks without mutating live policy by default. REF: `f818542c6`.

## Scope

- **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0038-15-Commit)`). Abgenommene Baseline `f818542c6`; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. 43/43 eigene Tests am eigenen REF.
  - **Closure (2026-08-20):** Rewrote `_src/tools/manage_approval_readiness.py`: no-arg invocation now defaults to safe read-only `--check --json`; each policy JSON file's `schema` field is pinned and checked (stale/missing => `BLOCKED`); the former in-place `authorities.json` mutation is replaced by `--propose-authorities-patch`, which only writes a reviewed candidate + unified diff under git-ignored `output/approval-readiness/` and never touches tracked policy; a new `capability` field (`metadata`/`verified`/`unavailable`) distinguishes bare presence from independently recomputed/cross-checked SSH fingerprints (matches real `ssh-keygen -lf` output); `revoked` entries are excluded from coverage; no check ever prints a configured signing-key path. Added `_src/tests/test_manage_approval_readiness.py` (43 tests) covering all eight required fixture categories (ready, missing role, wrong fingerprint, stale policy, unavailable handle, absent service control, revoke, malformed policy) plus fingerprint-computation, parsing, and non-mutation tests. Updated `docs/pipeline/issue-approval-setup.md` Steps 4 and 7 to match. Removed the now-stale `automation_safety_policy.json` disposition entry (`owner_task: 0038-15`) for the finding this closure fixes. Validation: `py_compile` OK; `python3 -m unittest _src.tests.test_manage_approval_readiness` — Ran 43 tests, OK; `python3 _src/tools/automation_safety.py --path _src/tools/manage_approval_readiness.py --json` — PASS, `unresolved_critical: 0` (was 1). Prerequisite `0037-37` is still `[p]` in TODO.md under another session's active claim, though its declared deliverables are already committed at REF `927da0690a964249f7ca0b83719601b849be801f` plus later policy commits — recorded as evidence rather than altered, since that Task/claim was outside this Task's write scope. Did not add a cross-reference note to `0037-07`'s acceptance-criteria text: the dispatching briefing's explicit write-scope statement restricted `TODO.md` edits to this entry only; a proposed one-line addition is recorded in the claim file for a session with `0037-07` in scope to apply. Flagged as a candidate for follow-up privileged Security Engineer review given the credential/approval-adjacent surface. Claim: `TODO-seven-talia-0038-15-20260820T024218Z.md`.

### Campaign F — Branch-based Task carriage and Feature integration

## Acceptance criteria

- **AC-001** Test and catalog `_src/tools/manage_approval_readiness.py`
- **AC-002** require policy schema versions
- **AC-003** make read-only JSON check the default
- **AC-004** replace in-place authority patching with reviewed candidates/diffs
- **AC-005** distinguish metadata presence from verified signer/remote/service/credential capability
- **AC-006** and never expose private key paths or claim readiness from prose-only records

## Definition of Done

Ready, missing role, wrong fingerprint, stale policy, unavailable handle, absent service control, revoke, and malformed policy fixtures pass with stable rules; Task `0037-07` consumes verified readiness rather than rediscovering setup manually.
