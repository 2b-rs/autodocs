# Requirements baseline — team-independent pause and phase-out

## Scope and evidence

This baseline derives from the two material prompts in `team-pause-phaseout-management-direction.md`, `DEC-0050-001`, and read-only inspection of `agent-inbox/main@b94b609e2a7d8d572cdbef091894156e0ac52f38`.

Pinned evidence:

- `assignment-state-machine.json` SHA-256 `90bd979f34ebff16e49c36f2a697380194eb0bfeade78d823b986a144da2f30e`;
- `supervisor.py` SHA-256 `e526cc06d65c4ab6da0bd5602227ea50049f5073fd03991b802b610c91d25847`;
- `agent_inbox_mcp.py` SHA-256 `3d54740417c7041b011ad5056b6da3706e4fdd4ca81dc5d68e0dc1475e610c9d`;
- `supervisor-gui.py` SHA-256 `a378e22a8efeb6329aebc3ef15bbdcf7e9b23805459e44f4af923feb6887f9b7`.

The agent-inbox checkout had unrelated local modifications during inspection; all evidence above is from the committed tree, not working-tree bytes.

## Functional requirements

- **REQ-0050-01 — Atomic admission block.** A pause request increments a team pause generation and atomically prevents delivery or acceptance of new offers by every current team member.
- **REQ-0050-02 — Pre-award freeze.** Unresolved offer rounds containing affected candidates are frozen without silently advancing tiers; unaffected candidates may proceed only when the offer contract explicitly permits a team-independent remainder.
- **REQ-0050-03 — Drain visibility.** Every nonterminal awarded assignment for an affected member is projected as `draining` with coordinator, deadline, last evidence time and handoff state; it is not silently cancelled.
- **REQ-0050-04 — Bounded checkpoint chance.** A running contractor receives a bounded handoff/checkpoint window and may record committed work, WIP preservation, claim state and intended successor without extending ownership indefinitely.
- **REQ-0050-05 — Team lifecycle.** Team states are `active`, `pausing`, `draining`, `quiesced` and `resuming`, bound to a monotonic generation and append-only events.
- **REQ-0050-06 — Zero proof.** `quiesced` requires authoritative empty sets for deliverable pre-award notices, nonterminal awards, unresolved delegation/rework children, and live repository claims, plus a retained digest/receipt.
- **REQ-0050-07 — Typed escalation.** At the assignment or drain deadline, Supervisor emits one idempotent escalation to the accountable coordinator and records delivery or retry state.
- **REQ-0050-08 — Evidence snapshot.** Coordinator action binds assignment state, last response/turn, quota evidence with age and `known|unknown|stale`, commits, claims, worktrees, retained logs and handoff progress.
- **REQ-0050-09 — Reasoned outcome.** A coordinator records exactly one of `extend_bounded`, `keep_or_complete`, `place_on_hold`, `delegate_atomically`, or `cancel_or_revoke`; each outcome has reason, actor, evidence digest, deadline/generation preconditions and recovery action.
- **REQ-0050-10 — Reclamation authority.** Contractor response is not required after the deadline, but silence, exhaustion or stale quota never proves absence of work and never authorizes automatic data destruction.
- **REQ-0050-11 — Ownership exclusivity.** The current contractor remains responsible until a replacement accepts atomically, unless a prior recorded cancellation/revocation closes ownership; compare-and-swap prevents dual winners and duplicate starts.
- **REQ-0050-12 — Preservation.** Reclamation preserves reachable commits and bounded WIP snapshots where possible; failure records exact paths/errors and leaves evidence intact for separately authorized recovery.
- **REQ-0050-13 — Bounded extension.** Extension count and cumulative duration are policy-bounded; exceeding either bound re-escalates and requires a non-extension outcome.
- **REQ-0050-14 — Blackout convergence.** Emergency provider blackout may shorten checkpoint waits but uses the same evidence, ownership, preservation and successor receipts; it cannot create an unrecorded hard-reclaim bypass.
- **REQ-0050-15 — Explicit resume.** Resume increments generation, re-enables admission only after validation, and never reassigns or resurrects reclaimed work automatically.
- **REQ-0050-16 — GUI and API parity.** GUI and MCP/API expose the same generation, deadlines, evidence, decisions and validation errors; dashboard state is a projection, never authority.
- **REQ-0050-17 — Accountability.** Views show active, draining and overdue counts and the accountable coordinator per assignment and team.
- **REQ-0050-18 — Idempotence and recovery.** Every pause, escalation, outcome, quiescence and resume command has an idempotence key and deterministic restart fold; partial appends cannot yield contradictory current state.
- **REQ-0050-19 — Privacy and minimization.** Evidence snapshots store references/digests and bounded metadata, not mailbox bodies, secrets, raw prompts, full logs or unnecessary personal data; access follows existing assignment visibility.
- **REQ-0050-20 — Audit and rollback.** Append-only events retain who requested, decided, preserved, delegated, revoked, quiesced and resumed; rollback/supersession is additive and never deletes history.

## Required record fields

The versioned record set must carry: `team_id`, `pause_generation`, `state`, `requested_at`, `requested_by`, `reason`, `drain_deadline`, per assignment `coordinator`, `check_at`, escalation event/delivery, evidence snapshot/digest, decision/outcome, successor, preservation ref/status, `quiesced_at`, and `resume_generation`. Timestamps are UTC; IDs are opaque; generations are monotonic integers.

## Verification requirements

The required matrix covers every configured team, mixed providers, pause versus offer-accept races, handoff then quota exhaustion, exact deadline boundaries, stale/unknown quota, recovery before and after revocation, ignored/misread and repeated escalation, extension abuse, delegation race, WIP preservation failure, restart during drain, stale claims, resume and zero proof. Set and sequence invariants require exhaustive finite-state or property evidence with replay inputs and case counts.
