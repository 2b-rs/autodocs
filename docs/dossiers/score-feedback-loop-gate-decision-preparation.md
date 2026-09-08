# Feature 0045 Management-gate decision preparation

## Status and authority boundary

- **Preparation format:** `management-gate-decision-preparation@v1`
- **Prepared at:** `2026-08-31T21:48:04Z`
- **Preparer:** `agent:data:0045-00-preparation:1788212597555-9ecd6db1`
- **Role / capability:** Architect persona, privileged preparation contractor
- **Assignment:** priority award `1788212597555-9ecd6db1`; supervisor wake
  `1788212615693-b5107628`
- **Autodocs baseline:**
  `5c6068537aa4a304c940ca82f62b466a08d72136` on branch `0045-00`
- **Agent-inbox evidence baseline:**
  `071c1cb1365ec90a9c4f70748275e615b9df475d` on `main`
- **State:** permanent evidence and form-ready inputs only; no decision has
  been submitted or resolved, no `DEC-*` identifier has been allocated, no
  Architect scope review has been authored, and no approved baseline or
  operative gate exists.

Management is the deciding authority. A distinct management-instantiated
Architect must review the scope selected by Management. This preparer is
neither authority and must not supply either record.

## Decision subject

Feature `0045` needs one shared start-gate decision that binds two related
choices before any fan-out implementation begins:

1. whether every minimally route-valid feedback or Curator-decision arrival
   opens a priority-gated Project Lead offer before trusted ingestion or recipe
   execution; and
2. which current execution interface binds the three deterministic recipe
   names without inventing a registry or overriding either repository's
   authority selector.

The decision has `cross-item-blast-radius`,
`material-architecture-or-repository-behavior`, and
`security-or-credential-boundary` reach. It controls starts and interfaces in
two repositories and separates routing, trust, product judgment, mechanical
execution, integration, and publication authority.

## Directly observed evidence

### Autodocs

- `docs/pipeline/score-feedback-loop.md` is explicitly proposed and
  non-operative. It requires Supervisor routing to a priority-gated Project
  Lead offer before trusted mutation and leaves the recipe binding open.
- `agent-workflow.json` declares `runner_protocol=runner-request@v1`,
  `authority_epoch=legacy-writable`, and `required_capability=sandboxed-grunt`.
  Its embedded `selector_digest` is the literal placeholder-like value
  `sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`;
  it must not be treated as proof of the file bytes recorded below.
- `_src/tools/runner_dispatch.py` and `_src/runner/actions-v1.json` do not
  exist. Historical `0037-46.01`/`.02` work is not a current registry.

### Agent-inbox

- `agents.json` defines a machine-readable `runner` capability and `Runner`
  role policy. A Runner is mail-woken, executes only a validated typed request,
  never selects work or product disposition, reports evidence, acknowledges,
  and ends.
- `supervisor.py::invocation_defined` treats a capability as launchable unless
  its contract explicitly sets `invocation_defined: false`; the current Runner
  contract has no such false value. `test_supervisor.py` independently asserts
  that Runner personas are selected and launchable.
- `README.md` still says Runner invocation is intentionally undefined and that
  Runner entries remain configuration-only. That prose contradicts current
  `agents.json`, `supervisor.py`, tests, and commit `5a0d26b65e02cbbae2f2f2bb6ae9e27d079acbf5`
  (`Define live coordination policy and runner contract`). The decision must
  not hide this inconsistency; Task `0045-02` must reconcile it before any
  adapter becomes operative.
- During preparation, agent-inbox `main` advanced through unrelated integrated
  work to `01937d6a0b369191056a404d43a9884cb5176f2c`. The assigned evidence
  baseline `071c1cb1365ec90a9c4f70748275e615b9df475d` is its ancestor, and all
  four evidence blobs (`agents.json`, `supervisor.py`, `test_supervisor.py`,
  and `README.md`) are byte-identical at both commits. The older commit remains
  the decision input pin; the newer observation proves no relevant drift.

