---
schema_version: "1.0"
id: "0040-10"
level: "task"
parent: "0040"
state: "closed"
visibility: "internal"
prerequisites:
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:484"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Repair the live automation-safety blocker before further process work begins. REF: `1164a971762e51673917458fa1342ce4507dd632`.

## Scope

- **Claim (2026-08-18):** Project-managed implementation via `TODO-zed-0040-10-20260818T141307Z-894c3cd8b63b.md`; owner_token `agent:zed:0040-10:20260818T141307Z-894c3cd8b63b`; branch `0040-10`; isolated worktree `.worktrees/0040-10`.
  - **Origin:** trilateral agreement, round 5, on project management's insistence — its K.-o. criterion A2. Architect and QA manager concurred.
  - **Context:** Since 2026-08-17 the automation-safety gate reports ten unresolved critical findings plus three stale policy entries, all in `_src/run-loop.sh`, and `_src/validate.py` treats critical findings as errors. `validate-project` is the mandatory second action of every `close-task-v1` transaction, so the closure path of **every** Task is affected. This is the damage of record from `T1`–`T5`, and no other Task in this Feature repairs it — `0040-08` explicitly does not re-open `0038-03`.
  - **Implementation completion (2026-08-18):** The privileged host bootstrapper now checks cleanup, installer, self-test, pipeline, archive, and PASS-result failures explicitly. `DEC-0040-10-001` retains host code in exact static coverage; all ten original critical findings and eleven advisories are individually recorded, the three stale run-loop entries are replaced, and three current-baseline provisioner blockers discovered by the full scan are exactly dispositioned without source suppression. The final default dual-source scan passed with 71 findings, 35 disposed critical, zero unresolved critical, and zero policy errors; `bash -n`, JSON syntax, seven focused tests, consistency assertions, and `git diff --check` passed. Independent implementation peer review found no residual issue. The bounded project validator timed out after 240 seconds, so no full-project pass is claimed. This node is not an integration checkpoint; no `Acceptance: ✓` is created.
  - **Interaction with `0038-24` (recorded 2026-08-18, concurrent claim):** Task `0038-24` is `[p]` under a foreign active claim and moves `_src/run-loop.sh` into a tracked `runner-host/` package. That move does **not** resolve this Task: `automation_safety.py` selects its scan targets by file extension over all tracked paths (`tracked_automation_paths`), independently of location, so relocating the file leaves the ten findings and the exit code unchanged. The two Tasks are complementary and must not be merged. Whichever lands second updates the other's paths; this Task therefore names the file by role — *the privileged host bootstrapper* — and resolves its actual path at implementation time. No foreign scope is claimed here.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** the Task restores a previously green state and adds no capability; its result is objectively checkable (scan exits clean) and is re-examined at `0040-09`.

## Acceptance criteria

- **AC-001** Each of the ten findings is dispositioned individually: genuinely unchecked mutating calls are fixed, false positives are recorded as such with reasoning, and the three stale policy entries are refreshed against current `_src/run-loop.sh`. Where the finding is an artifact of scope rather than of the code — the privileged host bootstrapper judged by the yardstick built for sandbox-internal automation — the disposition says so and the scope decision is recorded per `TK-2`. The evidence of a full pass is retained

## Definition of Done

Committed with real `REF`; the automation-safety scan reports zero unresolved critical findings and zero policy errors; no disposition is a blanket suppression; every accepted risk is individually named.
