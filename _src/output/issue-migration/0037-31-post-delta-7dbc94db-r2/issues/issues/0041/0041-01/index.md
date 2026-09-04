---
schema_version: "1.0"
id: "0041-01"
level: "task"
parent: "0041"
state: "closed"
visibility: "internal"
prerequisites:
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1324"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Replace the shared-checkout provisioner with a clone-based one that the privileged host runs per assigned item. REF: `8aafc0cb4`. Claim: `TODO-seven-naomi-0041-01-20260821T000000Z.md`; owner_token: `agent:seven-naomi:0041-01:20260821T000000Z`.

## Scope

- **Closure (2026-08-21):** Substantive delivery (`_src/tools/provision_worker_clone.sh`, `docs/pipeline/worker-clone-provisioning.md`) was already committed at `8aafc0cb4` but never bookkept. Independently re-verified all acceptance criteria and DoD points against a disposable throwaway repo under `/tmp` (never against the canonical repo or a tracked worktree): correct branch/parent derivation with `main` fallback and explicit notice, isolated clone with its own object store/refs/HEAD/index, canonical `git status`/`HEAD` byte-identical before/after, idempotent rerun, `.git`-symlink refusal, and registered-worktree refusal — all passed. `provision_tmp_worktree.sh` was confirmed rescoped (not left as a silent second mechanism) by the independent `0038-22` repair to a disjoint self-service scenario, with an explicit disclaiming header naming this script. `docs/pipeline/worker-clone-provisioning.md` documents who runs it and when. No test suite exists for the script, but the Task's Definition of Done does not require one (unlike `0041-06`'s), so this is not a gap. No fix was required; see claim for full evidence.
  - **Requirements covered:** `RQ-WT-01` … `RQ-WT-05`.
  - **Context:** `_src/tools/provision_tmp_worktree.sh` currently calls `git worktree add` on a hard-wired `tmp-work` branch, and its header advertises as a benefit that commits are "instantly durable" in the shared object store. That coupling is precisely the cause of the trigger (finding J). The clone deliberately gives it up: durability now begins at push.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** the change is confined to provisioning of a disposable checkout and is objectively checkable (canonical tree unaffected); it is re-examined at `0041-05`.

## Acceptance criteria

- **AC-001** The provisioner takes the item ID as input, creates the branch from its correct parent per `branch-workflow.md` when absent, and provisions the worker checkout by `git clone` with its own object store, refs, `HEAD` and index. Running it leaves `git status` in the canonical tree unchanged — proven by a before/after comparison retained as evidence. It refuses to run when the target path is a `.git` symlink or a registered worktree of the canonical repository, and says which it found. It stays idempotent and must not discard uncommitted worker edits that survived a `/tmp` reap

## Definition of Done

Committed; the old shared-checkout path is removed or explicitly refused rather than left as a silent second mechanism; the header comment no longer advertises shared-object-store durability; `docs/pipeline/` documents who runs it and when.
