# TODO-data-0044-17-worktree-lifecycle-20260828.md — active claim

task_id: 0044-17
feature_id: 0044
request_id: worktree-lifecycle-20260828
owner_token: agent:data:0044-17:worktree-lifecycle-20260828
base_commit: b42db62287c203112ded6c326fa165a7f4ee7131
capability_class: privileged
execution_authority: direct
startup_review: SANDBOX.md and AGENTS.md reviewed
write_scope: ["AGENTS.md", "TODO.md", "TODO-data-0044-17-worktree-lifecycle-20260828.md", "_src/tests/fixtures/legacy_task_doctor/cases.json", "_src/tests/test_legacy_task_doctor.py", "_src/tests/test_publish_scripts.py", "_src/tools/automation_safety_policy.json", "_src/tools/legacy_task_doctor.py", "_src/tools/legacy_task_editor.py", "_src/tools/provision_tmp_worktree.sh", "_src/tools/publish_public_site.sh", "_src/tools/test_provision_tmp_worktree.py", "docs/pipeline/branch-workflow.md", "docs/pipeline/legacy-task-doctor.md", "docs/pipeline/tools.md"]
state: [x]

## Assignment

Implement the current user's accepted lifecycle design:

- rename the exact item's `TODO-*` claim artifact to `DONE-*` when its
  Acceptance is recorded;
- let an owner remove its own clean completed worktree after the accepted
  commit is durably retained by the item branch;
- provide a conservative periodic fallback that removes only clean, unlocked,
  accepted, fully-`main`-reachable worktrees and never deletes branches or tags;
- do not remove any existing worktree as part of this implementation.

## Exact user provenance

> finde heraus, warum die Worktrees nach Abschluss nicht gelöscht werden.

> Mir fiele noch ein: Bei Item-Abschluss (acceptance) das TODO-+-item in DONE-* umbenennen. Mir gefallen 2+3. Kannst du das umsetzen? Löschen macht die Flotte selbst.

> Bring es rein.

## Intended write scope

- `_src/tools/provision_tmp_worktree.sh`
- `_src/tools/test_provision_tmp_worktree.py`
- `_src/tools/legacy_task_doctor.py`
- `_src/tests/test_legacy_task_doctor.py`
- `_src/tests/fixtures/legacy_task_doctor/cases.json`
- `_src/tools/legacy_task_editor.py`
- `_src/tools/publish_public_site.sh`
- `_src/tests/test_publish_scripts.py`
- `_src/tools/automation_safety_policy.json`
- `AGENTS.md`
- `docs/pipeline/branch-workflow.md`
- `docs/pipeline/tools.md`
- `docs/pipeline/legacy-task-doctor.md`
- `TODO.md`
- `TODO-data-0044-17-worktree-lifecycle-20260828.md`

No existing worktree, branch, tag, claim, or uncommitted data may be deleted by
this implementation session. Acceptance remains independent.

## Next step

Hand exact candidate tip `99993cb123d15710fcd346444724e179a726cbaf`
(substantive REF `635b9c810dc9fc2ed602116dbd13fba39c2b634d`) to an
independent privileged Integrator for the mandatory checkpoint. Do not
self-accept, integrate, finalize this claim to `DONE-*`, or remove this
worktree before that Acceptance.

## Completion evidence

- Substantive REF: `635b9c810dc9fc2ed602116dbd13fba39c2b634d`.
- Candidate refreshed with current `main@6b35e9af521154ec29962d7698dc72d76598bd23`
  by merge commit `99993cb123d15710fcd346444724e179a726cbaf` after the substantive commit; no overlap or
  conflict touched the lifecycle scope.
- `_src/tools/test_provision_tmp_worktree.py -v`: 32/32 passed. Covered exact
  accepted-item rename, unrelated historical-claim preservation, collision and
  missing-Acceptance refusal, acceptance on a distinct Feature branch, explicit
  owner removal with branch retention, live-CWD/dirty/locked/active-claim
  refusal, safe main-reachable fallback, and retention of claimless, unmerged,
  unaccepted, dirty, locked, outside-root, and current-target worktrees.
- `_src.tests.test_legacy_task_doctor`: 59/59 passed; accepted `DONE-*` remains
  parseable and premature `DONE-*` is rejected without retroactively forcing
  migration of historical accepted `TODO-*` claims.
- `_src.tests.test_legacy_task_editor`: 54/54 passed.
- `_src.tests.test_publish_scripts`: 12/12 passed, including exclusion of
  `DONE-*` claim provenance from the public export.
- `bash -n`, Python compilation, both changed JSON documents, and
  `git diff --check`: passed.
- `process_doc_doctor`: candidate and `main` baseline both 154 documents,
  32 findings, 1 pre-existing `DOC001` error at
  `docs/dossiers/0044-03-gate-scope-proposal.md`; no delta.
- Live `legacy_task_doctor` reports no finding for `0044-17`; repository-wide
  legacy debt remains pre-existing and is not represented as clean.
- The seven `provision_tmp_worktree.sh` AUTO001 tuples were recomputed against
  the changed bytes and bound to open integrating Task `0044-08`; no claim is
  made that the slow full-repository automation scan completed (it was stopped
  after exceeding three minutes without output).
