---
schema_version: "1.0"
id: "0040-05"
level: "task"
parent: "0040"
state: "closed"
visibility: "internal"
prerequisites:
  - "0040-01"
  - "0040-03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:534"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0040-05:0040-01, 0040-05:0040-03 Extend the Feature-breakdown process so the `T1`–`T8` defect class is detected before implementation, and add the escalation path the autonomy rule currently suppresses. REF: `f06867e06529469e26452e9cf20d362eb0d9648e`.

## Scope

- **Claim (2026-08-18):** Project-managed checkpoint implementation via `TODO-zed-0040-05-20260818T162728Z-4c98b6072815.md`; owner_token `agent:zed:0040-05:20260818T162728Z-4c98b6072815`; branch `0040-05`; isolated worktree `.worktrees/0040-05`. Mandatory checkpoint review is reserved for joint review with the current user before upward integration.
  - **Requirements covered:** `RQ-PROC-01`, `RQ-PROC-02`, `RQ-PROC-03`, `RQ-PROC-04`.
  - **Context — the hardest part of this Feature:** `AGENTS.md` currently states that "a drafting defect … is **not** `[u]`" and instructs agents to repair and "continue the repaired Task without requesting confirmation". Under that rule an agent that had escalated the `0038-03` scope would have been in breach. The extension must therefore not simply add a duty to escalate; it must **resolve the conflict** with the existing autonomy rule, and it must do so without reopening the floodgates that rule was written to close. The distinguishing criterion is blast radius (`RQ-DEC-05`), not difficulty.
  - **Implementation completion (2026-08-18):** `DEC-0040-005` applied the proposed rule to itself before normative mutation and records a supporting scope review by a distinct management-instantiated Architect. `AGENTS.md`, the Feature-breakdown header, and `process-roles.md` now use the same canonical `cross-item-blast-radius` predicate, require a conforming decision and distinct Architect support before qualifying mutation, preserve bounded `[p]` preparation and conditional `[u]`, distinguish affirmative retention from passive inheritance, and state that green validation is insufficient scope evidence. The worked table classifies `0038-03` positive and a local validator, shared-path typo, and hypothetical ordinary bug negative. Independent implementation peer review passed after two corrections; consistency, automation safety, 42 doctor tests, and `git diff --check` passed. The global doctor retains an unrelated pre-existing policy contradiction, so no global pass is claimed.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `authority:current-user:0040-05-review:20260818T174212Z`
    - **Authority reference:** `docs/pipeline/approvals/0040-05-review.md`
    - **Accepted at:** `2026-08-18T17:42:12Z`
    - **Contract SHA-256:** `5395c75ed6ff6eb59a08f6a0948f83319e9420f9af0745d70c5d31748331d1a3`
    - **Work-product manifest SHA-256:** `f3ab09d5076b8c7a5a9b9f21195cd7b63f86268128f10b87b808c09b67ab3846`
    - **Prerequisite-acceptance SHA-256:** `1c4c7b7a30187c0b5b3758a4fbf1bb33eff3fba1c89592db94e169ac512d7bab`
    - **Review REF:** `063a85998f90197b698b9672e816ffaba7e5fb15`
  - **Integration review:** **mandatory.** **Rationale (architect):** this Task changes the binding escalation semantics in `AGENTS.md` — the rule that governs when every other agent may stop and ask. An error here either re-suppresses the escalation this Feature exists to create, or floods the user with escalations and gets ignored. It is the one node whose failure mode is invisible until it has already caused the next incident, so it is reviewed at its boundary rather than only in aggregate.

## Acceptance criteria

- **AC-001** The breakdown process requires that a Task which installs a gate capable of blocking other Tasks declares its scope as a named, justified decision under `0040-03` (`RQ-PROC-02`). It names who reviews the scope and requires that this role exist and be involved **before** implementation (`RQ-PROC-03`) — `T7` is the counter-example of record. The `AGENTS.md` autonomy rule is amended so a latent scoping defect with cross-item blast radius is an explicit escalation trigger, while difficulty, unfamiliarity and ordinary drafting defects remain non-escalating
- **AC-002** the amendment states the boundary in terms an agent can apply without judgement calls. A green validation result is explicitly named as insufficient evidence that a scope is correct (`T2`)

## Definition of Done

Committed with real `REF`; `AGENTS.md`, `TODO.md` header and the breakdown process agree; a worked walk-through shows that applying the amended process to the `0038-03` intake would have produced a recorded decision and a review, without producing a false escalation for a routine Task.
