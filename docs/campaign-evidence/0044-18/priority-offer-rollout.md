# 0044-18 preparation-only lifecycle contract and delta

## Status and pins

- **Status:** proposed preparation record only; no rollout is activated.
- **Autodocs baseline:** `main@fd86cadc221ddbc919975a6b48b43a2fa984e8f2`.
- **External read-only baseline:** `agent-inbox/main@f081d27645ab97bd48f92b5274d82eea4f202864`, server `1.16.2`.
- **Management disposition:** `decision-1787959369327-8349792b` rejects an as-written rollout and authorizes this contract/delta preparation only.

## Proposed complete Assignment lifecycle

1. A coordinator creates one submitted offer round for one exact chain. It carries the ordered items, branch/worktree, exhaustive paths, authority, reply window, duration, prerequisites, start/wait/checkpoint/merge/stop conditions, and ordered priority groups.
2. After validation, the round becomes offered. Only candidates in the current lowest-numbered priority tier can see the offer and call `offer_reply`.
3. The first successful active-tier `ACCEPT` atomically records `AWARDED`; all competing active notices observe the terminal already-awarded result. Lower tiers receive no notice. A decline is final; timeout/advance is performed through `offer_control` only after the current tier is exhausted.
4. The awarded contractor receives the execution wake, changes the Assignment to `in_progress`, and works only inside the awarded branch/worktree and exhaustive scope.
5. On completion the contractor changes the Assignment to `review`. The coordinator records the resulting accepted disposition or opens a priority-gated rework offer; rework is unowned until a new `ACCEPT`. `on_hold` preserves state and shifts its due time when resumed.

This is a proposal describing the external `1.16.2` mechanism against which any later exact implementation re-pin must be assessed. It does not claim that current autodocs instructions, tools, tests, profiles, or active rounds implement it.

## Proposed delta and affected gates

The future candidate would replace manual new-round award messaging with the lifecycle above and make the atomic award result the only execution-start signal. Its affected gates are:

- `assignment-offer:<chain>` — validation and current-tier visibility before a reply;
- `assignment-start:<chain>` — only `AWARDED` releases the contractor;
- `assignment-tier-advance:<chain>` — decline/expiry progression is coordinator-controlled;
- `assignment-completion:<chain>` — contractor review handoff and coordinator disposition;
- each new multi-Dispatcher work unit whose start authority is changed by the rollout.

Existing legacy rounds remain governed by their pinned briefings. This record does not alter any gate, create a round, notify a candidate, or release execution.

## Required closure before substantive work

1. Saru's distinct Architect exact-scope review must be landed with a PASS that covers these affected gates and units.
2. The coordinator must issue a fresh exact-baseline implementation assignment after that PASS.
3. Only that later assignment may define implementation surfaces and validation. This preparation makes no test assertion and provides no Integration, Acceptance, release, or external-state evidence.
