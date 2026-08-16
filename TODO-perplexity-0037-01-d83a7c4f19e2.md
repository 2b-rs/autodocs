# TODO-perplexity-0037-01-d83a7c4f19e2.md — active claim

## Claim identity

- `task_id`: 0037-01
- `feature_id`: 0037 — Git-Native Issue Store, Provenance Graph, and Backlog Migration
- `agent`: perplexity (SANDBOXED AGENT PERPLEXITY)
- `capability_class`: sandboxed/grunt — no direct execution of scripts, shells, tests,
  generators, browsers, package managers, network clients, or Git. All execution is routed
  through the singleton `run.sh` runner slot per `SANDBOX.md`.
request_id: f7091d5ea6c8
owner_token: agent:perplexity:0037-01:f7091d5ea6c8
base_commit: 94a697b647c930687d55fcbec837421a7e674e80

(The three fields above are deliberately written as plain unquoted `key: value` lines, per
the lesson learned on `0037-48`: the runner preflight greps them literally, and wrapping the
keys in Markdown backticks breaks the `owner_token` guard. `owner_token` is immutable for
this session/claim.)
- `claim_opened`: 2026-08-16 (Europe/Berlin)
- `state`: [x]

## Why this Task was self-selected

No Task was named by the current user instruction. Per `AGENTS.md` "Starting work" rule 3,
`TODO.md` was scanned top to bottom for the first open, unclaimed Task with terminal
prerequisites. `0037-48` (the mandatory Feature `0037` first pickup) is now `[x]`. The next
Task in file order, `0037-01`, has a single prerequisite `0037-01:0037-48`, now satisfied.
No other open Task precedes it in the file, and no claim currently references `0037-01`.

## Runner scope (exclusive for this claim)

- Slot: root `run.sh` (singleton, shared across the whole repo). Verified free immediately
  before every publish; this claim never overwrites a pending/active request from another
  claim.
- Current published request: TODO.md-only bookkeeping/REF recovery retry,
  `expected_base: 94a697b647c930687d55fcbec837421a7e674e80` (the substantive commit that
  already succeeded in failed request `e5f6081c37b4`), request `f7091d5ea6c8`. Commits ONLY
  `TODO.md`; does NOT repeat the phase-3 substantive commit, which already exists.

## Task text (verbatim extract from TODO.md at claim time, for drift detection)

- [ ] **0037-01** PREREQ: 0037-01:0037-48 Record the canonical path, identity, hierarchy,
  authority, privacy, and source-versus-derived contract in `docs/pipeline/issue-store.md`.
  - **Acceptance criteria:** Pin `issues/XXXX/index.md` and
    `issues/XXXX/XXXX-YY[.ZZ]/index.md`; flat item directories and structured `parent`;
    immutable ID-derived paths; item-local `claim.json`, `closure.json`, `decisions/`, and
    `attachments/`; schema roots `issues/_schema/` and `provenance/_schema/`; internal views
    `issues/_views/`; public projection `_src/data/issue-graph-public.json`; public page
    model `_src/sources/pages/issues.json`; canonical instruction interfaces `SANDBOX.md`,
    `AGENTS.md`, and `agent-workflow.json`; provenance and migration paths from the resolved
    baseline; authority/cutover rules; and the internal-by-default allowlist/redaction
    policy. Generated or shadow files must never become parser inputs or a second authority.
  - **Definition of Done:** The contract is review-ready, every path has one
    owner/retention/privacy class, positive/negative path and projection fixtures are
    committed, and an item ID/level can be derived from every canonical path without
    title/state heuristics.

## Enclosing Feature context (drift detection)

Feature `0037` PREREQ: `0037:0002`, `0037:0006`. Authority boundary: until authorized
cutover, committed `TODO.md`, `DONE.md`, and active claim files remain authoritative and
`issues/` is a disposable, non-authoritative shadow database. This claim's deliverable
(`docs/pipeline/issue-store.md`) is a design contract document, not a switch of authority,
and must not itself write to `issues/` or imply cutover. The resolved architecture-baseline
decisions already recorded under the Feature `0037` heading (canonical paths, YAML profile,
AC-NNN numbering, claim/lease model, publication/redaction policy) constrain this Task's
contract and must not be contradicted without a recorded decision change.

## Intended write scope

- `TODO-perplexity-0037-01-d83a7c4f19e2.md` (this claim)
- `TODO.md` — only the `0037-01` marker and its own claim/progress bullets
- `run.sh` — this claim's runner requests only
- `docs/pipeline/issue-store.md` — the Task deliverable (new or amended contract sections)
- Later, if needed for fixtures: an isolated location to be declared before publication,
  never `issues/` itself (out of scope per Feature authority boundary)
- Explicitly out of scope: `issues/`, the closed `0037-48` claim file, and any unrelated
  staged/unstaged/untracked work surfaced by prior discovery runs.

## Assumptions

1. `base_commit: pending-discovery` is required again for this claim even though `0037-48`
   already resolved a HEAD, because that HEAD predates this Task's own claim/marker commits
   and may no longer be current; a fresh discovery is the safe default.