## Exact evidence and interface digests

All SHA-256 values are over the exact file bytes at the commits named above.
Git blob IDs are included to make repository-native revalidation possible.

| Repository | Path / projection | Git blob | SHA-256 |
| --- | --- | --- | --- |
| autodocs | `docs/pipeline/score-feedback-loop.md` | `b24743e2fb0a0987e50e47e03d5e82213093c289` | `2e5b56da933f148310e549770c60b43ead558b0d6c306352cb754492bf78a15f` |
| autodocs | `docs/dossiers/score-feedback-loop-requirements-20260831.md` | `0e04b189c9db08d09c7ca2ba2186958860d9ab82` | `6b6daeaed8a54287813ba5bdba876b1c2a4faed2a11c6a0e03410b3d4ffb6695` |
| autodocs | `agent-workflow.json` | `f81ea091982aa225e8999d05fc2faced5561e42f` | `7408152f5723b56986e2b39de8fe73e0d7e59636a5af8fa21474281ec17db566` |
| agent-inbox | `agents.json` | `55a05626eb3979fc7ea1c0dfe49a064b893bce55` | `ba48301826b71d7927863f72bbcd5fc1a7151d51955c112e5247e69bfce4c6e9` |
| agent-inbox | canonical compact JSON projection of `capability_sets.runner`, `role_policy.Runner`, and the five Runner personas' name/process-role/capability/role-practice fields | derived from `agents.json` | `10ef3bca2e6b521914cca68f1f1ef1243df12a9e2d4a6280d119815b5c6d32f9` |
| agent-inbox | `supervisor.py` | `11d07d1e642c826ca1818ee1850b92975cdd1c7e` | `0ec20127a2306d6caaaf2b38b5151d5dd7766af6355c7634cbd6376959e5100c` |
| agent-inbox | `test_supervisor.py` | `a70090972bc97f2ecd0d4745138adacdccd6ecee` | `d58aa2428057090ae3b7f4c9e204d082ea0c82930c036b0329393d2fbc9f8d36` |
| agent-inbox | `README.md` (conflicting prose retained as evidence) | `a77fcd9c4bd50360a763ea7b309ff16dc6c3d9b6` | `22725a5fef34c9bbfa8a5513ad3cfe01eb9fb9de6c9ce2aeb5668861f81b0f08` |

The compact Runner projection is produced with sorted source order preserved:

```sh
jq -c '{runner_capability:.capability_sets.runner,runner_role_policy:.role_policy.Runner,runner_agents:[.agents|to_entries[]|select(.value.role=="Runner")|{name:.key,process_role:.value.process_role,capability_class:.value.capability_class,role_practice:.value.role_practice}]}' agents.json
```

These digests describe evidence, not authority. The approved baseline must
later bind the resolved decision, separate review, and the exact verified
bytes; it must reject a changed commit, blob, projection, or SHA-256.

## Policy alternatives and consequences

### `ALT-01` — priority-gated Project Lead first; assignment-Runner adapter

**Recommended.** For each supported arrival, Supervisor performs only minimum
route-safety validation and opens a priority-gated Project Lead offer. The
awarded Lead records one explicit branch: similar-item handoff, dependent typed
Runner assignment, or trivial same-item Runner handoff. A versioned adapter
then maps the selected recipe contract to the current agent-inbox assignment
Runner envelope while pinning the autodocs selector and refusing any mismatch.

Consequences:

- preserves `REQ-0045-04`/`05` by keeping scheduling and product judgment with
  the awarded Project Lead;
- uses an actually implemented Runner lifecycle without claiming that it is an
  autodocs registry or that it overrides `runner-request@v1`;
- requires `0045-02` to specify the adapter, reconcile the README contradiction,
  prove both repository pins/digests, and fail closed before mutation;
- keeps trusted ingestion, proposal, apply, integration, and publication as
  separately authorized transitions; and
- adds a cross-repository compatibility surface that must be versioned, tested,
  and rolled back atomically by withholding activation.

