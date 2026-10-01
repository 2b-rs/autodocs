# Independent integration-checkpoint re-review — Task `0044-16`

## Verdict

**`accepted`.** Exact candidate
`e3561d47b4e2e0ddc4ebbf2a5af1bd8f813ab13a`, including substantive correction
`42e80f6e7412616999f42a865e3eefe8c985c85a`, conforms to the pinned Task
contract. Prior rejection `a141a493817f57ecf076180ccd2854f20207d0a4` and
finding `F-0044-16-GEORDI-01` remain append-only; this review closes that finding
only for the corrected candidate.

Reviewer: `Data-Geordi-20260822T213740Z`, persona Geordi, privileged Integrator.
Dispatcher: Data. Implementer: `Harry-Kira-20260822T184500Z`. The reviewer is
independent of both and did not author the implementation or its validation.

## Pinned baseline and closure

- Review branch/base:
  `review-0044-16-data-geordi-20260822T213740Z` from `main` at
  `ea0646721da70f9eae5f37a6f4b6881f47466b40`.
- Candidate/bookkeeping tip:
  `e3561d47b4e2e0ddc4ebbf2a5af1bd8f813ab13a`.
- Candidate tree: `4118f7fa774a85ec0b38f78bf28eb79c6fdf5b40`.
- Substantive correction:
  `42e80f6e7412616999f42a865e3eefe8c985c85a`; tree
  `ae2e40a05f162e60887b655c3ca5cf7b59c73679`.
- Original implementation:
  `59e5fd79d1501f21ff08d7f6a305f7f97d37ee0b`; prior candidate
  `904414470af2f84be5c3f93109a1c28379758a3e`.
- Exact complete candidate `0044-16` Task block: 7,420 bytes, SHA-256
  `70b84a144ccf1a55bc5c70a8829fa7b0860f9adfa77d1b14ee3f491f6e3b51ad`.
- Work-product manifest SHA-256:
  `0ba1d2bb536bbc2f25ae490a8a86773e77052a62ac2459cabef72db0c6d6c135`.
- Prerequisite-acceptance manifest SHA-256:
  `d5eefefdc766150cb757ab599a46cd46d9351ffc456572f5d5189764f431eccc`.

The transitive prerequisite closure is `0044-14` then `0044-15`. Both are
terminal and have current reachable accepted reviews: `0044-14` review
`964e6caed7ee72edc656ed070f65404f33ac5286`, and `0044-15` review
`11e3f1642397a879fa249d90c9dba22d6856c5ab`. No missing endpoint, cycle,
reversed edge, or ambiguous prerequisite was found. Current governance also
clarifies that prerequisite acceptance is a Feature-closure concern rather than
an entry gate for this checkpoint review; here the closure is accepted anyway.

### Work-product manifest

The manifest is the SHA-256 of the following UTF-8 records in this order, each
terminated by LF; `\t` below denotes one horizontal-tab byte:

```text
AGENTS.md\tdc232aa558068c82c46a5125eca17284c72de8a885702e97c7276e40ef492da3
TODO.md\tf2bb414e9f4f637205d9a8c2ff2e45152c4ffb2ee37e78770564273802a60d0d
TODO-Harry-Kira-0044-16-20260822T184500Z.md\t447d593bc5f767b35cc07f81a9c366ba5fed3c30f5e3c281ee31c3f371cf95c5
_src/tools/check_integration_hygiene.py\t9b586daebf149bd5f32b854efff7b2aadeb1ae7e0ea3148d0406b3df85ee7e15
_src/tools/test_check_integration_hygiene.py\t4b9e69ec73e97b8a33fde1eb03c6a9057854ed2ed8a28137e72611116a29d0f2
docs/pipeline/branch-workflow.md\t2e56fd0a2304811bcf2a23bdcdd6e8c88dd000034b39b93368497be7a478baff
docs/pipeline/tools.md\tf500096d3116da022b8409b88b1e8d37fe028addd198eb1fe6023bf997c872db
```

The prerequisite manifest uses the same line format for exact complete Task
blocks: `0044-14` →
`7aafea2fa8a22a65214111b9aaaf5922ced49c14ec86aa0ef18aca6545724fcc`;
`0044-15` →
`27b682a969692e4e9b8c685d8aa9f10dcf649501e7de7c78f087660d93be9301`.

## Correction verification

`F-0044-16-GEORDI-01` is closed. An independent serializer canary covered every
non-persistent finding code emitted by the implementation:
`INDEX_NOT_HEAD`, `MAIN_WORKTREE_DIRTY`, `STALE_AFTER_REF_MOVE`, and
`WORKTREE_UNAVAILABLE`. For the rejected candidate the canary proved that all
four leaked `index_age_seconds`, `index_mtime_utc`, and
`resample_delay_seconds`; for the corrected candidate it proved that all four
omit all three keys entirely. This negative control would fail on the original
null-key defect.

A persistent `FOREIGN_STAGED_TREE` serialized all three populated values. A
real CLI fixture returned exit `1`, `ok: false`, and the exact six-key finding
shape (`code`, `detail`, `worktree`, plus the three metadata keys). Missing
repository execution returned exit `2`, never a pass.

## Unchanged blocking and timing behavior

