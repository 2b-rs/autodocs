# Recovery claim — shared Git worktree contamination

- `owner_token`: `agent:jean-luc:recovery-core-worktree:20260824T231259Z`
- `capability_class`: `privileged`
- `authority`: current user, 2026-08-25 — “ok. Aus dem Fehler lernen und weitermachen.”
- `branch`: `recovery-core-worktree-jean-luc-20260825`
- `worktree`: `.worktrees/recovery-core-worktree-jean-luc-20260825`
- `base_commit`: `2dae2a088d54b950908edcbc31c5f4402a078750`
- `status`: snapshot preserved; root restoration and integration pending

## Scope and evidence

The shared `.git/config` had been rewritten by a fixture run that inherited the
real repository `GIT_DIR` and a temporary `GIT_WORK_TREE`. The exact mechanism
was reproduced in `/private/tmp/core-worktree-repro.E1Iq5v`. Before repair, the
configuration SHA-256 was
`767a3281bcb864f34a50674221717072d11693211c3d7cf1e4a80e20280419bb` and
contained only these reproduced contaminants:

- `core.worktree = /private/tmp/troy-0046-06-r2.NlZxX8`
- `user.name = WTP Test`
- `user.email = test@example.invalid`

The current-user-authorized repair removed exactly those three entries, retained
the signing key and SSH command, and saved the original configuration at
`/private/tmp/autodocs-git-config-pre-repair-20260825-767a3281`. Normal Git now
resolves `/Users/tobias.anton/devel/autodocs` as the top level; `main` remains at
the base above and the shared index tree still equals `HEAD`.

The physical root also carried three tracked, unstaged divergences which exist in
no reachable commit. Before any root clearing, this branch captures all three
verbatim and tags the capture as
`preserved/root-git-config-incident-20260825-jean-luc`. The roster addition and
the two memory lines are preserved as evidence only; their presence here grants
no authority and they are not adopted into `main` by the recovery candidate.

Snapshot REF: `1252503ae1cdcad5b387d2351965da9063964d3f`.
The preservation tag resolves to that exact commit. The child recovery commit
removes all three snapshot-only contents and retains only this claim plus the
exact registry row.

## Write scope

- this claim;
- `docs/pipeline/branch-workflow.md`, only the preserved-tag registry row;
- snapshot-only copies of `docs/pipeline/agent-roster.md`,
  `logs/agent-memory/agents/benjamin.md`, and
  `logs/agent-memory/roles/Architect.md`.

No Task Acceptance, checkpoint, Feature closure, `DONE.md`, external service,
push, or unrelated cleanup is authorized. The three snapshot-only changes are
removed again on this branch after the preservation tag is created. The physical
root is restored only after the tag and exact registry record are durable.
