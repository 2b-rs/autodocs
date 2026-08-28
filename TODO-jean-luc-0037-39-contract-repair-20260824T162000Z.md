# Claim — 0037-39 contract repair

task_id: 0037-39
request_id: 20260824T162000Z
owner_token: agent:jean-luc:0037-39-contract-repair:20260824T162000Z
owner: jean-luc
state: [w]
capability_class: privileged
execution_authority: direct Shell and Git in `.worktrees/0037-39-contract-repair-jean-luc-20260824`
startup_review: DEC-0037-002 and the independent Architect review already authorize removal of the sandboxed-grunt/queue start gate from 0037-39; this repair makes the unchanged DoD consistent with that binding decision
base_commit: b32931d1dc3633934b297348aedf7b3259308b2c
branch: 0037-39-contract-repair-jean-luc-20260824
worktree: .worktrees/0037-39-contract-repair-jean-luc-20260824

## Exact write scope

- `TODO.md` — only the `0037-39` Definition of Done
- `TODO-jean-luc-0037-39-contract-repair-20260824T162000Z.md`

No implementation, Acceptance, checkpoint integration, Feature closure, deployment, or external mutation is authorized.

## Progress

- 2026-08-24: Beverly and Benjamin independently reported the stale DoD phrase requiring sandboxed-agent runner actions. Repository inspection confirmed the contradiction against the immediately preceding `DEC-0037-002 execution model` paragraph.

## Restart-recovery disposition — 2026-08-28

- `terminal: yes`; disposition-complete without a separate repair commit under this claim.
- `reason:` superseded by the governed `0037-51` execution-model rewrite at REF `f3522aaaa80d851f3ba28744b08956a52eb63275`, which is an ancestor of current `main@8948a602320c7c0781ed9a578a42b664dfd2eff4`.
- `current evidence:` Task `0037-39` now states direct item-worktree execution with optional Dispatcher-selected Runner job control and has current Acceptance at substantive REF `7dcaf135c4323bf9f566baa2d9739e02c43bf0be`.
- `handoff:` no TODO repair or implementation action remains under this owner token; lease released and claim must not be resumed.
