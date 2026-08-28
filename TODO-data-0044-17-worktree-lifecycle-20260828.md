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
state: [p]

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

Finish validation, commit the bounded implementation, mark `0044-17` `[x]`
with the real REF, and hand the mandatory checkpoint to an independent
privileged Integrator without self-acceptance or integration.
