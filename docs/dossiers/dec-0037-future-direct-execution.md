# Future direct-execution capability decision

### `DEC-0037-002` — Remove sandboxed-grunt transport dependencies from the future architecture

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-24T08:37:26Z`
- **Deciding identity:** `agent:data:0037-51:20260824T083513Z`
- **Role:** `Architekt`
- **Authority reference:** `task:0037-51`
- **Subject:** Future Feature `0037` agent capability model and disposition of work introduced solely for sandboxed-grunt execution
- **Decision:** Every future agent is modeled as having direct Shell and Git execution capability. Feature `0037` removes or defers the legacy singleton runner, runner queue, typed runner-action transport, runner-only bootstrap, and sandboxed-grunt qualification work that exists solely to compensate for absent direct execution. It retains or rewrites the independent safety invariants those transports carried: isolated item worktrees, exact claims and scopes, collision rejection, governance-path protection, stale-baseline and authority-epoch rejection, deterministic validation, immutable evidence, recovery, review separation, atomic cutover, and fail-closed rollback. Completed runner artifacts and decisions remain append-only historical evidence and are not described as unimplemented or deleted by this decision.
- **Technical justification:** Management removed sandboxed grunts from the future system after all agents gained Shell and Git access. Preserving runner transport as a mandatory architectural layer would retain avoidable Tasks, deployment boundaries, host-service failure modes, and dependency edges without a future consumer. Removing transport must not erase the safety properties previously coupled to it; those properties protect concurrent repository mutation, authority, provenance, cutover, and recovery independently of which process executes Git or validation commands.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
  - `security-or-credential-boundary`
  - `material-risk-decision`
- **Considered alternatives:**
  - **ALT-01:** Remove runner-only transport and re-home independent safety invariants in direct-execution contracts
    - **Disposition:** `selected`
    - **Reason:** It implements Management's capability decision while preserving repository safety, authority, provenance, recovery, and cutover guarantees.
  - **ALT-02:** Retain the runner queue as the mandatory execution path even though every future agent has Shell and Git access
    - **Disposition:** `rejected`
    - **Reason:** It preserves an unnecessary host service, action registry, deployment sequence, and runner-specific Task chain whose original capability constraint no longer exists.
  - **ALT-03:** Remove all runner-related work and its coupled checks without replacement
    - **Disposition:** `rejected`
    - **Reason:** Collision control, governance protection, stale-state rejection, immutable evidence, and fail-closed recovery are safety invariants rather than sandbox accommodations.
- **Consequences:**
  - **CON-01:** Open runner-only implementation, activation, failover-remediation, qualification, and post-activation rollout work is removed or deferred before implementation; already completed work remains immutable history.
  - **CON-02:** Direct-execution tools and process contracts must enforce exact item scope, branch/worktree isolation, stale-baseline rejection, collision control, governance protection, validation, evidence, and recovery without depending on a runner request envelope.
  - **CON-03:** The Feature `0037` prerequisite graph and cutover plan require an explicit reviewed rewrite before any affected gate is implemented or crossed; this candidate does not itself mutate those gates.
  - **CON-04:** `DEC-0037-001` remains a valid record for its historical queue-failover subject, but its unimplemented future corrective chain is superseded for planning by this decision after `DEC-0037-002` is integrated on `main`.
  - **CON-05:** Rollback before issue-store authority cutover restores the current legacy direct-execution workflow; post-cutover recovery remains forward issue-store recovery and does not depend on restoring a retired sandbox runner.
  - **CON-06:** No active claim, request, or completed evidence is silently grandfathered, discarded, or reclassified; operative backlog changes must disposition each affected item and preserve its provenance.
  - **CON-07:** The removed runner deployment checkpoints do not leave the Feature without a review floor: `0037-34.02` becomes the intermediate authority-switch checkpoint and `0037-40` becomes the single terminal integrating Task with mandatory review.
- **Affected work units:**
  - `feature:0037`
  - `task:0037-45`
  - `task:0037-41`
  - `task:0037-46`
  - `subtask:0037-46.01`
  - `subtask:0037-46.02`
  - `task:0037-47`
  - `task:0037-50`
  - `subtask:0037-50.01`
  - `subtask:0037-50.02`
  - `subtask:0037-50.03`
  - `subtask:0037-50.04`
  - `subtask:0037-50.05`
  - `task:0037-51`
  - `task:0037-39`
  - `subtask:0037-10.04`
  - `task:0037-42`
  - `task:0037-43`
  - `task:0037-44`
  - `task:0037-21`
  - `task:0037-25`
  - `subtask:0037-25.01`
  - `task:0037-30`
  - `task:0037-32`
  - `subtask:0037-34.01`
  - `subtask:0037-34.02`
  - `task:0037-33`
  - `subtask:0037-35.01`
  - `task:0037-36`
  - `task:0037-40`
  - `task:0038-02`
  - `task:0038-04`
  - `task:0038-06`
  - `task:0038-07`
  - `task:0038-09`
  - `task:0038-10`
  - `task:0038-17`
  - `task:0038-19`
  - `task:0038-20`
  - `task:0038-22`
  - `task:0038-23`
  - `task:0038-24`
  - `task:0038-28`
  - `task:0038-30`
  - `task:0038-16`
  - `subtask:0038-16.01`
  - `subtask:0038-16.02`
  - `task:0039-05`
  - `task:0039-02`
  - `task:0041-01`
  - `task:0041-02`
  - `task:0041-03`
  - `task:0041-04`
  - `task:0041-05`
  - `task:0041-06`
  - `task:0044-04`
  - `task:0044-05`
  - `task:0044-07`
  - `repository:autodocs`
- **Affected gates:**
  - `task-start:0037-46.02`
  - `task-start:0037-47`
  - `task-start:0037-50.02`
  - `task-start:0037-50.03`
  - `task-start:0037-50.04`
  - `task-start:0037-50.05`
  - `validation:agent-bootstrap`
  - `validation:issue-policy`
  - `integration:0037-46.02`
  - `integration:0037-34.02`
  - `integration:0037-40`
  - `feature-closure:0037`
  - `external:runner-host-service`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `authority:repository-owner`
    - **Role:** `Management`
    - **Participation:** `consulted`
    - **Position:** `supports`
    - **Note:** Management directly removed sandboxed grunts from the future system and approved eliminating Tasks and intermediate steps introduced solely for them while retaining useful non-runner functionality.
- **Waiver:** `none`

#### `DEC-0037-002-C001`

- **Event format:** `decision-record-correction@v1`
- **Target record:** `DEC-0037-002`
- **Recorded at:** `2026-08-24T10:24:03Z`
- **Correcting identity:** `agent:data:0037-51-runner-role-amendment:20260824T102013Z`
- **Role:** `Architekt`
- **Authority reference:** `fa8d575f723b9905050c77df935cc7b55a8ebaa2:TODO-jean-luc-0037-51-20260824T072000Z.md#assumptions-and-evidence`
- **Correction reason:** The original field could be read as retiring the operational Runner role together with sandbox-specific runner transport. The current user clarified that this exceeded the decision: Runner remains a Dispatcher-selected direct-execution role for Task-ID-bound background jobs.
- **Target field:** `Decision`
- **Previous effective block SHA-256:** `5c22be78cb62e04d6609010e12c815814df111fa27125cf14fe693e206c4140f`
- **Replacement block:**
  ```markdown
  - **Decision:** Every future agent is modeled as having direct Shell and Git execution capability. Feature `0037` removes or defers the legacy singleton runner, runner queue, typed runner-action transport, runner-only bootstrap, and sandboxed-grunt qualification work that exists solely to compensate for absent direct execution. This transport retirement does not retire Runner as an operational role: Dispatchers explicitly select Programmer, Tester, or Runner, and a Runner starts and controls Task-ID-bound long-running background work, its job lifecycle, and its interfaces to other agents through direct execution rather than the retired runner service. The architecture retains or rewrites the independent safety invariants the old transports carried: isolated item worktrees, exact claims and scopes, collision rejection, governance-path protection, stale-baseline and authority-epoch rejection, deterministic validation, immutable evidence, recovery, review separation, atomic cutover, and fail-closed rollback. Completed runner artifacts and decisions remain append-only historical evidence and are not described as unimplemented or deleted by this decision.
  ```

