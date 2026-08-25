# Checkpoint review — Task `0038-30` (mandatory Integration review)

- **Reviewer:** `belanna`, Integrator, Team Voyager, `privileged`
- **Assignment:** Kathryn (Project Lead), agent-inbox `1787666620976-704b6125` (measurement +
  request), thread `0038`, 2026-08-25; coordination handed to Jean-Luc mid-review
  (agent-inbox `1787670676549-1cb714e0`), scope/authorization unchanged.
- **Independence:** reviewer authored none of the implementation commits reviewed below.
  Git authorship is not usable for independence in this repository (shared configured
  identity); independence is established via claim/owner-token records, all of which name
  implementers distinct from this review.
- **Item:** `0038-30`, "Narrow the legacy handoff manifest's activation precondition from
  'registry exists' to 'queue is live'", `Integration review: mandatory` (Architect `seven`,
  2026-08-24, downgrade recommendation explicitly declined). Product REF `f6789e512`
  (2026-08-22) — **no dedicated branch**; already an ancestor of `main` at review start
  (confirmed by Kathryn, agent-inbox `1787667196928-cf3d3bd8`, independently re-confirmed
  here).
- **Target:** `main` @ `6a937f8414440cc84233954012ff802eaf57924c` (self-measured).

## Why a batch, not just one node

`python3 _src/tools/legacy_task_doctor.py --json` against `main@28d7a0091` reported
`unaccepted_checkpoints: ['0038-30', '0038-32', '0038-33']` for Feature `0038`. Individually
verified: `0038-32` and `0038-33` already carry substantively real, independently reviewed
`accepted` dispositions, only in a non-canonical record form the gate's regex
(`\*\*Acceptance:\*\*\s*✓`) does not recognize — a rendering defect, not a review gap.
`0038-30` carries **no** acceptance record in any form: real gap. Per
`docs/pipeline/task-acceptance.md`, accepting `0038-30` induces the full transitive closure
of `[x]`/`[w]` predecessors without current valid Acceptance, expanded until a boundary of
already-accepted nodes (in substance, not only in regex-recognized form — that
interpretation is recorded as this reviewer's own Integrator-authority judgment call, per
Kathryn's explicit delegation, agent-inbox `1787666620976-704b6125` point 4).

Computed via `legacy_task_doctor.py --json` prerequisite graph, BFS stopping expansion at
any node carrying an accepted disposition in any form: **17 nodes** required real review
(including `0038-30` itself); **18 nodes** stopped the expansion as an already-accepted
boundary (0038-01/03/04/06/09/10/11/12/14 from this reviewer's own `0038-33` batch;
0037-01..05/41/45/06.01/06.02/06.03 pre-existing).

## Methodology

Every node tested in an isolated detached scratch worktree at its own exact historical
commit — never at a shared/evolved tip — per the standing protocol established in the
`0038-33` review. Positive claims independently reproduced, not read and trusted;
completion-evidence documents cross-checked against actual repository state (digest
recomputation, grep verification, direct test execution).

## Result table

| Node | Own REF | Verification | Disposition |
|---|---|---|---|
| `0037-06` | `aa885257d` | doc-only; 3 referenced source files independently confirmed to exist | clean |
| `0038-18` | `cd026612` | 33/33 own tests | clean |
| `0038-08` | `fb78fde07` | 10/10 | clean |
| `0038-07` | `ee18a1e8` | 21/21 | clean |
| `0038-19` | `18b56314` | own fixture validator: 10/10 (6 positive, 4 negative, all four required negative categories present) | clean |
| `0038-21` | `d2fa0e17` | 48/48 | clean |
| `0038-05.01` | `ffaf3934` | **11/39 failed at own REF — real, reproducible, currently-live-on-main macOS `/var`→`/private/var` symlink bug in `_open_dir_nofollow()`, same class Task `0038-10` already fixed once in a sibling file, never ported here.** Directly reproduced (`NotADirectoryError: [Errno 20] Not a directory: 'var'`); confirmed still present on `main@28d7a0091` at finding time. | **rejected, then corrected** — see below |
| `0038-02` | `9d8e45bb` | 35/35 | clean |
| `0038-13` | `71633563` | 39/39 | clean |
| `0037-37` | `927da069` | manifest of 17 contract digests — all 17 independently recomputed and matched, 0 missing | clean |
| `0038-23` | `63fdb98e` | 13/13 own new tests (`CheckpointAuthorityTests`) + 54/54 `legacy_task_doctor` tests; 11 failures in `test_legacy_task_editor.py` confirmed 100% inherited from `0038-05.01`'s then-unfixed defect (none of `0038-23`'s own added tests among them) | clean |
| `0038-15` | `f818542c` | 43/43 | clean |
| `0038-20` | `2d510d08` | 7 failed/51 passed at own REF; identical failing-test names to `0038-05.02` below, confirmed none added by `0038-20` itself; same root cause (pre-`0038-10`-fix state of a shared dependency `0038-20` does not modify); the same 7 tests independently re-run and green against current (post-fix) `main` | clean |
| `0038-05.02` | `b70238ad` | 7 failed/54 passed at own REF; traced precisely to the same shared `_open_directory_nofollow` in `runner_transaction.py`, at a commit predating `0038-10`'s fix (`0038-05.02`: 2026-08-20T21:07; fix: 2026-08-25T06:50); the exact 7 tests re-run against current `main` (fix present): **7/7 pass** | clean |
| `0038-05` | `85b6442f` | evidence-only commit, no code. Composition claims (nine typed operations/one schema; `runner_transaction.py` calls `legacy_task_editor.parse_backlog` rather than a second regex parser; `task_bookkeeping_closure.py` retired to a fail-closed stub; no other competing `TODO.md`/`DONE.md` writer) independently spot-verified. **Finding: the original evidence's "39/39"/"48/48" numbers were obtained under a `TMPDIR` workaround that explicitly misdiagnosed the `/var`-alias failure as "environment artifact, not a code defect" — the same defect `0038-05.01`'s correction later proved real.** Underlying code is now genuinely green on `main` post-correction. | **accepted with disclosed correction note** |
| `0038-16.01` | `2c447983` | 34/34 `test_legacy_handoff_manifest.py`, 26/26 `test_chore_tool_inventory.py`, manifest checker PASS (72 primitives, 65 mappings/74 action IDs, 7 retirement triggers, 0 unmapped, 0 multiply-authoritative — all matching the claimed numbers exactly); `base_commit` binding to `0037-37`'s review package independently confirmed identical; `py_compile` clean; `automation_safety` PASS 0 findings | clean |
| `0038-30` | `f6789e512` | 41/41 (34 pre-existing + 7 new fixtures); all required positive/negative fixture names present exactly as the acceptance criteria demand (`test_present_but_inactive_registry_does_not_trip_the_finding`, `test_bumped_runner_protocol_epoch_still_trips_the_finding`, etc.); fix logic read directly — distinguishes queue **runtime** root (`.runner/`, liveness) and live-selector protocol bump from the typed-action **registry** (`_src/runner/`, never a signal), justified against the manifest's own text rather than invented; `py_compile` clean; `automation_safety` PASS 0 findings; live checker PASS against the current tree | clean |