### `ALT-02` — bind recipes directly to autodocs `runner-request@v1`

Supervisor still offers the item to a Project Lead first, but every recipe is
encoded as a legacy autodocs runner request.

Consequences:

- matches the literal current autodocs selector;
- does not natively establish the required agent-inbox arrival/offer/assignment
  continuation or cross-repository handoff;
- risks conflating sandbox mutation transport with the distinct assignment
  Runner role and would require a second bridge anyway; and
- retains legacy singleton assumptions that do not express the required
  event-driven two-repository lifecycle.

### `ALT-03` — Supervisor directly selects and executes recipes

Supervisor validates the arrival, chooses the action, and invokes ingestion or
publication without a Project Lead award.

Consequences:

- reduces latency but violates `REQ-0045-04`/`05` and collapses routing,
  product judgment, and mechanical execution authority;
- can mutate trusted queue/history before the required decision branch exists;
  and
- is unsuitable without a material requirements and authority change.

### `ALT-04` — create a new recipe registry first

Feature `0045` invents `_src/runner/actions-v1.json`, a dispatcher, or another
registry and binds recipes to it.

Consequences:

- could eventually provide a uniform typed interface;
- has no current producer, authority contract, or accepted implementation;
- would enlarge the start gate into an unplanned infrastructure project and
  improperly revive superseded work; and
- cannot be selected from current evidence without a new architecture and
  backlog decision.

## Recommended binding if Management selects `ALT-01`

The approved contract should state all of the following:

1. `feedback_ingestion`, `ai_proposal`, and `apply_publish` are logical recipe
   names, not executable authority or registry entries.
2. Supervisor may perform only minimum route validation before it opens the
   priority-gated Project Lead offer.
3. Only the awarded Lead selects and records the scheduling branch and exact
   dependent/trivial assignment.
4. The adapter accepts only an awarded, typed assignment containing identity,
   repository and base commit, exact read/write scopes, normalized input digest,
   idempotence key, allowed effects, timeout, cleanup, evidence, recovery, and
   next-event/terminal disposition.
5. The adapter pins autodocs
   `5c6068537aa4a304c940ca82f62b466a08d72136` and its selector digest plus
   agent-inbox `071c1cb1365ec90a9c4f70748275e615b9df475d` and Runner projection digest.
   Any mismatch, stale award, duplicate/conflicting key, missing authority, or
   unresolved README/implementation contradiction stops before mutation.
6. The Runner validates and executes only the selected transition. It never
   chooses work, decides similarity or product disposition, accepts a proposal,
   grants authority, integrates, publishes, or crosses a release gate.
7. Cross-repository results use the versioned immutable handoffs already named
   in the proposed contract; no assignment writes both repositories.

## Affected work products, processes, units, and gates

### Work products and processes

- autodocs: `TODO.md` Feature `0045`, requirements dossier, proposed process
  contract, approved baseline, selector, later typed handoff schemas and tests;
- agent-inbox: priority offers, assignments, Runner capability/role policy,
  Supervisor launch/continuation behavior, Runner documentation/tests, and
  later recipe adapter/result schemas;
- processes: feedback arrival, trusted ingestion, proposal scheduling,
  Curator-decision arrival, decision ingestion, apply/publication scheduling,
  cross-repository handoff, retry/idempotence, integration, and release.

### Affected work units

- `feature:0045`
- `task:0045-00`
- `task:0045-01`
- `task:0045-02`
- `subtask:0045-03.01`
- `subtask:0045-03.02`
- `task:0045-03`
- `task:0045-04`
- `task:0045-05`
- `subtask:0045-06.01`
- `subtask:0045-06.02`
- `task:0045-06`
- `repository:autodocs`
- `repository:agent-inbox`
- `path:agent-workflow.json`
- `path:docs/pipeline/score-feedback-loop.md`
- `path:agents.json`
- `path:supervisor.py`

### Affected gates

