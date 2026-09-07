# Claim: belanna / 0038-35 freeze-violation correction (Implementation)

- **owner_token:** `agent:belanna:0038-35-freeze-violation-correction:20260907`
- **Task:** Implementation award correcting the invalidated 0038-35 integration PASS. Brief: `docs/campaign-evidence/0038-35/correction-0038-35-freeze-violation.md`.
- **Capability class:** `privileged` (OFFER `1788811635600-ae6136fa`, process=Implementation, item=0038-35, scope_name=freeze-violation-correction; ACCEPT recorded; AWARD confirmed via `offer_status`: status=awarded, winner=belanna).
- **Execution authority:** direct local execution in an item-owned `/tmp` worktree; no self-integration, no self-acceptance (Implementation award, not Integration Review).
- **Branch/worktree:** `0038-35-freeze-violation-correction` at `/tmp/autodocs-worktrees/0038-35-freeze-violation-correction`, cut from `main` at `4f420824368c190813effc6e8d39e3652ab015ec` (tip at claim time: `docs(0038-35): record freeze-violation correction evidence`).
- **Write scope (per AWARD):** `_src/tools/issue_lists.py`, `AGENTS.md`, `TODO.md`. This claim file travels on the same branch.

## Scope correction received mid-work (authoritative, not self-decided)

Two messages narrowed execution order after I had already drafted a broader plan:
- supervisor `1788812690316-066cfeb5`: revert only the illegal 0038-35 hand-edit in `TODO.md`; no new `TODO.md`/`DONE.md` content; generator support belongs in `issue_lists.py`.
- kathryn `1788812931669-c89bed93`: (1) revert Worf's bad hunk now — corrective, not a new hand-edit; (2) land the generator fix (extract AE-8 from `AGENTS.md:271/282` markers) now; (3) do **not** run/land a regeneration that re-adds the AE-8 block to `TODO.md` — that step waits for `0037-40` signed activation.

This supersedes an earlier self-authored draft plan (reinstate the AE-8 hunk in `TODO.md` via generator-verified bytes without a live regeneration). That draft is abandoned in favor of the explicit authority instruction above: revert-only now, regeneration parked.

## Work performed

1. **`TODO.md`**: reverted the exact 13-line `4c114df3b` hand-edit (the `adversarial-completion-evidence@v1` BEGIN/END block and its body), restoring the file to its last valid generated state. No other line touched (`git diff --stat`: `TODO.md | 13 -------------`, deletions only).
2. **`_src/tools/issue_lists.py`**: implemented Seven's generator spec. Added `_extract_adversarial_evidence(repository_root)` (fails closed with an `IssueListsError` naming `AE-8` if the `AGENTS.md` markers are missing/malformed), threaded an optional `evidence_block` through `_header()`, and wired `render_lists()` to extract the block from `AGENTS.md` and project it into the `todo` kind only (not `done`/`open`/`blocked`/`unclear`/`owners`), plus a `agents_md_ae8_sha256` digest entry.
3. **`_src/tests/test_issue_lists.py`**: added `test_ae8_block_extracted_from_agents_md_matches_todo_only`, `test_ae8_missing_markers_in_agents_md_is_a_hard_error`, `test_ae8_extraction_is_deterministic_and_digested`. `python3 -m pytest _src/tests/test_issue_lists.py -v` → 8 passed (5 original + 3 new).
4. **Did not** run generation against the live `issues/` store to re-populate `TODO.md`'s AE-8 block — parked per kathryn's item (3) pending `0037-40` activation.

## DEC-0038-004 adversarial completion evidence (my own change is claim-bound: AE-1 serialization shape/field presence, on `_header()`'s output)

- **AE-2 baselines:** pre-change baseline = `main@4f420824368c190813effc6e8d39e3652ab015ec` (this branch's base). Candidate = uncommitted worktree state about to be committed on `0038-35-freeze-violation-correction`.
- **AE-3 falsification, red→green:** ran the pre-change module against the real fixture issues via a full `git archive main | tar -x` snapshot (`/tmp/ae3-baseline-check`, deleted after use): `baseline(main@4f420824368c) todo contains AE-8 begin marker: False` (red — no extraction existed). On the candidate, `test_ae8_block_extracted_from_agents_md_matches_todo_only` asserts the same marker present and byte-equal to `AGENTS.md`'s block (green). Command: `python3 -m pytest _src/tests/test_issue_lists.py -v` (candidate, 8 passed).
- **AE-4 adjacent cases:** (a) kind dimension — `todo` carries the block, `done`/`open`/`blocked`/`unclear`/`owners` do not (same test, second half). (b) source-integrity dimension — `AGENTS.md` markers missing/malformed raises `IssueListsError` naming `AE-8` rather than silently omitting the block (`test_ae8_missing_markers_in_agents_md_is_a_hard_error`).
- **AE-6:** additive only — no existing assertion in `test_issue_lists.py` weakened; the 5 pre-existing tests still pass unmodified.
- **AE-7:** n/a — this is a behavior change, not excluded.

## Known, expected, out-of-scope-to-fix red state (not a regression I own)

`python3 -m pytest _src/tests/test_adversarial_evidence.py -q` now shows 3 failures against the live repo root (`test_live_repository_projections_are_identical`, `test_projection_mode_exit_zero_on_live_repo`, `test_all_eight_propositions_present_in_both_files`), all `AE-8-PARTIAL-PROJECTION` / block-count-0-in-`TODO.md`. This is the **direct, intended consequence** of reverting the improperly-obtained `4c114df3b` PASS per the correction brief and the two scope-correction messages above: `TODO.md` no longer carries the AE-8 block, `AGENTS.md` still does, and re-closing that gap requires the parked regeneration step. Not fixed here; not mine to fix before `0037-40` activation.

## Must not

Regenerate/re-populate `TODO.md`'s AE-8 block; touch any other `TODO.md`/`DONE.md`/`TODO-*`/`DONE-*` content; self-integrate or self-accept (Implementation award); advance `main`.

## Progress log

- 2026-09-07 — offer verified via `offer_status` (awarded). Worktree/branch confirmed at base `4f420824368c190813effc6e8d39e3652ab015ec`.
- 2026-09-07 — implemented generator fix + tests; ran AE-3 red baseline via `git archive`; verified regenerated-vs-live AE-8 block byte-identity against the real `issues/` store (verification only, output discarded, not promoted).
- 2026-09-07 — received supervisor/kathryn scope correction (revert now, regenerate later); reverted `TODO.md` hunk accordingly (13 deletions only); confirmed `test_issue_lists.py` 8/8 green and the 3 expected `test_adversarial_evidence.py` live-repo failures are exactly the intended-red consequence, not a new defect.
- 2026-09-07 — this claim file committed alongside the deliverables. Kathryn flagged its absence (`1788813133603-f128da96`); filed now.
- Next: commit deliverables + this claim on the item branch with Task-ID/Base-Ref trailers, then hand off review-ready to kathryn/PL per normal flow (no self-accept).