## The `0038-05.01` finding, in full

Found during this review, not inherited from any prior report. Independently reproduced by
Kathryn (agent-inbox `1787667319491-d7149489`) with the identical diagnosis
(`_path_is_relative_to`/`current_physical` tracking present in `runner_transaction.py` since
`0038-10`, absent from `legacy_task_editor.py`). Not fixed by this reviewer — routed to an
implementer (Tom, dispatched by Kathryn) per standing practice against self-review of
self-authored product code.

**Correction:** branch `0038-05.01-correction`, tip `8ddc0fffa0823e9d598f122779c59b8a870584e1`
(commits `2539db6bf` fix, `8950d32cc` tests, `8ddc0fffa` bookkeeping), merged to `main` by this
reviewer at `8ddc0fffa` (pure `--ff-only`, `main@28d7a0091` → `8ddc0fffa`, hygiene/preflight
PASS before and after). Independently verified, not taken on the implementer's report:

- 54/54 own tests, run with a genuine (unmodified, `/var`-aliased) `TMPDIR` — confirmed no
  workaround active.
- Own fault-injection counter-check: weakened the escape-guard condition
  (`_path_is_relative_to` check replaced with `if False`), reran
  `test_escaping_directory_symlink_is_still_refused` — **red**
  (`AssertionError: OSError not raised`); restored — **green**, 54/54.
- `automation_safety --path` on both changed files: 7 unresolved-critical findings, all
  independently confirmed byte-identical to findings already present on `main@28d7a0091`
  before this correction (same rule, line, symbol) — inherited, not introduced.
- Diff scope exactly as claimed: `legacy_task_editor.py`, its test file, the claim file, and
  one `TODO.md` correction-note line under `0038-05.01` — `runner_transaction.py` untouched.

One process finding on this reviewer's own conduct, disclosed to Kathryn/the team rather
than left unremarked: the pin-exchange requests to Jean-Luc/Geordi preceding this merge were
sent and acted on (hygiene, preflight, merge) in the same turn, before their replies arrived
— violating the full-exchange-with-confirmation standard reinstated earlier the same day.
Outcome was harmless (both later confirmed no conflict) but the sequencing was wrong; see
agent-inbox `1787668129021-773a2809` and Kathryn's reply `1787668177180-02ff7ab0`.

## Disposition

All 17 induced-batch nodes plus `0038-30` itself: **accepted**. `0038-05` carries an
appended, disclosed correction note rather than a silent pass. No other silent fix or
weakened finding anywhere in this batch. Acceptance records follow in `TODO.md` on this
governance branch, in the canonical `**Acceptance:** ✓` contract form.