#### `DEC-0037-002-C002`

- **Event format:** `decision-record-correction@v1`
- **Target record:** `DEC-0037-002`
- **Recorded at:** `2026-08-24T10:24:03Z`
- **Correcting identity:** `agent:data:0037-51-runner-role-amendment:20260824T102013Z`
- **Role:** `Architekt`
- **Authority reference:** `fa8d575f723b9905050c77df935cc7b55a8ebaa2:TODO-jean-luc-0037-51-20260824T072000Z.md#assumptions-and-evidence`
- **Correction reason:** The original justification used “runner” only for transport but did not state the retained role boundary, creating an avoidable ambiguity in downstream decomposition.
- **Target field:** `Technical justification`
- **Previous effective block SHA-256:** `1b2b94352e360087f2f9ddc042e3f88ee6c07e1f0d6484ce45df5d71f13cb65b`
- **Replacement block:**
  ```markdown
  - **Technical justification:** Management removed sandboxed grunts from the future system after all agents gained Shell and Git access, and then clarified that Runner remains an operational role. Preserving singleton, queue, typed-action, or host-service transport as a mandatory architectural layer would retain avoidable Tasks, deployment boundaries, failure modes, and dependency edges; retaining Runner instead preserves explicit ownership and lifecycle control for long-running background work such as webtree regeneration and nightly database rebuilds. The role and the transport are therefore separate interfaces. Removing transport must not erase the safety properties previously coupled to it, and retaining Runner must not confer acceptance, integration, specialist, credential, or release authority. Those properties and boundaries protect concurrent repository mutation, authority, provenance, cutover, recovery, and inter-agent handoff independently of which process executes Git or validation commands.
  ```

