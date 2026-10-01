# Task-Acceptance decision — 0037-09.01

- **Reviewer:** paul (Discovery Integrator, privileged)
- **Assignment:** michael OFFER `1787871554232-7418d522`; paul ACCEPT `1787871785038-d47b85a4`; explicit AWARD `1787871949767-d076e6ce` (michael, 2026-08-27T23:05:49Z). ACCEPT is not the award; this AWARD authorizes inspection and evidence only.
- **Reviewed at:** 2026-08-28T01:20:00+02:00
- **Product REF (reviewed baseline):** `7b36370e84c5c793e705a1d418e2b5db2b7cc965`
- **Product parent:** `5ba92074c2b8b2109d35ba2f736b8ebe7f196ab9`
- **Main pin (AWARD / this worktree):** `a8b50eeeab207d91f32114499bdfcbc74b49ad73`
- **C merge (how the product reached main; not the review):** `6b4f8bab94042246ca2a352210f0bda43bba9017`
- **Worktree:** `.worktrees/review-0037-09.01-paul-20260827T230700Z`
- **Branch:** `review-0037-09.01-paul-20260827T230700Z`
- **Product inspection checkout (read-only, detached):** `.worktrees/review-0037-09.01-paul-product-7b36370e`

## Independence

Not the claim owner (`agent:julian:0037-09.01:20260824T171000Z`). Not the principal implementer. Product author is `tobias.anton <tobias.anton@accenture.com>`. Not sole validation producer (validation re-run independently this session). Not geordi/obrien. No waiver.

Eyes-open: this reviewer previously landed the 09.01 product unreviewed as wave C (`6b4f8bab9`). This review is first-review of Julian's 09.01 work products at `7b36370e84`. C is not the reviewed tree and was not used as a substitute for inspection.

## Pins

- `7b36370e84` is an ancestor of `main@a8b50eee`.
- `6b4f8bab9` is an ancestor of `main@a8b50eee` and is recorded only as the land path.
- 0037-09.01 is `[x]` on `main@a8b50eee` TODO.md L1098–1101 **without** `Acceptance: ✓` on its own block.
- Node is **not** flagged `Integration review: mandatory`.
- 09.01 `cases.json` blob `a5946b33218fa04b46e9a6c024c0352d658b616b` is identical at `7b36370e84` and `a8b50eee`.

## Contract

- **Contract SHA-256:** `dbc7d52a2f3c06aec9197a8d676a6e4aeece9c09ad26b6820afd70fb324805ff` (exact `TODO.md` block on `a8b50eee` from `- [x] **0037-09.01**` through the blank line before `0037-09.02`).
- **Work-product key-file SHA-256:** `b2d5a4ae11b3d5c42d7ac1f10252c4f75b3022053b0269c9a1c23085916e7ad8` over product-tree bytes of `issue_validate.py`, `test_issue_validate.py`, `fixtures/0037-09.01/cases.json`, implementer claim `TODO-julian-0037-09.01-20260824T171000Z.md`.
  - `c63900c1342d04c98df53adaa28cf9706f7c8261e3f13277d25907e94aed24cf` `_src/tools/issue_validate.py`
  - `74dd7e0093615bd5c9717fe7415316dc6d101aa94a0f8856aacccb41d73e78c2` `_src/tests/test_issue_validate.py`
  - `7458d198b0084e5f2cd18a5fca22a6ee1b7af6ce0cc6c985d68d5f40c917e2ed` `_src/tests/fixtures/0037-09.01/cases.json`
  - `29b5cd4c78556f53774d1103109c34b125f0926a06ccbe2c89aa0407dc5ca7c8` `TODO-julian-0037-09.01-20260824T171000Z.md`

## Independent validation (this session)

Against isolated product checkout `7b36370e84` (CPython 3.9.6 via `uv`):

- `uv run python -m unittest _src.tests.test_issue_validate` → **8/8 OK** in 6.984s
- `uv run python -m unittest _src.tests.test_issue_store` → **10/10 OK** in 0.424s
- `uv run python -m py_compile _src/tools/issue_validate.py _src/tests/test_issue_validate.py` → PASS
- `git diff --check 5ba92074c..7b36370e84` → empty
- `uv run python _src/tools/automation_safety.py --path _src/tools/issue_validate.py --json` → `verdict: PASS`, 0 findings

