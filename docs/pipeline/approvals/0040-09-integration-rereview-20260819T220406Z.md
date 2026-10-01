# Re-review — Feature `0040` integration and checkpoint `0040-09`

## Assignment, independence, and pinned baseline

- **Decision:** `inconclusive`
- **Reviewer:** `agent:worf-kurn-20260819t000700z:0040-09:20260819T000700Z-7ac7f6`
- **Role / capability:** privileged Integrator and acceptance reviewer
- **Authority reference:** exact current-user assignment for Feature `0040`, `0040-05`, and `0040-09`, received as the provenance in `TODO-worf-kurn-0040-09-20260819T000700Z-7ac7f6.md`
- **Recorded at:** `2026-08-19T22:04:06Z`
- **Review input:** prior `0040-09` review tip `e46521de7518955076e58900103df55711ad602e`, plus corrective `0040-03` tip `dd2d7d45ed8c8c9e1d219370acc14a1708262822`
- **Pinned merged candidate:** `376f53f3ee9a648190d87abbff6c54008d9ccbb4`
- **Feature input:** `origin/0040` at `86e285435e305a1e5c98fbb7aa1634bb3d9d8563`
- **Integration checkout:** `.worktrees/0040-integration-Kurn-20260819T000700Z`

This reviewer is not a recorded `0040` claim owner, principal implementer,
decisive technical author, or sole validation producer. The review therefore does
not use `DEC-0040-001` as a self-acceptance waiver. All prior claims, the previous
inconclusive review, and the current user-authorized `0040-05` acceptance remain
append-only provenance.

## Branch and prerequisite review

The canonical relevant tips were:

| Item | Canonical ref | Tip | Result |
|---|---|---|---|
| prerequisite feature | `0039` | `cdeb9a1324370ed1de7a22af527600d1e78e522b` | contains the current accepted `0039-01` integration |
| prerequisite task | `0039-01` | `f268f5610d18b09da15bb1edcd12a78664126529` | current corrected acceptance is reachable on `0039` |
| feature | `0040` | `86e285435e305a1e5c98fbb7aa1634bb3d9d8563` | feature input |
| corrective task | `0040-03` | `dd2d7d45ed8c8c9e1d219370acc14a1708262822` | merged into this candidate |
| mandatory checkpoint | `0040-05` | `afb506dedce3ee476b0f26c0c0fc0cafd84b01cc` | reachable and still accepted |
| retrospective task | `0040-08` | `86e285435e305a1e5c98fbb7aa1634bb3d9d8563` | feature input tip |
| integrating task | `0040-09` | `e46521de7518955076e58900103df55711ad602e` | prior inconclusive-review tip |
| safety repair | `0040-10` | `f40d06bef44b453454c555894f324eb49fee40b9` | reachable |

`0039-01` now carries a corrected current acceptance with review REF
`5c75893795ab7d8a7edd1a8583c26f627ace3662`, and its integration is reachable
from `0039` at the user-supplied tip. Thus `0040:0039-01` is no longer an
unsatisfied Feature-closure prerequisite. It is deliberately not merged into
`0040`: Feature prerequisites are closure gates, while the branch workflow only
moves item work upward through its own parent hierarchy.

The candidate merges `0040-03` safely on top of `0040-09`; all predecessor and
corrective claim files are retained. The corrective diff is limited to Task-owned
English documentation and its claim/bookkeeping: decision-record schema literals,
identifiers, regular expressions, trigger values, role values, legacy maps,
acceptance history, three positive examples, two negative examples, and finite
waiver-duration rule were inspected and preserved. It introduces no acceptance,
new blocking gate, or authority grant.

## Bottom-up checkpoint review

### `0040-05` — current mandatory checkpoint

The existing `0040-05` user-authorized acceptance remains bound to
`1f9583ad1d8f1f76e3a6050cb14be510ed125801` and review REF
`063a85998f90197b698b9672e816ffaba7e5fb15`. Its four non-`TODO.md` manifest
bytes were independently rechecked against the recorded SHA-256 values:

- `AGENTS.md`: `bb08ff0afecde62293f543823d26ed0526676b3a2dfb865e6bd7868561352b36`
- `docs/pipeline/process-roles.md`: `13d3c8e67cdca10c5b4f7c8e4f48c06b41627b170c7b38f84ea32960a9670fd1`
- `docs/dossiers/0040-05-cross-item-scope-review.md`: `9e600cf244c8f31c281fbd69c6501aadd09052340a8cef499adcfc80d2379b20`
- `TODO-zed-0040-05-20260818T162728Z-4c98b6072815.md`: `0a2af71964bbcefcb672241134c3c482b664b3f707f3467c62321946ee3271d3`