#### `DEC-0037-002-C003`

- **Event format:** `decision-record-correction@v1`
- **Target record:** `DEC-0037-002`
- **Recorded at:** `2026-08-24T10:24:03Z`
- **Correcting identity:** `agent:data:0037-51-runner-role-amendment:20260824T102013Z`
- **Role:** `Architekt`
- **Authority reference:** `fa8d575f723b9905050c77df935cc7b55a8ebaa2:TODO-jean-luc-0037-51-20260824T072000Z.md#assumptions-and-evidence`
- **Correction reason:** The original alternatives omitted the selected combination of transport retirement and role retention, so they did not expose the rejected role-retirement interpretation.
- **Target field:** `Considered alternatives`
- **Previous effective block SHA-256:** `63e9bf176e940aa7edd8cbaabd91cb127083fd5a58a3fe72fd14a69e392cd614`
- **Replacement block:**
  ```markdown
  - **Considered alternatives:**
    - **ALT-01:** Remove sandbox-only transport, retain Runner as direct background-job controller, and re-home independent safety invariants
      - **Disposition:** `selected`
      - **Reason:** It implements both Management clarifications while preserving explicit long-job ownership, repository safety, authority separation, provenance, recovery, and cutover guarantees.
    - **ALT-02:** Retire Runner as a role together with the singleton and queue transports
      - **Disposition:** `rejected`
      - **Reason:** It contradicts the clarified Management boundary and leaves long-running Task work without an explicit job-control and inter-agent interface owner.
    - **ALT-03:** Retain the runner queue as the mandatory execution path even though every future agent has Shell and Git access
      - **Disposition:** `rejected`
      - **Reason:** It preserves an unnecessary host service, action registry, deployment sequence, and runner-specific Task chain whose original capability constraint no longer exists.
    - **ALT-04:** Remove all runner-related work, role semantics, and coupled checks without replacement
      - **Disposition:** `rejected`
      - **Reason:** Background-job ownership, collision control, governance protection, stale-state rejection, immutable evidence, and fail-closed recovery remain necessary independently of sandbox transport.
  ```

