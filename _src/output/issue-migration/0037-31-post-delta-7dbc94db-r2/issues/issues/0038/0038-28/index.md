---
schema_version: "1.0"
id: "0038-28"
level: "task"
parent: "0038"
state: "closed"
visibility: "internal"
prerequisites:
  - "0038-24"
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1915"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0038-28:0038-24 Re-verify and re-own the `runner-host/run-loop.sh` automation-safety dispositions after the host-package move. REF: `3a6e73620f52fb3e0faa54a53f2ccd250a044409`

## Scope

- **Claim:** `TODO-seven-mezoti-0038-28-20260821T125650Z.md` (`agent:seven-mezoti:0038-28:20260821T125650Z`, `unprivileged`, branch `0038-28` off `main` at `7b2e2ce99`).
  - **Origin (2026-08-21, architect `Seven-B'Ellana`, during the Feature 0038 → `main` integration):** `runner-host/run-loop.sh` carries 21 automation-safety dispositions whose evidence is current against `main`'s `0040-10`-remediated content, but whose owner (`0038-10`) became terminal at this integration and whose alternate owner (`0040-10`) ceased to exist when Feature `0040` moved to `DONE.md`. `_validate_dispositions()` requires a live, non-terminal `owner_task`, so the debt needs a real owner or the repo-wide gate fails for every agent. The re-pointing performed at integration was strictly mechanical — `path`, `owner_task`, `expires_after_task` only; every `line`, `rule`, `symbol`, `evidence_sha256`, `rationale`, and `expected_safe_invariant` was preserved byte-identical from `main`. **No finding was resolved, weakened, or hidden: the debt was relocated, not discharged.** This Task owns discharging it.
  - **Why Feature 0038:** the Feature owns the file (`runner-host/` was created by `0038-24`), owns the scanner and its policy schema (`0038-03`), and has the sibling precedent for exactly this work (`0038-27`). Feature 0038 remains open, so the schema's live-owner requirement is genuinely satisfied rather than papered over.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect `Seven-B'Ellana`, 2026-08-21):** the Task is bookkeeping over an existing, unchanged finding set; it grants no capability and touches no credential or publication path, and its correctness is fully mechanically checkable by re-running the scanner. Re-examined at this Task's own closure — a local, reachable trigger.
  - **Implementation completion (2026-08-21, `agent:seven-mezoti:0038-28:20260821T125650Z`, `unprivileged`):** All 21 `runner-host/run-loop.sh` dispositions re-verified against the current bytes at `7b2e2ce99` using the scanner's own finding tuple `(path, rule, line, symbol, evidence_sha256)` — the exact key `_validate_dispositions()` matches on. **Zero drift:** all 21 match; nothing needed refreshing. A naive single-line re-hash reports 8 mismatches (AUTO001+AUTO010 at lines 425/737/845/1130); those are precisely the four *aggregate* findings whose evidence is a multi-line `evidence_text` span rather than a source line, so they are a false alarm, not drift — both checks are recorded in the retained evidence so a later reviewer need not re-derive it. The line/evidence refresh `0040-10` owed was in fact delivered (`1164a9717`), and `0043-01`'s later edit (`6786bcc70`) touched no dispositioned span. **No `evidence_sha256` was altered:** the commit changes exactly three fields per entry — `rationale`, `owner_task`, `expires_after_task` — and `git diff` shows 21 -/+ pairs for those and **zero** for `evidence_sha256`, `line`, `symbol`, `rule`, `kind` and `expected_safe_invariant`. What was genuinely unresolved was the *justification*: ten `AUTO010` blocking-task entries deferred to Task `0038-10`, terminal (`[x]`, REF `4231f93b2`) and whose delivered scope was `runner_transaction.py`, never `run-loop.sh` — an unfalsifiable deferral. Each of the 21 rationales now names an individual accepted risk (no blanket suppression, no finding removed or downgraded; the SSH-key-initialization entry is deliberately kept a visible `blocking-task`), and the ten dead deferrals are redirected to the live successor: `0038-16.01`'s pre-activation handoff manifest into the `0037-46.01` typed-action queue. **Autonomous backlog repair, TK-2 flagged:** `owner_task`/`expires_after_task` re-pointed `0038-28` → `0038-16` instead of naming this Task, because the schema requires a live non-terminal owner and naming `0038-28` would expire all 21 entries the instant it is marked `[x]` — the third instance of that orphaning defect in this Feature. Follows the precedent set twice already under the identical constraint (`0038-27`/`sync_to_devel.sh`; `Seven-Tom`'s reconciliation of `provision_tmp_worktree.sh`), both to durable custodian `0038-16`, whose Definition of Done gates on "zero undispositioned critical chore findings remain". `0038-28` remains the Task that discharged the debt. The underlying schema gap (no evidence-anchored permanent disposition kind — standing `AGENTS.md` suggestion of 2026-08-20) is deliberately not fixed here; it is its own Task. **Validation:** `python3 _src/tools/automation_safety.py --json` → `verdict: PASS`, `policy_errors: 0`, `unresolved_critical: 0`, `disposed_critical: 24`, with all 21 `run-loop.sh` findings individually dispositioned; `python3 -m unittest _src.tests.test_automation_safety` 120/121 — the single failure is on `_src/tools/runner_transaction.py` (`AUTO010`), pre-existing and out of write scope, already recorded verbatim in `0038-27`'s completion note. Retained evidence: `docs/pipeline/fixtures/0038-28/reverification.json` + `README.md`. Substantive commit `3a6e73620f52fb3e0faa54a53f2ccd250a044409` on branch `0038-28` (based off `main` at `7b2e2ce99`); branch left at rest, not merged. Claim `TODO-seven-mezoti-0038-28-20260821T125650Z.md` travels on the branch. No acceptance credit claimed.


### Campaign E — Adopt once, then hand off cleanly

## Acceptance criteria

- **AC-001** Re-verify all 21 dispositions against the current bytes of `runner-host/run-loop.sh` — line numbers, symbols, and `evidence_sha256` — and refresh any that drifted, recording what changed and why. Each genuinely unresolved finding either gets its code remediated or keeps an individually justified disposition naming its accepted risk
- **AC-002** no blanket suppression. Confirm no disposition's `evidence_sha256` was altered merely to make the gate pass

## Definition of Done

Committed with a real `REF`; `python3 _src/tools/automation_safety.py --json` reports zero policy errors with every remaining finding individually dispositioned or remediated; the re-verification evidence is retained.
