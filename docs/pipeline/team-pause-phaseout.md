# Team pause, drain and phase-out architecture

## Boundary

This contract is non-operative until `0050-00` binds `DEC-0050-001`, the requirements digest and a supporting distinct Architect scope review. It defines interfaces for agent-inbox implementation; it does not itself pause a team, mutate live Supervisor state, cancel work, or authorize release.

## State and ownership model

Each team has one monotonic `pause_generation` and one folded state:

`active → pausing → draining → quiesced → resuming → active`.

`pausing` is entered by the atomic admission transaction. `draining` begins when the frozen inventory contains any nonterminal award or live claim. `quiesced` requires the zero-proof receipt. `resuming` validates that no stale-generation offer can accept before the new active generation is published.

Assignment ownership remains the existing atomic-award ownership. `draining` is a projection layered over `awarded|in_progress|on_hold|review|rework`, not a replacement that loses the prior state. A delegation child cannot make the parent owner-free: responsibility moves only on child ACCEPT, or closes first through a recorded cancellation/revocation.

## Append-only records

1. `team_pause_requested@v1`: team, generation, actor, reason, request time, drain deadline, idempotence key and roster digest.
2. `team_pause_inventory@v1`: exact frozen offer, assignment, child-offer and claim identities plus source revisions/digests.
3. `assignment_drain_checkpoint@v1`: coordinator, contractor, check time, handoff deadline and checkpoint/preservation references.
4. `assignment_deadline_escalation@v1`: exact deadline, evidence classification, accountable coordinator, delivery attempts and idempotence key.
5. `assignment_reclamation_decision@v1`: evidence digest, exactly one outcome, reason, precondition generation/state, successor/preservation fields and recovery action.
6. `team_quiescence_receipt@v1`: empty-set manifests, source revisions, legacy-reconciliation receipts, digest and `quiesced_at`.
7. `team_resume@v1`: prior pause generation, new resume generation, actor, reason and validation receipt.

Events append under the same mailbox lock used by offer and assignment transitions. Folding rejects missing parents, generation regression, duplicate semantic idempotence keys, two outcomes for one escalation, or a successor start without an accepted child or closed prior owner.

## API surface

- `team_control(action=pause|resume, team, reason, drain_deadline, idempotence_key)` creates the generation transaction or returns the identical prior receipt.
- `team_status(team, generation?)` returns authoritative sets, counts, coordinator accountability and zero-proof readiness.
- `assignment_drain_checkpoint(offer_id, preservation_ref?, handoff_state, reason)` records bounded contractor progress without deciding reclamation.
- `assignment_reclamation_decide(offer_id, escalation_id, evidence_digest, outcome, ...)` is coordinator-only and compare-and-swap guarded.
- Existing `offer`, `offer_inbox`, `offer_reply`, `offer_control` and `assignment_transition` call a shared `team_admission_guard` and append compatible lifecycle events; no parallel unguarded path remains.

Errors are stable: `TEAM-PAUSED`, `TEAM-GENERATION-STALE`, `DRAIN-DEADLINE-NOT-REACHED`, `EVIDENCE-STALE`, `OUTCOME-DUPLICATE`, `EXTENSION-BOUND`, `OWNERSHIP-COLLISION`, `PRESERVATION-UNVERIFIED`, and `ZERO-PROOF-INCOMPLETE`.

## Pause transaction

Under one lock: validate actor/team/deadline; increment generation; append request; close affected candidate notices; freeze active pre-award rounds without advancing tiers; snapshot authoritative assignments and claims; append inventory; mark each award draining; schedule coordinator `check_at`; persist before publishing notices. A crash before persistence has no visible effect; a crash after persistence replays notices idempotently.

Offer acceptance carries the candidate's observed generation. The guard compares it with the current team generation and state inside the same acceptance lock. A concurrent pause wins or the accept wins, never both: if pause wins, acceptance returns `TEAM-PAUSED`; if accept wins, the new award appears in the pause inventory/drain fold.

## Deadline escalation and decision

Supervisor derives `check_at` from the assignment due time and team drain deadline and emits a typed escalation once per `(offer_id,generation,deadline)`. The evidence snapshot records values and age; quota is `known`, `unknown`, or `stale`, never silently zero. Delivery failure remains retryable and visible.

The coordinator must inspect the snapshot and choose one outcome:

- `extend_bounded`: new due/check time within count and cumulative-duration caps;
- `keep_or_complete`: retain owner or accept already-reviewed completion with ordinary authority checks;
- `place_on_hold`: preserve prior state and stop active execution without releasing ownership;
- `delegate_atomically`: open a bounded offer while the contractor remains responsible until ACCEPT;
- `cancel_or_revoke`: close ownership, bind preservation result and explicitly reopen/re-offer or disposition the item.

Supervisor re-escalates missing coordinator action. It never chooses the product outcome. Escalation is operational routing, not a Management decision request.

## Blackout compatibility

Provider blackout can set a shorter emergency `check_at` and use a healthy coordinator, but it produces the same inventory, evidence, decision, preservation and ownership receipts. “Losing unpushed results is accepted” is superseded for this lifecycle: preservation may fail, but the failure is recorded and no automatic deletion follows. Recovered providers do not regain reclaimed assignments.

## GUI projection

Team cards show state/generation, pause reason/requester, drain deadline, active/draining/overdue counts and zero-proof status. Assignment rows show accountable coordinator, `check_at`, escalation delivery, evidence freshness, handoff/preservation state, chosen outcome and successor. Controls call the canonical APIs and surface stable errors; existing process `stop/start` remains runtime control and is not presented as team quiescence.

## Recovery, migration and rollback

Startup folds the append-only journal, recomputes inventories from exact source revisions, resends undelivered escalations, and refuses quiescence when claims, child offers or pre-migration records are indeterminate. Stale roster/status prose is displayed as a projection finding but never counted as an award or claim. Each unknown legacy identifier produces a visible typed reconciliation finding and must receive an append-only `imported|terminal|superseded|live` receipt before zero proof; it is neither silently ignored nor allowed to block forever without an accountable reconciliation action. Pre-activation active assignments migrate into generation zero and are included on the first pause; no live work is grandfathered away. Rollback appends a supersession event, disables new commands only after reconciling all active generations, and preserves every receipt.

## Validation contract

Use deterministic race fixtures and a finite-state/property model for generation monotonicity, one-owner exclusivity, one-decision-per-escalation, and quiescence iff all authoritative sets are empty. Run unit tests for folds/validation, integration tests across MCP/Supervisor/GUI projections, and end-to-end restart/recovery tests. Evidence names exact agent-inbox candidate, autodocs contract digest, random seed/replay input, enumerated state boundary and executed case count.
