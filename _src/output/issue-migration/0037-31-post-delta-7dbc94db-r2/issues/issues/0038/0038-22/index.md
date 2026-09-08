---
schema_version: "1.0"
id: "0038-22"
level: "task"
parent: "0038"
state: "closed"
visibility: "internal"
prerequisites:
  - "0038-01"
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1890"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
---

## Goal

PREREQ: 0038-22:0038-01 Adapt the disposable worktree provisioner to per-item branches without owning branch policy. Claim: `TODO-seven-naomi-0038-22-20260820T013813Z.md`; owner_token: `agent:seven-naomi:0038-22:20260820T013813Z`; base_commit: `41f70cc7247c95b7f39ea91d9b424b7c4c996607`. REF: `d67412fcd`.

## Scope

- **Backlog repair (2026-08-20, `agent:seven-naomi:0038-22:20260820T013813Z`):** `_src/tools/provision_tmp_worktree.sh` carried a header marking it SUPERSEDED by Feature `0041` Task `0041-01` (`provision_worker_clone.sh`, already merged into this branch's history at `8aafc0cb4`). Investigated `docs/dossiers/re-intake-worker-isolation-and-checkin.md`: that supersession is scoped to `RQ-WT-01..06`, worker isolation for **sandboxed grunts provisioned by the privileged host side** via `git clone` (grunts cannot run Git at all). `0038-22` targets a different, still-live use case — a self-service `.worktrees/<item>` provisioner for agents that run Git themselves, matching the convention already used by `.worktrees/0019-01`, `.worktrees/0033-01`, `.worktrees/0039-01`, `.worktrees/0042-02`, etc. No `[u]` needed: rewrote the script and its header to the new scope instead of the stale single-`tmp-work`-branch content the SUPERSEDED banner described; `provision_worker_clone.sh`/`worker-clone-provisioning.md` untouched.
  - **Validation:** `python3 _src/tools/test_provision_tmp_worktree.py` — 18/18 passed (fresh provision/branch-off-parent incl. `main` fallback, idempotent re-heal without clobbering surviving uncommitted edits, directory-gone rebuild, collision refusal, reap-vs-surface-vs-claim-protect, root boundary, `--reap-only`, concurrent non-collision). `python3 _src/tools/automation_safety.py --json`: this file's 5 AUTO001 findings are `disposed critical` after refreshing their exact-digest dispositions in `_src/tools/automation_safety_policy.json`. The overall scan's remaining `exit=1` (12 unresolved critical + 3 stale dispositions) is confirmed pre-existing and entirely foreign — `_src/run-loop.sh` and `_src/tools/provision_worker_clone.sh` (Feature `0041`), neither touched by this claim; not fixed here as out of scope. Full detail in the claim file.
  - **Carried disposition (2026-08-20, repair note under `0038-14`, merged in from branch `0038-27` via `0038-14-repair`):** `automation_safety_policy.json`'s `_src/tools/provision_tmp_worktree.sh` `AUTO001` (line 27) disposition was re-pointed here from expired `0038-14`. This Task's own closure must reconcile that entry (remove it if the rewrite no longer matches, or re-disposition it) rather than leave it pointed at a Task that has itself closed — do not repeat `0038-14`'s omission.
  - **Integrator reconciliation (2026-08-20, `Seven-Tom`, privileged, dispatched by Seven, during `0038` branch consolidation — Autonomous backlog repair per `AGENTS.md`):** `0038-22`'s own `[x]` closure above refreshed the disposition's line/symbol/evidence to match its rewritten provisioner (5 entries at lines 134/165/189/201/269, replacing the single stale line-27 entry) but its branch predates architect `Seven-B'Ellana`'s `0038-14-repair` re-point decision recorded in the "Carried disposition" note directly above, so it still named `owner_task: 0038-14` — already-terminal, and now doubly stale since `0038-22` itself is also terminal, which would reproduce the identical orphaning defect `0038-14-repair` fixed once already. Determinable without a human decision: mechanically re-pointed all 5 entries' `owner_task`/`expires_after_task` from `0038-14` to `0038-16`, the identical durable-custodian precedent Task `0038-27` already established for `_src/tools/sync_to_devel.sh` under the same schema constraint (owner_task must name a currently open Task; `0038-16`'s own Definition of Done gates on "zero undispositioned critical chore findings remain"); rationale/kind/evidence text preserved verbatim plus this note appended. Verified in `_src/tools/automation_safety_policy.json`.

## Acceptance criteria

- **AC-001** Update `_src/tools/provision_tmp_worktree.sh` and its documentation to provision and idempotently heal a worktree for a caller-supplied item branch named `feature-task.subtask`, leaving the worktree location to the requesting runner's discretion and never sharing a worktree between agents
- **AC-002** base a new item branch off its parent branch
- **AC-003** and reap orphaned per-attempt scratch worktrees that match no active claim while surfacing — never deleting — any worktree that still holds uncommitted content. Worktree lifecycle only
- **AC-004** it must not create branches, merge, or make any branch/authority policy decision (owned by `0038-20`)

## Definition of Done

Idempotent re-heal after a `/tmp` reap restores a per-item worktree without clobbering surviving uncommitted edits; a scratch worktree with no active claim is reaped while one with uncommitted content is surfaced with a recovery pointer; concurrent per-item worktrees for different agents do not collide.
