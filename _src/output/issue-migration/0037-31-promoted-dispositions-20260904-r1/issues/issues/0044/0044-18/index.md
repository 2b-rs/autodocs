---
schema_version: "1.0"
id: "0044-18"
level: "task"
parent: "0044"
state: "open"
visibility: "internal"
prerequisites:
  - "0044-04"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1285"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0044-18:0044-04 Roll out priority-gated atomic chain awards for multi-Dispatcher coordination. *(privileged implementer; implementation identity distinct from the mandatory Integrator)* **REF:** `059e5e98b0b0d6b2441a624d73dc4f15fdd89fee`. Claim: `TODO-benjamin-0044-18-20260829.md`.

## Scope

- **Integration review (2026-08-29, Integrator `obrien`, independent of Implementer `benjamin` and Architect `saru`):** Checkpoint passed; DEC-0044-032 dossiers and rollout preparation evidence integrated. Review REF: `f95e331d55653db3c6046e7f8d3fa8f5c3da4ae9`; Review evidence: `docs/campaign-evidence/0044-18/integration-review-obrien-20260829.md`. Task Acceptance deferred to feature integration.
  - **Authority and source baseline:** Current-user Management instruction of 2026-08-28 to let Project Leads split work into independently executable chains, state start/wait/checkpoint conditions, and award each chain through ordered Dispatcher priority groups with minimal messaging overhead. External mechanism baseline: `agent-inbox` main REF `2983630f7f4d5cae697e0fbf82198358a577f0ec` (`agent-inbox` server v1.11.0).
  - **Required semantics:** A Project Lead creates exactly one live `offer` round per item/chain and may create separate rounds for independent chains in parallel. Equal candidates share a numeric priority; only the active lowest-numbered tier receives a notice. Only that tier may call `offer_reply`; its first successful `accept` is the serialized, atomic `AWARDED` result and the sole start authority. Competing active notices become `ALREADY AWARDED` before their next inbox read. Lower tiers receive nothing until every active candidate declines or the Project Lead advances an expired deadline through `offer_control`. `offer_status` inspects state without coordination mail.
  - **Chain contract:** Every round names the exact ordered items, branch/worktree and write scope, planned duration, reply window, authority reference, and all `start when`, `wait for`, prerequisite, checkpoint, merge-point and stop conditions. A frontier entry, free-form `OFFER` mail, or another Dispatcher's activity is planning context, never an award.
  - **Role multiplicity:** Several Project Leads or Dispatchers in one team are concurrent capacity, not primary/backup identities. An award assigns only its item/chain; it never transfers the role, retires a peer, or puts a peer on standby. `delegate` means temporary work coverage only. Independent chains should be awarded to different available Dispatchers when capacity permits; one chain still has exactly one winner.
  - **Migration and activation:** Update the binding autodocs coordination instructions, role descriptions, tool catalog, generated roster/profile guidance, and executable conformance tests to the new `offer`, `offer_reply`, `offer_status`, and `offer_control` contract. Existing already-open legacy message rounds finish under their pinned briefing; all rounds created after the activation commit use the priority tools. Activation is fail-closed per runtime: before creating a new round, prove the coordinator and candidates expose the v1.11.0 tools; if not, refresh/restart the affected runtime and report the unavailable mechanism rather than silently emulating an atomic award with `send`.
  - **Validation matrix:** Exercise (1) priority 1 = Worf or Benjamin and priority 2 = other Dispatchers, proving priority 2 receives no initial mail; (2) all priority-1 declines activate priority 2; (3) simultaneous accepts produce exactly one winner and a terminal already-awarded result for the loser; (4) two independent chains can be awarded concurrently to different Dispatchers; (5) early deadline advance, duplicate live round, duplicate candidate, and standby/exhausted/retired candidates fail closed; and (6) generated profiles remain current when produced from the canonical `agent-inbox` root.
  - **Integration review: mandatory.** **Rationale (architect):** Architect `data`, 2026-08-28 — this changes the fleet-wide assignment state machine and the only start-authority signal for parallel work. A defect can duplicate execution, hide eligible capacity, or violate prerequisite/checkpoint ordering across teams, so an independent privileged Integrator must verify both the governance projection and the executable race/failure-path evidence before activation.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

The operative autodocs documents agree on the state machine and chain rules; no prose still instructs a coordinator to use manual first-accept-wins `AWARD`/`WITHDRAWN` exchanges for new work; role/capability authority is unchanged; the external baseline and runtime-reload evidence are pinned; the full relevant process/tool tests pass; and an end-to-end two-chain pilot records exact offer IDs, winners, hidden-tier evidence and absence of duplicate starts without placing an unawarded peer on standby.
