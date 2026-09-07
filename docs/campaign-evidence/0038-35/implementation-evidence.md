# `0038-35` implementation evidence — Feature `0038` terminal integration candidate

- **Implementer:** `belanna`, Team Voyager, `privileged`, Implementer-only for this
  item; distinct from Architect `data` (contract author) and terminal Integrator
  `geordi`. No Acceptance, review, checkpoint verdict, `main` advance, `DONE.md`
  move, or Feature closure performed or claimed here.
- **Authority:** Project Lead `jean-luc`, direct assignment, agent-inbox
  `1787687738487-253e1d0f`, thread `0038-35`, 2026-08-25, under `DEC-0038-005`
  and the Architect contract
  `docs/campaign-evidence/0038-35/architect-terminal-integration-contract.md`.
- **Base:** `main@8a364e000fed6e826a1e7d49c4b1c014c849eece`, branch/worktree
  `0038-35` cut directly from that pin (no prerequisite branches to merge — all
  38 listed prerequisites are already `[x]`/`[w]` and reachable from `main` at
  this exact base, independently confirmed below).

## What this package is and is not

It is a **digest-bound description of the current state** of all 38 Feature
`0038` prerequisite work units, prepared so a separately assigned terminal
Integrator can perform the actual prerequisite-closed Acceptance batch,
Feature aggregate review, and closure. It is **not**:

- an Acceptance record for any of the 38 nodes,
- a review or re-review of `0038-33`/`0038-34` (those remain a separately
  assigned "fresh structured Task reviewer" step per the Architect contract),
- an integration verdict,
- a `TODO.md`→`DONE.md` move, or
- a judgment that the package is ready for closure. It is explicitly **not
  ready** — see Gaps below.

## Method

1. Independently confirmed all 38 prerequisite IDs against `TODO.md`'s own
   `0038-35` PREREQ list (exact string match, no transcription).