- `task-start:0045-01`
- `task-start:0045-02`
- `task-start:0045-03.01`
- `task-start:0045-03.02`
- `task-start:0045-03`
- `task-start:0045-04`
- `task-start:0045-05`
- `task-start:0045-06.01`
- `task-start:0045-06.02`
- `task-start:0045-06`
- `validation:docs/pipeline/score-feedback-loop-approved-baseline.json`
- `integration:0045`
- `feature-closure:0045`

## Paused action and rollback boundary

Paused now:

- finalizing `score-feedback-loop-approved-baseline.json`;
- starting any downstream `0045` task or subtask;
- implementing or activating arrival routing, recipe adapters, trusted
  ingestion, Curator-decision continuation, apply, or publication; and
- treating either the proposed contract or these recommendations as authority.

Before activation, rollback is simply to withhold or reject the candidate and
leave all downstream gates closed. After a later authorized implementation,
rollback must stop new arrivals before mutation, retain every durable request,
award, assignment, decision, result, retry ancestor, and publication receipt,
disable the adapter as one reviewed change, and restore the previous selectors
without rewriting history.

## Form-ready Management decision inputs

**Subject:** `DECISION NEEDED — Should Feature 0045 use Project-Lead-first scheduling with a selector-pinned assignment-Runner adapter?`

**Paused action:** Finalization of the approved shared baseline and every
downstream `0045` task start.

**Observed fact:** Autodocs selects legacy `runner-request@v1` and has no recipe
registry. Agent-inbox has a live assignment Runner contract at `071c1cb1365`,
but its README still contradicts the implementation. The proposed Feature
contract requires a priority-gated Project Lead decision before trusted recipe
execution.

**Risk if continued:** Choosing or executing a recipe without the decision can
let Supervisor/Runner code make product decisions, bypass the Project Lead
gate, or bind downstream work to nonexistent or contradictory infrastructure.

**Choices:**

- **A — select `ALT-01`:** Project-Lead-first scheduling plus a fail-closed,
  versioned assignment-Runner adapter pinned to both repositories; `0045-02`
  must reconcile documentation and prove selector compatibility before use.
- **B — select `ALT-02`:** Project-Lead-first scheduling but bind recipes
  directly to legacy autodocs `runner-request@v1`; accept the extra bridging
  work and legacy transport limitations.
- **C — select `ALT-03`:** Supervisor directly selects/executes recipes;
  requires explicit replacement of `REQ-0045-04`/`05` and authority controls.
- **D — select `ALT-04`:** pause Feature implementation and first authorize a
  separately planned recipe registry.

**Recommendation:** A. It preserves the required authority separation, uses
existing Runner machinery without fabricating a registry, and makes current
selector/documentation mismatches explicit fail-closed work for `0045-02`.

**Requested reply:** A, B, C, D, or a fully specified alternative, including
whether GitHub remains the durable transport/provenance boundary.

**Permanent evidence:** this dossier at the immutable preparation candidate
reported by the preparer; proposed contract digest
`2e5b56da933f148310e549770c60b43ead558b0d6c306352cb754492bf78a15f`;
selector digest
`7408152f5723b56986e2b39de8fe73e0d7e59636a5af8fa21474281ec17db566`;
Runner projection digest
`10ef3bca2e6b521914cca68f1f1ef1243df12a9e2d4a6280d119815b5c6d32f9`.

## Required post-decision sequence

1. The current user/Management submits and resolves one durable decision using
   the permanent candidate and form-ready inputs above.
2. Supervisor separately assigns the exact selected scope to a distinct
   Architect, who records support, dissent, or a narrower correction without
   relying on this preparation as review.
3. Only after both immutable references are supplied may this Task finalize the
   schema-valid approved baseline with exact resolution, review, interface,
   selector, Runner, and evidence digests.
4. A separate reviewer/integrator validates the candidate. Preparation,
   Management decision, Architect review, implementation, Acceptance,
   integration, and release remain distinct lifecycles.