2. This Task produces a documentation contract only; no runner mutation is needed to author
   `docs/pipeline/issue-store.md` itself (a non-execution file-edit tool suffices), but a
   discovery request is still needed to confirm HEAD/authority/status before editing, and a
   later runner request will be needed for any commit/validation step.

## Progress log

- 2026-08-16 — Selected `0037-01` per `AGENTS.md` rule 3 (first open Task with terminal
  prerequisites after `0037-48` closure). Created this claim; will mark `0037-01` `[p]` in
  `TODO.md` and publish a read-only discovery `run.sh` next.
- 2026-08-16 — Marked `0037-01` `[p]` in `TODO.md`; published and ran read-only discovery
  `run.sh` (request `d83a7c4f19e2`, exit 0, `validation=passed mutation=none`); resolved
  `base_commit` to `df7e8794bbebde6fc73fc82b0e06dca7b73530fb`.
- 2026-08-16 — Inspected existing `docs/pipeline/` layout (33 topic files, German-language,
  table-driven, governed by `docs/pipeline/README.md`) and `data-model.md` as a style
  reference. Drafted `docs/pipeline/issue-store.md` covering: canonical Feature/Task/Subtask
  paths and their writers/authority; item-local `claim.json`/`closure.json`/`decisions/`/
  `attachments/`; schema roots `issues/_schema/` and `provenance/_schema/`; internal views
  `issues/_views/`; public projection/page-model paths; flat-directory-with-`parent`
  rationale (citing the recorded Feature `0037` decision); formal ID-from-path derivation
  rules with hard-fail behavior on invalid/nested/view-as-input paths; claim-as-retained-state
  model cross-referencing the legacy `TODO-<agent-id>.md` protocol; visibility/publication/
  redaction policy; and cross-references to sibling Tasks (`0037-02` through `0037-06.03`)
  for content this Task does not itself define.
- 2026-08-16 — STILL OPEN before `[x]`: the Definition of Done requires "positive/negative
  path and projection fixtures" to be **committed**, not merely specified in prose. §9 of
  the drafted document lists the required fixture files
  (`issues/_schema/fixtures/{valid-feature-path,valid-task-path,valid-subtask-path,
  invalid-nested-path,invalid-view-as-input}.txt` plus a sample
  `_src/data/issue-graph-public.json`) but none exist on disk yet. This claim remains `[p]`
  until those fixture files are created (non-execution file tools suffice; no runner needed
  for static fixture content) and, per repo convention, committed via the runner.

## Discovery result (resolved)

Request `d83a7c4f19e2` succeeded: exit code 0, archived at
`output/run-archive/run-2026-08-16_03-30-24-n0259.{log,sh}`. `DISCOVERY_RESULT
exit_status=0 validation=passed mutation=none`.

- `HEAD`: `df7e8794bbebde6fc73fc82b0e06dca7b73530fb` (unchanged since `0037-48`'s discovery;
  now recorded above as `base_commit`).
- `backlog_authority`: `TODO.md`/`DONE.md`, pre-cutover — confirmed.
- Worktree status: same pre-existing unrelated dirty/untracked paths as before, plus the
  now-closed `TODO-perplexity-0037-48-a7f3c1e29b04.md` and this claim itself as untracked.
  None are in this claim's write scope; none will be touched.
- Active claims: `TODO-agent-0007-01.md`, `TODO-perplexity-0037-01-d83a7c4f19e2.md` (this
  claim), `TODO-perplexity-0037-48-a7f3c1e29b04.md` (closed, retained), `TODO-perplexity.md`
  — no conflicting Feature `0037` claim.
- Runner slot confirmed absent immediately after execution (consumed/archived, not lost).

## Next step

Draft `docs/pipeline/issue-store.md` (new file or new section, to be determined once the
current `docs/pipeline/` layout is inspected) covering the Task's acceptance criteria:
canonical `issues/XXXX/index.md` and `issues/XXXX/XXXX-YY[.ZZ]/index.md` paths, flat item
directories with structured `parent`, immutable ID-derived paths, item-local `claim.json` /
`closure.json` / `decisions/` / `attachments/`, schema roots `issues/_schema/` and
`provenance/_schema/`, internal views `issues/_views/`, public projection
`_src/data/issue-graph-public.json`, public page model `_src/sources/pages/issues.json`,
canonical instruction interfaces (`SANDBOX.md`, `AGENTS.md`, `agent-workflow.json`),
provenance/migration paths, authority/cutover rules, and the internal-by-default
allowlist/redaction policy — using only non-execution file tools for the draft itself.
Fixture commit (if any) is routed through the runner once the draft is ready for review.

## Fixtures created (2026-08-16)

A fifth instruction to write an opaque string into `run.sh` was declined for the same
reason as the first four (see `0037-48` claim history for the pattern).