2. Parsed `TODO.md` directly (not only through `legacy_task_doctor.py`'s
   summarized title field, which only captures each node's first line) to
   extract each node's **complete block** — header through every sub-bullet,
   up to the next top-level task header — and computed its SHA-256.
3. Searched each block for all three known `Acceptance` record forms used in
   this repository (the canonical `**Acceptance:** ✓` contract form, the
   `**Acceptance: ✓**` bold-wrap variant, and the bare `Acceptance: ✓` form —
   all three are currently in live use across the backlog, a known rendering
   inconsistency this manifest does not attempt to normalize or fix).
4. Recorded every `REF: ...`-shaped token found in each block.
5. Cross-referenced known historical rejection records from this session's own
   direct work today (`0038-10`, `0038-31`, `0038-34` each carry at least one
   append-only rejected review in their history) and from repository search.

## Result: `docs/campaign-evidence/0038-35/aggregate-manifest.json`

38 nodes, all terminal (`[x]` or `[w]`). Full per-node digest/REF/Acceptance-form
table in the manifest; not duplicated here.

### Gaps — recorded, not repaired (fails closed per the Architect contract)

1. **8 of 38 nodes carry no `Acceptance` record in any form:** `0038-16`,
   `0038-16.02`, `0038-17`, `0038-22`, `0038-24`, `0038-25`, `0038-27`,
   `0038-28`. This blocks package eligibility until each receives current
   valid Acceptance under `task-acceptance.md` (or an explicit boundary
   decision by the terminal Integrator/reviewer).
2. **RESOLVED during this claim.** Fresh structured `0038-33`/`0038-34`
   Acceptance, as `DEC-0038-005` requires, was produced by `paul` while this
   manifest was being built (evidence `5b08608b0dada88e061ab8985c8f11e08cde21e9`,
   bookkeeping `3c2175e5290d1fe8590bdf4790236e39274a2c73`, branch
   `review-0038-33-34-paul-20260825T195800Z`). Both **accepted**. Independently
   verified before incorporating: both commits exist, this candidate's base
   (`8a364e000`) is a confirmed ancestor of the bookkeeping commit, and both
   review reports were read directly (not summarized secondhand) — see
   `docs/campaign-evidence/review-0038-33-34-paul-20260825/report-0038-33.md`
   and `report-0038-34.md`. Per Project Lead `jean-luc`'s explicit instruction
   (agent-inbox `1787688307131-b21ddfc9`), Paul's review branch is referenced
   here as data only and is **not merged** into this candidate branch — that
   git-level reconciliation is reserved for terminal Integrator `geordi`.
3. **`legacy_task_doctor.py --json` structural check reports 175 findings
   whose text mentions `0038`**, out of 776 repository-wide. A sample
   (`0038-30`) was manually cross-checked against the raw `TODO.md` text: the
   tool's "`Integration review` attribute lacks an `(architect)`-tagged
   Rationale" finding for that node is very likely a **pattern/formatting
   false positive** — an actual `Architect checkpoint decision: ... confirmed
   — mandatory` sub-bullet is present and reachable, just not in the exact
   inline-tag shape the tool's regex expects. This is reported as an
   observation, not adjudicated; the terminal reviewer should not treat every
   one of the 175 findings as a real gap without the same spot-check, nor
   dismiss all of them without checking.
4. **Full-repository `automation_safety.py --json` scan**, run fresh at this
   exact base: see `docs/campaign-evidence/0038-35/validation/automation-safety-full.json`
   for the complete, unfiltered output and the summary in the Validation
   section below.

## Validation run at this exact base

| Check | Command | Result |
|---|---|---|
| Structural backlog check | `python3 _src/tools/legacy_task_doctor.py --json` | 776 findings repo-wide (563 error / 212 warning / 1 info), 175 mention `0038`; see Gap 3 above and the raw output in `validation/legacy_task_doctor.json` |
| Automation-safety policy | `python3 _src/tools/automation_safety.py --json` | `verdict: FAIL`, `{advisory: 49, disposed_critical: 2, findings: 73, policy_errors: 66, unresolved_critical: 22}`. Spot-checked: policy errors are exclusively `owner_task 0038-16 is terminal; disposition expired` (the already-documented, pre-existing `0038-16`-closure disposition-expiry class, `AGENTS.md` suggestion log 2026-08-20); unresolved criticals are `AUTO001`/`AUTO005`/`AUTO008` in `bootstrap_instance.sh`/`provision_tmp_worktree.sh`, unrelated to any of the 38 `0038-35` prerequisites or this candidate's own changes. Full output: `validation/automation-safety-full.json`. |
| `git diff --check` | on this candidate | clean (rechecked before final commit) |
| `0038-33` focused suite | Reported by fresh reviewer `paul`: `python3 -m pytest _src/tests/test_automation_safety.py -q` → 125 passed; `automation_safety.py --path _src/tools/runner_transaction.py --json` → PASS 5/5 advisory, 0 unresolved. Not independently re-run by this Implementer claim (out of write scope; recorded as reported). |
| `0038-34` focused suite | Reported by fresh reviewer `paul`: `test_adversarial_evidence.py` 22/22; `automation_safety.py --path` → PASS 0 findings; `py_compile` clean; AE-8 projection exit 0. Not independently re-run by this Implementer claim (same reason). |

## Rollback / recovery

Before any integration: abandon this candidate branch (`0038-35`); `main`
remains untouched at `8a364e000`; all history stays reachable via the branch
ref and this evidence directory. No autonomous reset, force-push, or tag
deletion performed or required. After a rejected/inconclusive terminal review:
the finding is appended here or in a superseding evidence file; this record is
never rewritten.

## Expected root target

Per the Architect contract, the terminal Integrator alone advances `main` and
moves `TODO.md`→`DONE.md`, only after every gap above is closed and the
complete prerequisite-closed Acceptance batch (including fresh `0038-33`/
`0038-34` review) passes. No target SHA is asserted here since that closure
has not occurred and this package is not yet eligible.