#### `DEC-0037-002-C004`

- **Event format:** `decision-record-correction@v1`
- **Target record:** `DEC-0037-002`
- **Recorded at:** `2026-08-24T10:24:03Z`
- **Correcting identity:** `agent:data:0037-51-runner-role-amendment:20260824T102013Z`
- **Role:** `Architekt`
- **Authority reference:** `fa8d575f723b9905050c77df935cc7b55a8ebaa2:TODO-jean-luc-0037-51-20260824T072000Z.md#assumptions-and-evidence`
- **Correction reason:** The consequences must preserve the retained role, define its authority boundary, and add the shared job-control contract and checkpoint without restoring runner transport.
- **Target field:** `Consequences`
- **Previous effective block SHA-256:** `3f5eb05f9e70ff679e6c742ed6597e2a2c3baca214b27f6dc4c6bc1ad6efdb76`
- **Replacement block:**
  ```markdown
  - **Consequences:**
    - **CON-01:** Open sandbox-only runner implementation, activation, failover-remediation, qualification, and post-activation rollout work is removed or deferred before implementation; already completed work remains immutable history.
    - **CON-02:** Runner remains in the operational role taxonomy alongside Programmer and Tester. It is normally an `unprivileged` direct-execution role and receives no acceptance, integration, architecture, specialist, credential, release, or risk authority from role selection.
    - **CON-03:** The future Runner contract owns Task-ID-bound background-job start, identity, status/heartbeat, resource and timeout bounds, logs/artifacts/results, cancellation and termination, restart/recovery, cleanup, and handoff interfaces. It reports findings and state; it does not decide technical intent or acceptance.
    - **CON-04:** Direct-execution tools and process contracts must enforce exact item scope, branch/worktree isolation, stale-baseline rejection, collision control, governance protection, validation, evidence, and recovery without depending on a runner request envelope.
    - **CON-05:** The Feature `0037` prerequisite graph and cutover plan require an explicit reviewed rewrite before any affected gate is implemented or crossed; this candidate does not itself mutate those gates.
    - **CON-06:** `DEC-0037-001` remains a valid record for its historical queue-failover subject, but its unimplemented future corrective chain is superseded for planning by this decision after `DEC-0037-002` is integrated on `main`.
    - **CON-07:** Rollback before issue-store authority cutover restores the current legacy direct-execution workflow; post-cutover recovery remains forward issue-store recovery and does not depend on restoring a retired sandbox runner.
    - **CON-08:** No active claim, background job, request, completed evidence, Runner persona, or host process is silently grandfathered, discarded, or reclassified. Operative changes must bind each retained job/persona and each retired transport artifact explicitly.
    - **CON-09:** `0037-21` becomes an intermediate mandatory role/interface checkpoint; `0037-34.02` remains the intermediate authority-switch checkpoint; `0037-40` remains the single terminal integrating Task and mandatory Feature review floor.
  ```

#### `DEC-0037-002-C005`

