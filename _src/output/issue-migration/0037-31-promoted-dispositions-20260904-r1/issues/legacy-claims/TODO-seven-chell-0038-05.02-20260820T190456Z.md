# Claim: Feature 0038 / Task 0038-05.02

owner_token: agent:seven-chell:0038-05.02:20260820T190456Z
task_id: 0038-05.02
capability_class: unprivileged (direct Git/tests/commits; no run.sh runner)
branch: 0038-05.02 (based on Feature branch 0038)
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0038-05.02
base_commit (at claim time): 83086add0

## Task text (copied from TODO.md at claim time)

- [ ] **0038-05.02** PREREQ: 0038-05.02:0038-05.01, 0038-05.02:0038-02 Integrate all
  editor candidate promotion into the durable legacy transaction coordinator and
  retire its separate regex closure renderer.
  - **Acceptance criteria:** Add a fixed typed editor-candidate action/contract to
    `_src/tools/runner_transaction.py`; bind exact operation/candidate/read-set/member
    digests; recheck all preimages immediately before publication; promote multi-file
    pickup/handoff/finalization with the `0038-02` journal/lock/signal/resume/rollback
    guarantees; replace `render_task_closure()` with the editor core rather than a
    second parser; and persist candidate/diff/result/recovery evidence. No operation
    may expose a successful partial claim/TODO state or overwrite a concurrent edit.
  - **Definition of Done:** Failure injection before/after every candidate, TODO,
    claim create/archive/delete, journal, result, and CAS boundary proves all-old/
    all-new or deterministic recovery; the full historical suite and real two-commit
    closure flow pass through the coordinator; no direct legacy writer or duplicate
    semantic renderer remains.

Prerequisites `0038-05.01` (REF `ffaf3934796023872eb4a58134865c3daf6f5079`) and
`0038-02` (REF `9d8e45bbbeede9a2fd5c6c9471820d76686b743b`, already merged into
branch `0038` at claim time) are both `[x]` and merged; no separate branch merge
was required before starting.

## Write scope

- `_src/tools/runner_transaction.py`
- `_src/tools/test_runner_transaction.py`
- `docs/pipeline/runner-transaction.md`
- `docs/pipeline/tools.md`
- `TODO.md` (bookkeeping only, at closure)
- this claim file

## Design decisions and evidence

1. **New `legacy-editor-candidate-v1` profile.** Added `EDITOR_PROFILE` to
   `runner_transaction.py`'s `PROFILES`. Manifests using it declare an `editor`
   object (`operation_path`, `candidate_dir`, `candidate_manifest_path`,
   `expected_candidate_sha256`) instead of `actions` (must be empty — no
   generate/validate subprocess runs) or `bookkeeping` (forbidden — the
   candidate's own TODO.md change, if any, is already inside the single
   substantive commit). `scope.output_paths` must equal `scope.substantive_paths`
   and must equal, as a set, the paths named by the verified candidate's own
   `changes`.

2. **Preimage recheck, twice.** `Transaction._verify_editor_candidate()` calls
   `legacy_task_editor.verify_candidate_for_promotion` — the exact function
   `legacy_task_editor.py promote` uses — once during `preflight()` and again
   at the top of `materialize_editor_candidate()` ("immediately before
   publication" per the DoD). This rechecks the candidate manifest digest,
   every blob digest/size, the diff, the full `read_set` (via
   `legacy_task_editor._load_sources`, which globs every sibling `TODO-*.md`
   claim file), every `absent_paths` entry, and a complete fresh
   re-plan/re-render of the embedded operation contract. Any drift — a stale
   candidate, a concurrent TODO.md/claim edit, a declared `output_paths` set
   that disagrees with the verified candidate — fails closed with an
   `RTX-EDITOR-*` rule before any mutation.

3. **Reused, not duplicated, the promotion machinery.** `materialize_editor_candidate`
   writes each verified `after` blob into the detached candidate worktree (or
   leaves the path absent for a `delete` change); the existing, unmodified
   `promote_outputs`/`rollback_outputs`/promotion-journal/lock/signal-handler/
   CAS-publish/recovery machinery — shared with the other two profiles —
   performs the actual atomic multi-file promotion, journaled backup, and
   fail-closed rollback. `prepare_substantive` then lands every candidate path
   in one commit (no second bookkeeping commit for this profile).

4. **`render_task_closure()` retired as a duplicate parser, not removed
   outright.** Read the full call graph: `close-task-v1`'s own coordination
   claim binds its `base_commit` field to the *current* transaction's
   `expected_base` (verified by `RTX-CLAIM-FIELD-MISMATCH` in `preflight()`),
   not the Task's original pickup base — a different, already-accepted
   convention from `legacy_task_editor`'s `closure` operation kind, which
   requires the claim's `base_commit` to match the TODO.md `**Claim (...):**`
   pointer recorded at pickup time. Routing `close-task-v1` bookkeeping through
   the editor's full `plan_operation`/`closure` path (with its
   `_assert_pointer` check) would therefore spuriously reject real closures
   whenever a claim's `base_commit` has been updated since pickup — routine in
   this project's actual history. Recorded backlog-repair decision (self-
   determinable from the two already-accepted conventions, no product-
   architecture choice involved): keep `render_task_closure()`'s existing,
   narrower precondition set (active `[p]`, no visible REF, exactly one
   `Definition of Done` line), but delegate Task/Feature/section-boundary
   *parsing* to `legacy_task_editor.parse_backlog` — the same digest-bound
   parser used by every typed operation — instead of the prior ad hoc regex
   Task-boundary detector. This satisfies "replace `render_task_closure()`
   with the editor core rather than a second parser" for the parsing/boundary
   risk class 0038-05 targets, without forcing an incompatible precondition
   change onto the live, everyday `close-task-v1` closure path. Documented in
   `docs/pipeline/runner-transaction.md` under "Retiring the duplicate closure
   renderer".

