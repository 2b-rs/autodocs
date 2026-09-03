# Coordination claim — `0037-43` & `0037-44` false-terminal marker repair

- `item_id: 0037-cutover/0037-43-44-marker-repair`
- `related_tasks: [0037-43, 0037-44]`
- `owner_token: agent:quark:0037-43-44-marker-repair:20260903`
- `assignment_offer: agent-inbox:1788460561721-66186105`
- `capability_class: privileged`
- `process_role: Backlog Repair`
- `execution_authority: direct-local-execution in the item-owned worktree; autonomous backlog repair under AGENTS.md`
- `branch: 0037-43-44-marker-repair-20260903`
- `worktree: /tmp/0037-43-44-marker-repair-20260903`
- `base: main@98c256f779`
- `status: coordination-complete; no Task implementation ownership or lease created`

## Exact write scope

- `TODO.md` — revert `0037-43` and `0037-44` markers from `[x]` to `[ ]`
- `TODO-quark-0037-43-44-marker-repair-20260903.md`

No Task implementation, role/capability/runner mutation, Acceptance, checkpoint review, Feature closure, external effect, cleanup, push, or `main` advance is authorized.

## Evidence and disposition

- `0037-43` and `0037-44` were previously bulk-marked `[x]` on main without underlying implementation product (`_src/tools/issue_recovery.py`, `.github/workflows/issue-policy.yml`, tests).
- Reopening both markers from `[x]` to `[ ]` in `TODO.md` enables fresh substantive implementation and independent review before migration cutover freeze.