- **Event format:** `decision-record-correction@v1`
- **Target record:** `DEC-0037-002`
- **Recorded at:** `2026-08-24T10:24:03Z`
- **Correcting identity:** `agent:data:0037-51-runner-role-amendment:20260824T102013Z`
- **Role:** `Architekt`
- **Authority reference:** `fa8d575f723b9905050c77df935cc7b55a8ebaa2:TODO-jean-luc-0037-51-20260824T072000Z.md#assumptions-and-evidence`
- **Correction reason:** The original affected-unit set omitted the operational role contracts and the completed build-run identity contract consumed by future background-job interfaces.
- **Target field:** `Affected work units`
- **Previous effective block SHA-256:** `34bec325993be5fcf764f20865c16c2b7ed8c22831a49c97859d4e802324a1a0`
- **Replacement block:**
  ```markdown
  - **Affected work units:**
    - `feature:0037`
    - `task:0037-45`
    - `task:0037-41`
    - `task:0037-46`
    - `subtask:0037-46.01`
    - `subtask:0037-46.02`
    - `task:0037-47`
    - `task:0037-50`
    - `subtask:0037-50.01`
    - `subtask:0037-50.02`
    - `subtask:0037-50.03`
    - `subtask:0037-50.04`
    - `subtask:0037-50.05`
    - `task:0037-51`
    - `task:0037-39`
    - `subtask:0037-10.04`
    - `task:0037-42`
    - `task:0037-43`
    - `task:0037-44`
    - `task:0037-21`
    - `task:0037-25`
    - `subtask:0037-25.01`
    - `task:0037-30`
    - `task:0037-32`
    - `subtask:0037-34.01`
    - `subtask:0037-34.02`
    - `task:0037-33`
    - `subtask:0037-35.01`
    - `task:0037-36`
    - `task:0037-40`
    - `task:0038-02`
    - `task:0038-04`
    - `task:0038-06`
    - `task:0038-07`
    - `task:0038-09`
    - `task:0038-10`
    - `task:0038-17`
    - `task:0038-19`
    - `task:0038-20`
    - `task:0038-22`
    - `task:0038-23`
    - `task:0038-24`
    - `task:0038-28`
    - `task:0038-30`
    - `task:0038-16`
    - `subtask:0038-16.01`
    - `subtask:0038-16.02`
    - `task:0039-05`
    - `task:0039-02`
    - `task:0041-01`
    - `task:0041-02`
    - `task:0041-03`
    - `task:0041-04`
    - `task:0041-05`
    - `task:0041-06`
    - `task:0043-01`
    - `task:0044-04`
    - `task:0044-05`
    - `task:0044-07`
    - `path:docs/pipeline/roles/programmer.md`
    - `path:docs/pipeline/roles/tester.md`
    - `path:docs/pipeline/roles/runner.md`
    - `path:docs/pipeline/agent-roster.md`
    - `path:docs/pipeline/process-roles.md`
    - `repository:autodocs`
  ```

#### `DEC-0037-002-C006`

- **Event format:** `decision-record-correction@v1`
- **Target record:** `DEC-0037-002`
- **Recorded at:** `2026-08-24T10:24:03Z`
- **Correcting identity:** `agent:data:0037-51-runner-role-amendment:20260824T102013Z`
- **Role:** `Architekt`
- **Authority reference:** `fa8d575f723b9905050c77df935cc7b55a8ebaa2:TODO-jean-luc-0037-51-20260824T072000Z.md#assumptions-and-evidence`
- **Correction reason:** The clarified shared role interface adds a review boundary and downstream start gates that were absent from the transport-only gate list.
- **Target field:** `Affected gates`
- **Previous effective block SHA-256:** `0e25087b536704288c9d96be0afdd89879b8f1e7357687e4e3f26ffce3adf9ec`
- **Replacement block:**
  ```markdown
  - **Affected gates:**
    - `task-start:0037-46.02`
    - `task-start:0037-47`
    - `task-start:0037-50.02`
    - `task-start:0037-50.03`
    - `task-start:0037-50.04`
    - `task-start:0037-50.05`
    - `task-start:0037-21`
    - `task-start:0037-25.01`
    - `task-start:0037-34.01`
    - `task-start:0039-02`
    - `task-start:0044-05`
    - `validation:agent-bootstrap`
    - `validation:issue-policy`
    - `validation:background-job-contract`
    - `integration:0037-46.02`
    - `integration:0037-21`
    - `integration:0037-34.02`
    - `integration:0037-40`
    - `feature-closure:0037`
    - `external:runner-host-service`
  ```
