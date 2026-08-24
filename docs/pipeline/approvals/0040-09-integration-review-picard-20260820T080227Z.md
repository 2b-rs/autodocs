# Aggregate integration review — Feature `0040`, checkpoint `0040-09`

## Assignment, independence, and pinned baseline

- **Decision:** `accepted`
- **Reviewer:** `agent:picard:0040-closure:20260820T080227Z`
- **Role / capability:** privileged Integrator and acceptance reviewer
- **Authority reference:** current-user assignment of 2026-08-20, verbatim in `TODO-picard-0040-09-review-20260820T080227Z.md`
- **Recorded at:** `2026-08-20T08:02:27Z`
- **Pinned candidate:** `d5a65d3a770e7996432f18b5c37cf25c180a3c89` (branch `0040`)
- **Merge base with `main`:** `74af28df766ab0e55c4c43dcaebd6631ce40aefb`
- **Review checkout:** `.worktrees/0040`, clean at review time

**Independence.** This reviewer performed none of the Feature `0040` implementation,
authored none of its technical dispositions, and produced none of its validation
evidence. It did not use `DEC-0040-001`; that waiver is not invoked by this review.

**Disclosed involvement.** This session transcribed the two Management decisions
`DEC-0040-007` and `DEC-0040-008` into the repository at commit
`d5a65d3a770e7996432f18b5c37cf25c180a3c89`, and that commit is part of the pinned
candidate. The decisions themselves were taken by the current user; the session
presented the available dispositions and their consequences and decided nothing.
The verbatim user selections are retained in
`docs/dossiers/0040-management-closure-provenance.md`. This review does not treat
its own transcription as evidence of the decisions' correctness; it verifies only
that they exist, carry valid Management authority, and match the retained
verbatim selections.

## Disposition of the predecessor review's required actions

The prior re-review (`agent:worf-kurn-…`, `2026-08-19T22:04:06Z`, `inconclusive`)
named three required actions. All three are now satisfied:

1. **`F-0040-09-001` — ratify or reject `DEC-0040-005`. Resolved.** Management
   ratified the substantive rule as its own decision in `DEC-0040-007`. The
   historical agent-as-Management entry is preserved uncorrected. Verified: the
   original record is byte-unchanged, the ratification is append-only in the same
   dossier, and the accepted `0040-05` baseline is untouched.
2. **`F-0040-09-002` — finite bounded-waiver duration for `DEC-0040-001`.
   Resolved.** The granting authority appended `DEC-0040-008` with
   `Duration: from 2026-08-18T00:32:23Z until event:feature-closure:0040`, which
   is the event form explicitly permitted by `decision-record@v1` section 4.
   `DEC-0040-001` and its legacy projection `DEC-0040-001-LM001` remain unchanged
   and continue to record the historical incompleteness truthfully.
3. **`F-0040-09-003` — resolve the automation-safety validation limitation on an
   exact new baseline. Resolved; see Validation.**

## Prerequisite and ancestry review

All required tips are ancestors of the pinned candidate (`git merge-base
--is-ancestor`, exit 0 each):

| Item | Tip | Result |
|---|---|---|
| `0040-03` corrective | `dd2d7d45ed8c8c9e1d219370acc14a1708262822` | reachable |
| `0040-05` checkpoint | `afb506dedce3ee476b0f26c0c0fc0cafd84b01cc` | reachable |
| `0040-08` retrospective | `86e285435e305a1e5c98fbb7aa1634bb3d9d8563` | reachable |
| `0040-09` integrating | `e46521de7518955076e58900103df55711ad602e` | reachable |
| `0040-10` safety repair | `f40d06bef44b453454c555894f324eb49fee40b9` | reachable |
| prior pinned candidate | `376f53f3ee9a648190d87abbff6c54008d9ccbb4` | reachable |

All ten Tasks are terminal: `0040-01`, `0040-03`, `0040-05`, `0040-08`, `0040-09`,
`0040-10` are `[x]`; `0040-02`, `0040-04`, `0040-06`, `0040-07` are `[w]` with
recorded reasons from the trilateral agreement.

**Feature-closure prerequisite `0040:0039-01`.** Satisfied on its original terms.
`0039-01` is `[x]` with a current independent `Acceptance: ✓` (review REF
`5c75893795ab7d8a7edd1a8583c26f627ace3662`), reachable on Feature branch `0039`
at `cdeb9a1324370ed1de7a22af527600d1e78e522b`. It is deliberately not merged into
`0040`: a Feature prerequisite is a closure gate, not an upward-merge edge. The
separate release of the Feature `0039` reservation (`MGMT-0039-001`) does not
alter this gate and was not relied upon.

## Checkpoint review

