# Task `0038-28` — re-verification evidence for the `runner-host/run-loop.sh` dispositions

Retained under the Definition of Done of Task `0038-28` ("the re-verification
evidence is retained"). Companion data: [`reverification.json`](reverification.json).

## What was re-verified

All **21** `runner-host/run-loop.sh` dispositions in
`_src/tools/automation_safety_policy.json`, against the current bytes of
`runner-host/run-loop.sh` at commit `7b2e2ce99` — after Task `0038-24` moved the
file out of `_src/`.

## Method

`_src/tools/automation_safety.py` derives a finding's `evidence_sha256` either from
the single source line (`_source_evidence`) or, for aggregate findings, from an
explicit multi-line `evidence_text` span (`_evidence_digest`).
`_validate_dispositions()` then matches a disposition on the exact tuple
`(path, rule, line, symbol, evidence_sha256)`.

A naive line-by-line re-hash is therefore **not** a valid check: it reports false
mismatches on every aggregate entry. Both checks were run and both are recorded in
`reverification.json`:

| check | result |
|---|---|
| naive single-line re-hash | 8 apparent mismatches (AUTO001+AUTO010 at lines 425, 737, 845, 1130) |
| authoritative match against live scanner findings | **21 / 21 match, 0 drifted** |

The 8 apparent mismatches are exactly the four aggregate findings whose evidence is
a multi-line span. They are recorded explicitly so a later reviewer does not
re-derive the same false alarm.

## Result

- **Zero drift.** No `line`, `symbol` or `evidence_sha256` needed refreshing. The
  refresh that Task `0040-10` owed was in fact delivered (`1164a9717`), and the
  later `0043-01` edit (`6786bcc70`) did not touch any dispositioned span.
- **Zero evidence digests altered by this Task.** `git diff` on
  `_src/tools/automation_safety_policy.json` shows no `evidence_sha256`,
  `line`, `symbol`, `rule` or `expected_safe_invariant` change — so no finding was
  silenced by rewriting its evidence to make the gate pass. Only `rationale`,
  `owner_task` and `expires_after_task` changed.

## What was actually discharged

The evidence was already sound; the **justifications** were not. Ten `AUTO010`
`blocking-task` entries deferred to Task `0038-10`, which is terminal and whose
delivered scope was `_src/tools/runner_transaction.py`, never `run-loop.sh` — an
unfalsifiable deferral. Each of the 21 rationales now carries a dated,
individually named accepted risk, and the ten dead deferrals are redirected to the
live successor (`0038-16.01`'s handoff manifest → the `0037-46.01` typed-action
queue). No blanket suppression was used; no finding was removed.

Custodian `owner_task`/`expires_after_task` moved `0038-28` → `0038-16`, matching
the precedent already set for `sync_to_devel.sh` and `provision_tmp_worktree.sh`.
Naming `0038-28` itself would expire all 21 entries the moment this Task closes and
break the repo-wide gate — the very defect the Task exists to end. See
`docs/pipeline/automation-safety.md` for the disposition model, and the standing
`AGENTS.md` suggestion of 2026-08-20 for the underlying schema gap (no
evidence-anchored permanent disposition kind), which is deliberately **not** fixed
here.