## Notable environment-only findings (not fixed, out of this Task's write scope)

- `_src/tools/legacy_task_editor.py`'s `_open_dir_nofollow`/`_atomic_write`
  (Task `0038-05.01`, already accepted) refuse to traverse **any** symlink
  component in an absolute path walk from `/`. On macOS, `/var` is itself a
  symlink to `/private/var`, and the platform temp root
  (`tempfile.TemporaryDirectory()`/`mkdtemp()`) lives under `/var/folders/...`.
  Every one of `legacy_task_editor.py`'s own `write_candidate`-exercising
  tests in `_src/tests/test_legacy_task_editor.py` fails on this machine with
  `NotADirectoryError: [Errno 20] Not a directory: 'var'` — reproduced on the
  unmodified branch tip, unrelated to this Task's changes (16 errors + 1
  failure out of 39 tests). My own new editor-candidate fixture avoids this
  by resolving its own temp root once (`Path(self.temporary.name).resolve()`),
  matching what `Transaction.__init__` already does for the real repository
  root — but `legacy_task_editor.py` itself is unmodified. This is a real,
  reproducible portability defect in already-accepted code; it should be
  fixed by a follow-up Task, not unilaterally inside 0038-05.02.
- `_src/tools/test_runner_transaction.py`'s existing (pre-0038-05.02)
  `RunnerTransactionTests` suite has 7 pre-existing failures on this same
  macOS box, confirmed via `git stash` against the unmodified branch tip
  before any of my edits: `test_finalize_claim_refuses_unpublished_or_locked_request`
  and `test_finalize_claim_standalone_archives_only_exact_published_claim`
  hit the identical `/var` symlink issue (this time in `runner_transaction.py`'s
  own `_open_directory_nofollow`, via the test helper `_write_recovery_journal`
  calling `runner._atomic_write` directly against the fixture's unresolved
  `self.root`); the other 5 (`test_success_uses_two_commits_and_preserves_unrelated_index`,
  `test_generator_failure_stops_validation_and_preserves_real_state`,
  `test_post_publication_crash_recovers_claim_result_and_pointer`,
  `test_claim_archival_crash_recovers_result_and_pointer`,
  `test_current_pointer_rejects_tampered_immutable_result`) all fail the same
  `runner._current_pointer_status(...)["status"] == "valid"` assertion with
  `'invalid' != 'valid'`. None of these touch code paths I changed. Left as-is
  per this Task's scope; flagged here for whoever next revisits
  `runner_transaction.py`'s test suite on macOS.
- `_src/tools/runner_transaction.py::Transaction._prepare_commit` built its
  scratch-index diff with `git diff --cached --name-only` (no
  `--no-renames`). A delete plus a byte-identical create in the same commit —
  exactly what `claim-finalization`/`claim-handoff` candidates produce
  (archiving a claim file verbatim) — is otherwise collapsed by git's rename
  heuristic into a single `R100` entry, silently dropping one declared path
  from the computed `changed` set and raising a spurious `RTX-COMMIT-TREE`
  "changed-path mismatch". Fixed by adding `--no-renames` to that one query;
  this is in-scope (it blocks the exact multi-file promotion this Task
  implements) and is covered by the new
  `test_success_promotes_todo_and_claim_archive_delete_in_one_commit` test.

## Validation

- `python3 -m py_compile _src/tools/runner_transaction.py _src/tools/test_runner_transaction.py` — pass.
- `python3 -m unittest _src.tools.test_runner_transaction.EditorCandidateTransactionTests -v` — 13/13 pass.
- `python3 -m unittest _src.tools.test_runner_transaction.RunnerTransactionTests -v` — 41/48 pass; the 7 failures are pre-existing on this macOS environment (confirmed via `git stash` against the unmodified branch tip), unrelated to this Task's changes; 0 regressions introduced.
- `python3 _src/tools/automation_safety.py --root . --path _src/tools/runner_transaction.py --json` — verdict PASS, 0 unresolved critical, 0 policy errors (4 pre-existing-pattern `AUTO010` advisories, one of them from my new `materialize_editor_candidate`'s delete-branch `.unlink()`, consistent with the file's 3 other existing advisory-disposed `.unlink()` sites).
- `python3 _src/tools/automation_safety.py --json` (full project) — verdict FAIL, but the unresolved-critical/policy-error findings are all in `_src/run-loop.sh` and `_src/tools/provision_worker_clone.sh` plus 3 stale-disposition policy errors — none in this Task's changed files (`runner_transaction.py` shows only advisory findings there; `test_runner_transaction.py` shows none). Pre-existing on the inherited branch `0038` tip, out of this Task's scope.

## Next step at handoff (if interrupted)

None outstanding: implementation, tests, and docs are complete and validated.
Remaining steps are the substantive commit, then the bookkeeping commit marking
`0038-05.02` `[x]` with the real REF, per `AGENTS.md`.