**`0040-05` — retained, not re-granted.** Its `Acceptance: ✓` was granted by
`authority:current-user:0040-05-review:20260818T174212Z` — the current user acting
as management authority, not the Feature owner session. Under the create-once
immutability baseline this reviewer does not add, alter, or duplicate that record.
Verified that the candidate diff removes or modifies no existing `Acceptance:`
line.

**Bounded-waiver compensating control.** The Feature contract requires that every
acceptance the Feature owner granted to its own work be marked as such and name
`DEC-0040-001`. Verified: Feature `0040` contains exactly one `Acceptance: ✓`
record, and it was granted by the current user, not by the owner session. The
waiver was therefore never exercised for self-acceptance, and the compensating
control is satisfied vacuously rather than by a marked self-acceptance.

**`0040-09` — requirement disposition.** The matrix in
`docs/dossiers/0040-09-integration-package.md` carries a disposition for all 20
decomposed stable requirement IDs. Independently checked by set comparison against
the requirements baseline: the only baseline ID absent from the matrix is
`RQ-SRC-01`, which is the verbatim customer source requirement and not one of the
20 decomposed requirements. No decomposed requirement is undispositioned, and no
deferred traceability work is represented as delivered.

**No new blocking gate.** `_src/validate.py` is not in the candidate diff. The
candidate's only automation-relevant change is
`_src/tools/automation_safety_policy.json`, whose added entries are individually
named, owner-bound (`owner_task`), and expiry-bound (`expires_after_task`)
dispositions, not blanket suppression. `0040-04` closed `[w]` explicitly barred
from becoming a blocking gate. No `RQ-DEC-05` decision is therefore missing.

## Validation (fresh, on the exact pinned candidate)

| Check | Result |
|---|---|
| Full default live automation-safety scan | **PASS** — 105 files, 71 findings, 35 disposed critical, **0 unresolved critical**, **0 policy errors** |
| Targeted `_src/run-loop.sh` scan with explicit policy | 0 unresolved critical, 10 disposed critical |
| Automation-safety unit suite | 120 of 121 pass; 1 pre-existing failure, see finding below |
| Legacy task-doctor unit suite | **PASS** — 42 tests |
| Candidate diff whitespace | **PASS** — `git diff --check 74af28df7..HEAD` |
| Repository object/ref integrity | **PASS** — `git fsck --no-reflogs --no-dangling` |
| Acceptance-record preservation | **PASS** — no existing `Acceptance:` line removed or modified |

The predecessor could not claim a fresh full safety pass because its targeted scan
exceeded a 60-second bound. That bound, not a defect, was the obstacle: the same
scan completes normally when allowed to run, and the authoritative default live
scan passes. Note for future reviewers: `--policy` defaults only for live scans,
so an explicit `--path` run without `--policy` reports every disposition as
missing and yields a misleading `FAIL`. This reviewer initially made that error and
corrected it before drawing any conclusion.

## Findings

- **`F-0040-09-004` — minor, pre-existing, not attributable to this candidate,
  owner Feature `0038`.** `_src/tests/test_automation_safety.py::
  test_current_safe_aggregate_controls_do_not_regress` fails because
  `_src/tools/runner_transaction.py` receives `AUTO010`. Attribution was
  established empirically, not assumed: a detached worktree at the merge base
  `74af28df766ab0e55c4c43dcaebd6631ce40aefb` reproduces the identical single
  failure out of 121 tests, and `runner_transaction.py`,
  `test_automation_safety.py`, and `automation_safety.py` are byte-identical
  between `main` and the candidate. Merging this Feature therefore neither
  introduces nor worsens the failure. It contradicts no `0040` criterion and is
  carried to Feature `0038`, which owns `runner_transaction.py`. Deferral is
  permitted because the authoritative full scan passes and the defect is outside
  the reviewed contract.

No critical or major finding is open. Findings `F-0040-09-001` and `F-0040-09-002`
are closed by Management decision; `F-0040-09-003` is closed by fresh validation.

## Decision

**Accepted.** The pinned candidate `d5a65d3a770e7996432f18b5c37cf25c180a3c89`
satisfies the `0040-09` acceptance criteria and Definition of Done. All ten Tasks
are terminal, both mandatory checkpoints are disposed (`0040-05` retained
accepted, `0040-09` accepted here), every decomposed requirement carries a
disposition, the bounded waiver is complete and was never used for self-acceptance,
no new blocking gate was introduced, and fresh full automation-safety validation
passes on this exact baseline.

This acceptance binds the digests recorded in the `TODO.md` acceptance record. It
confers no product approval, release authorization, safety acceptance, or
Automotive SPICE capability claim; the Feature's own scope boundary between
process support and assessed capability remains binding.

## Remaining closure step

With this checkpoint accepted and the `0040:0039-01` closure gate satisfied,
Feature `0040` is eligible for the privileged closure act: integration of branch
`0040` into `main`, reconciliation and removal of the carried predecessor claim
files, and the path-isolated move to `DONE.md`. That act is recorded separately
from this review.