- Code inspection and a two-candidate fixture proved one shared re-sample only:
  sleeper calls were exactly `[0.25]`; the candidate committed during the window
  disappeared, while the persistent candidate remained one blocking finding.
  The measured fixture wall was 2.887 seconds.
- The persistent finding reported age `39,600.0` seconds and the configured
  delay. A separate default-delay fixture retained all populated values.
- `MAIN_WORKTREE_DIRTY` and `STALE_AFTER_REF_MOVE` still fire in their hermetic
  fixtures; `INDEX_NOT_HEAD` remains the integration-index finding.
- `_worktree_paths()` still enumerates `git worktree list --porcelain`, and the
  checker still visits the complete registered set before resampling only the
  initial foreign candidates.
- `HygieneReport.ok` remains false for any finding and the CLI maps that to exit
  `1`; persistent divergence was not converted to advisory or narrowed to
  integration-near worktrees.
- The hard root preflight remains explicit and complementary in `AGENTS.md`,
  `docs/pipeline/branch-workflow.md`, and `docs/pipeline/tools.md`.

## Independent validation

- Startup hard root preflight: PASS at review base
  `ea0646721da70f9eae5f37a6f4b6881f47466b40`.
- Mandatory startup hygiene: PASS, zero findings across 129 worktrees, 117.81
  seconds wall. A prior scan was discarded when `main` advanced during it.
- `py_compile`: PASS for checker and fixture module.
- Persistent focused fixture: PASS in 4.864 seconds; 5.75 seconds command wall.
- Full focused suite: 6/6 PASS in 15.885 seconds; 16.66 seconds command wall.
- Independent all-code null-leak negative control: PASS; rejected candidate
  fails the same predicate as expected.
- Independent concurrent two-candidate/shared-delay fixture: PASS.
- Persistent CLI blocking fixture: PASS, exit `1`; missing repository: PASS,
  exit `2`.
- Focused `automation_safety.py`: PASS, two files, zero findings and zero policy
  errors.
- `process_doc_doctor.py --json`: candidate and original baseline both PASS
  with 29 byte-identical sorted findings (SHA-256
  `fcc8a91c2b43f5f0581882ddfa7a0518275219c25b6b37a4e83f99db3b794006`).
- Live exact-candidate scan: PASS, zero findings across 130 registered
  worktrees, 133.76 seconds wall.
- `git diff --check`: PASS.

The live runtime confirms the mandatory gate has material cost and currently
scales poorly with the worktree registry. This is an operational observation,
not a conformance failure: it is not caused by the 2.0-second resample when no
foreign candidates exist, and the Task neither authorizes nor requires a wider
performance redesign.

## Scope and authority

The candidate changes resampling plus reporting and preserves what blocks. The
correction changes only serialization of absent optional finding values plus its
test and append-only bookkeeping. There is no blocking-to-advisory conversion,
foreign cleanup, cross-item scope mutation, candidate repair by this reviewer,
integration, `main` or Feature ref movement, `DONE.md` change, push, runner use,
or external mutation.

`main` later advanced from the review base through unrelated bookkeeping. That
does not change the pinned candidate or its contract. Any future integration
must reconcile then-current target policy; this review grants no integration
authority.

## `DEC-0044-013` dispatch record

- Dispatching identity: Data.
- Reviewer persona: Geordi, identity `Data-Geordi-20260822T213740Z`, distinct
  from dispatcher Data and implementer Harry-Kira.
- Context given: the complete briefing below; current repository authority and
  governance; exact candidate/history/diffs; candidate claim and tests; prior
  rejected report and finding; prerequisite reviews; agent-inbox broadcasts;
  direct Git and test authority.
- Context not given: no implementer session transcript, no prewritten verdict,
  no hidden validation result, no authority to fix or integrate the candidate,
  no authority to move `main`/Feature refs or `DONE.md`, and no runner authority.

### Verbatim briefing

~~~~text
Resume as `Data-Geordi-20260822T213740Z`, privileged independent Integrator reviewer, for exact Task 0044-16 re-review only. Pin candidate tip `e3561d47b4e2e0ddc4ebbf2a5af1bd8f813ab13a`, substantive correction `42e80f6e7412616999f42a865e3eefe8c985c85a`, and prior rejected review evidence `a141a493817f57ecf076180ccd2854f20207d0a4` / finding F-0044-16-GEORDI-01. Verify independently that all non-persistent findings omit `index_age_seconds`, `index_mtime_utc`, and `resample_delay_seconds` entirely, while persistent `FOREIGN_STAGED_TREE` contains all three populated values; exercise a negative regression that would fail on null-key leakage. Reconfirm one shared resample, persistent blocking semantics, MAIN_WORKTREE_DIRTY, STALE_AFTER_REF_MOVE, all-worktree scope, hard root preflight, missing repo exit 2, and timing/runtime evidence. Preserve rejection append-only. If conforming, commit review evidence first and a separate path-isolated Acceptance bookkeeping commit with real REF/digests. Record this verbatim briefing/context. Do not fix candidate, integrate, move main/Feature refs, touch DONE.md, push, or use runner. Keep concise.
~~~~

## Final disposition

Verdict `accepted` at `2026-08-22T21:50:52Z`. Evidence is committed before the
separate `TODO.md` acceptance record. The prior `rejected` verdict remains
append-only and no integration is performed.