Against the AWARD worktree `a8b50eee` (sibling-additive tree; **not** treated as the 09.01 review):

- `uv run python -m unittest _src.tests.test_issue_validate` → **17/17 OK** in 18.398s
- Confirms the 09.01 fixture blob is unchanged and the 09.01 cases still execute in the later suite.

## Work-product findings

Inspected the actual product diff `5ba92074c..7b36370e84` (4 files, +508/−1): side-effect-free snapshot validator on the 0037-08 parser; IV0900–IV0908; 13 tracked negative cases in `cases.json`; dedicated HEAD-compare tombstone test (`IV0907`/`IV0908`); staged-index vs working-tree distinctness; explicit authoritative/candidate roots; fixed-seed property loop `random.Random(370901)` × 32 acyclic graphs; stable exit codes `0`/`2`/`3`.

Acceptance criteria map:

| Criterion | Where detected |
|---|---|
| unknown/duplicate/malformed IDs and criteria | parser `IS0832`/`IS0835`/`IS0826`/`IS0829` plus graph `IV0902` |
| reused tombstones | `IV0908` (and missing-instead-of-tombstone `IV0907`) vs HEAD/authoritative root |
| parent/prefix/path mismatch | parser `IS0836`/`IS0803`/`IS0835` |
| invalid fields/Markdown | `IS0832`/`IS0824` |
| cycles/self-dependencies | `IV0906` / parser `IS0840` plus graph `IV0903` |
| missing endpoints | `IV0904` |
| Feature-closure vs start-gate misuse | `IV0905` |
| diagnostics name item/path/line/field/rule; stable exit codes | `Diagnostic` dataclass; `EXIT_OK=0`, `EXIT_INVALID=2`, `EXIT_USAGE=3` |

DoD: one negative fixture per tracked error category in `cases.json` (13); tombstone pair covered by `test_tombstone_reuse_and_removal_compare_against_head` because it requires HEAD comparison; working-tree and staged-index both exercised; resource bounds `MAX_ITEMS=10000`, `MAX_EDGES=100000`, plus parser document-byte oversize `IS0804`.

### Observations (non-blocking)

- Tracked `duplicate_item_id` mutation is a path/id mismatch (`IS0835`), not two successfully parsed items sharing an ID. `IV0902` remains in `_graph_checks` as defense in depth.
- Tracked `self_dependency` is caught as parser `IS0840`; `IV0903` is likewise defense in depth.
- `IV0901` item/edge-count ceilings are implemented; the tracked oversize fixture exercises parser `IS0804` rather than forcing 10k items / 100k edges.

No critical or major findings. No criterion contradiction.

## Prerequisite-Acceptance closure

Declared implementation start prerequisites: `0037-02`, `0037-08`.

On `main@a8b50eee` both already carry current `Acceptance: ✓` (0037-02: belanna, baseline `91a4b99fb`; 0037-08: paul, baseline `4376be766`). Both accepted baselines are ancestors of `a8b50eee`. Verify-only this assignment; not restamped; 0037-08 Acceptance text not rewritten.

Prerequisite-Acceptance does **not** block 0037-09.01 Acceptance credit. This AWARD nevertheless forbids writing `Acceptance: ✓` until a later AWARD that names Acceptance bookkeeping.

## Disposition

- **0037-09.01 work products vs this Task contract:** `accepted` (implementation complete at `7b36370e84`; independent validation green; criteria and DoD evidence present).
- **Current `Acceptance: ✓` for 0037-09.01:** **not recorded**. Withheld by AWARD `1787871949767-d076e6ce` (no Acceptance stamp this round; no main advance).
- **Overall review record:** `accepted` for work-product fitness; Acceptance credit deferred to a later exact AWARD.

No `TODO.md` Acceptance bookkeeping. `refs/heads/main` not advanced. 09.02/09.03 not restamped. 09.04, 09 parent, Feature 0037 `DONE.md`, 0037-16, 0037-28, 0039-01, 0019, spawn, geordi: not touched.