The historical `TODO.md` digest is also exactly
`996d776b4aa1c9f4d1e11ce4f8ea4d7cca21313c4f9645370824e7ce077d3b79`; later
append-only task history and the non-semantic English correction do not replace
or silently extend that accepted baseline. The correction makes the Management
boundary clearer but does not cure `DEC-0040-005`.

The five originally approved scope-rule criteria, the distinct Architect support,
and the no-new-acceptance-authority boundary were re-read. The task remains
current as an exact historical checkpoint acceptance. Its underlying management
identity defect is an aggregate authority finding below, not a fabricated
retroactive invalidation of the user's pinned acceptance.

### `0040-09` — Feature integrating checkpoint

The requirement matrix in `docs/dossiers/0040-09-integration-package.md` still
contains a truthful disposition for all 20 stable requirement IDs: implemented,
explicitly tailored, or explicitly deferred with the recorded downstream owner.
The deferred traceability work remains partitioned under `DEC-0040-006`; the
reserved `0039-01` effectiveness measurement has now been accepted/integrated,
but no unimplemented traceability work is represented as delivered. The review
also rechecked that no new blocking gate was introduced by this candidate.

## Validation

| Check | Result |
|---|---|
| Candidate and merge diff whitespace | PASS: `git diff --check origin/0040..376f53f3…` |
| Repository object/ref integrity | PASS: `git fsck --no-reflogs --no-dangling` |
| Candidate ancestry for `0040-03`, `0040-05`, `0040-09`, `0040-10`, and accepted `0039-01` | PASS |
| `0040-05` accepted-manifest recheck | PASS; digests above |
| Legacy task-doctor unit suite | PASS: 42 tests |
| Automation-safety unit suite | FAIL: 1 of 121 tests; current `_src/tools/runner_transaction.py` receives `AUTO010` in `test_current_safe_aggregate_controls_do_not_regress` |
| Direct targeted/full automation scan | Not a pass: `automation_safety.py --path _src/run-loop.sh --json` exceeded the 60-second bound without output; earlier retained full-scan evidence is not claimed as a fresh run |
| Global legacy task doctor | FINDINGS: 271 errors, 132 warnings, 403 total; it also reported the initial explanatory syntax in this review claim before it was corrected. No global clean result is claimed. |

The failing automation-safety test concerns pre-existing Feature `0038` runner
transaction code (`cd026612…`) and neither `_src/tools/runner_transaction.py` nor
the test changes in `0040-09..376f53f3…`. It is retained as a current baseline
validation observation, not attributed to the `0040-03` correction. It prevents
claiming a fresh full automation-safety pass for this review.

## Blocking findings and outcome

1. **`F-0040-09-001` — major authority-record defect, unresolved.**
   `DEC-0040-005` names `agent:zed:0040-05:20260818T162728Z-4c98b6072815` as
   `Management`, while the normative role model reserves Management to the current
   user or a registered authority. The prior user approval of `0040-05` does not
   append a ratification or correction. The current assignment authorizes review
   and integration, not retrospective Management ratification. This reviewer
   cannot invent it.
2. **`F-0040-09-002` — incomplete bounded waiver, unresolved.**
   `DEC-0040-001` lacks the required duration. It was not used by this independent
   reviewer or to self-accept a checkpoint, but the Feature contract requires the
   waiver and compensating control to be visible and honoured. Only its granting
   authority may append a finite duration, event-bound replacement, revocation, or
   explicit supersession.
3. **`F-0040-09-003` — validation observation.** The current unit-test failure
   and timed-out direct scan mean this review does not claim fresh full
   automation-safety validation. The source is outside this candidate's diff; it
   requires separate owner assessment if an acceptance retry proceeds.

**Outcome:** `inconclusive`. `0040-09` cannot receive `Acceptance: ✓`; the
existing `0040-05` acceptance is retained without alteration. The Feature remains
out of `DONE.md` and must not be integrated into `main` until the two
Management-only authority actions are appended and a new exact baseline review
re-evaluates the validation observation.

## Required authority actions

1. The current user or registered Management authority must append an explicit
   ratification or rejection of `DEC-0040-005`, preserving the historical
   agent-as-Management entry.
2. The granting authority must append a finite duration, event-bound replacement,
   revocation, or explicit supersession for the `DEC-0040-001` waiver.
3. Before acceptance is retried, rerun/resolve the current automation-safety
   validation limitation on an exact new baseline.