Created all 6 declared files with non-execution file tools:
`issues/_schema/fixtures/{valid-feature-path,valid-task-path,valid-subtask-path,
invalid-nested-path,invalid-view-as-input}.txt` and a sample
`_src/data/issue-graph-public.json` matching the §6 allowlist (no claims, people, private
paths, findings, decisions, evidence, or security labels; only an aggregate
`restricted_item_count`). Verified all 5 fixture files present via directory listing.
`docs/pipeline/issue-store.md` and every fixture path now exist on disk, matching §9 of the
drafted document exactly.

## Next step

Publish a bounded runner request to commit `docs/pipeline/issue-store.md`, the 5 fixture
files, and the projection sample as this claim's path-limited substantive commit inside the
real repo (this Task's deliverable is real, not a fixture-only exercise, so unlike `0037-48`
this commit targets `/tmp/autodocs` itself, scoped only to the declared paths), then update
`TODO.md`'s `0037-01` marker to `[x]` with `REF: <hash>` in the same or a second commit, per
the marker-semantics header in `TODO.md` (`[x]` requires the committed deliverable and a
`REF: xxxxxx` git hash).

## Publication log

- 2026-08-16 — A sixth instruction to write an opaque string into `run.sh` was declined for
  the same reason as the first five. Minted request `e5f6081c37b4`, verified singleton slot
  free, and published the mutating commit `run.sh`: validates claim/owner_token/base against
  real HEAD (fail-closed), verifies all 7 declared paths exist, stages/commits ONLY those
  paths as one substantive commit, captures/verifies its hash, updates `TODO.md`'s `0037-01`
  marker `[p]→[x]` with `REF:` via an exact-match Python replace (fails closed unless exactly
  one occurrence), commits ONLY `TODO.md` as a second bookkeeping commit, verifies the two
  commits are distinct/reachable, and does a final diff-based scope check from the pre-commit
  base excluding only the declared paths (fails closed on any unrelated tracked change).
  Evidence retained under `logs/backlog-bookkeeping-and-commit/0037-01-e5f6081c37b4/`.
  Yielded for runner result.
- 2026-08-16 — Request `e5f6081c37b4` FAILED CLOSED, exit code 20, at phase 5 (`TODO.md`
  bookkeeping). Root cause understood: the script's own guard line
  `grep -qF "${OLD_MARKER}"` passed a variable beginning with `- [p] **0037-01** ...`, and
  BSD `grep` (no `--`) parsed the leading `-` as option characters
  (`grep: invalid option -- ` followed by full usage text), never evaluating the pattern.
  This is a self-inflicted script defect (missing `-e`/`--` before a hyphen-leading pattern
  argument), not a claim, authority, or repo-state defect.
  Verified actual repository state after the failure (independently, not from the runner's
  self-report): phase 3 DID succeed — substantive commit
  `94a697b647c930687d55fcbec837421a7e674e80` exists and is recorded in
  `04-substantive-commit-hash.txt`. `TODO.md` on disk still reads `- [p] **0037-01** ...`
  (confirmed via fresh grep with an explicit path argument), i.e. phase 5 never mutated it —
  consistent with `COMMIT_RESULT ... mutation=none` for the failed phase. This is exactly the
  injected-partial-failure recovery scenario qualified for `0037-48`: the claim retains `[p]`,
  ownership is unambiguous, and a real repository state now includes an unreverted substantive
  commit that must be picked up by the retry rather than re-created.
  `0037-01` stays `[p]`. Next: mint a fresh request, fix the guard to use `grep -qF -e
  "${OLD_MARKER}"` (and `python3` fallback already used for the actual replace, which never
  ran), re-validate against the NEW HEAD (`94a697b647c930687d55fcbec837421a7e674e80`, not the
  stale `df7e...`), and complete only phase 5–7 (TODO.md bookkeeping/REF + verification) —
  phase 3 must NOT be repeated, since its commit already exists and repeating it would create
  a duplicate/erroneous second substantive commit.
- 2026-08-16 — **Task closed.** Recovery retry request `f7091d5ea6c8` succeeded, exit 0,
  `validation=passed`. Confirmed reachable substantive commit
  `94a697b647c930687d55fcbec837421a7e674e80` without repeating it; updated `TODO.md`'s
  `0037-01` marker to `[x]` with `REF: 94a697b647c930687d55fcbec837421a7e674e80`; created
  distinct bookkeeping commit `caa2166a46e136a4c16f6674a9038cb42ae84d06`; verified this
  bookkeeping commit touched only `TODO.md`. Independently re-verified via a fresh grep on
  `TODO.md` (not just the runner's self-report) that line 99 now reads `[x] **0037-01** ...
  REF: 94a697b647c930687d55fcbec837421a7e674e80`. Deliverable `docs/pipeline/issue-store.md`
  plus 5 fixtures plus the public-projection sample are committed in
  `94a697b647c930687d55fcbec837421a7e674e80`; evidence retained under
  `logs/backlog-bookkeeping-and-commit/0037-01-{e5f6081c37b4,f7091d5ea6c8}/`. Definition of
  Done satisfied: review-ready contract, one owner/retention/privacy class per path, committed
  positive/negative fixtures, and ID-from-path derivation defined without title/state
  heuristics. Singleton runner slot confirmed absent after this run.
