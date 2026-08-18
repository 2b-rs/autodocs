# Task `0040-05` — pre-implementation cross-item scope decision

**Status:** Planning and architecture evidence. This record opens bounded
implementation of Task `0040-05`; it is not Task acceptance, an integration
verdict, or `Acceptance: ✓`.

### `DEC-0040-005` — Require narrow pre-implementation review for cross-item gate scope

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-18T16:50:25Z`
- **Deciding identity:** `agent:zed:0040-05:20260818T162728Z-4c98b6072815`
- **Role:** `Management`
- **Authority reference:** `TODO-zed-0040-05-20260818T162728Z-4c98b6072815.md#assignment-and-review-boundary`
- **Subject:** Pre-implementation decision and review boundary for gate-scope changes with cross-item blocking or contract effects
- **Decision:** A conforming decision record and a supporting review by a distinct management-instantiated Architect are required before the first mutation that implements, activates, widens, narrows, affirmatively retains, or removes a gate scope whose declared behavior can block another work unit or change its contract. Affirmative retention means an in-scope decision to preserve contested gate behavior; passive inheritance, an unrelated shared-path edit, difficulty, unfamiliarity, green validation, or a hypothetical ordinary bug does not trigger this rule. Bounded decision preparation continues under `[p]`; `[u]` is used only when the required assignment, authority decision, dissent resolution, or management exception is the sole next action. The scope review neither validates implementation nor creates acceptance credit.
- **Technical justification:** Task `0038-03` installed a repository-wide blocking validator while its selected scope remained invisible and unchallenged; its initially green result did not reveal the latent coupling. A record-only rule would preserve provenance but would not correct the missing pre-implementation scope challenge represented by `T7`. A shared-path or all-drafting-change proxy would instead flood the process with reviews unrelated to actual cross-item gate behavior. The selected rule uses the closed `cross-item-blast-radius` predicate, preserves routine autonomous repair, and separates scope authority from implementation and later checkpoint acceptance.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
  - `authority-tailoring-or-waiver`
- **Considered alternatives:**
  - **ALT-01:** Narrow mandatory review by a distinct Architect for declared cross-item gate or contract effects
    - **Disposition:** `selected`
    - **Reason:** Satisfies `RQ-PROC-02/03/04`, addresses both invisible scope and missing pre-implementation challenge, and leaves local autonomous repair intact.
  - **ALT-02:** Require a decision record but allow the Implementer to be the sole scope reviewer
    - **Disposition:** `rejected`
    - **Reason:** Preserves traceability but does not provide the distinct reviewing role required before implementation and would not have corrected `T7`.
  - **ALT-03:** Require Architect review for every shared-path edit or drafting defect
    - **Disposition:** `rejected`
    - **Reason:** Shared paths and drafting defects are poor blast-radius proxies; this would create escalation noise and contradict the negative boundary in `decision-record@v1`.
- **Consequences:**
  - **CON-01:** Future Tasks must name affected work units and gates before implementing qualifying cross-item scope behavior.
  - **CON-02:** A distinct Architect can stop or return a contested scope before it becomes repository-wide behavior, without granting implementation acceptance.
  - **CON-03:** Bounded planning remains executable under `[p]`; user or authority interruption occurs only when no disjoint preparation remains.
  - **CON-04:** Existing inherited gates are not automatically reopened; deliberate in-scope retention of contested behavior is reviewable, while passive inheritance is not.
  - **CON-05:** `AGENTS.md`, the `TODO.md` Feature-breakdown header, and `process-roles.md` must use the same predicate and review boundary.
- **Affected work units:**
  - `task:0040-05`
  - `feature:0040`
  - `repository:autodocs`
- **Affected gates:**
  - `task-start:0040-05`
  - `integration:0040-05`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:zed:architect:0040-05:scope-review-20260818-7f4c9a2d`
    - **Role:** `Architekt`
    - **Participation:** `reviewed`
    - **Position:** `supports`
    - **Note:** Supports ALT-01, the narrow mandatory distinct-Architect pre-implementation scope review, and opposes record-only review and broad shared-path or drafting-change review. The trigger is actual declared gate behavior that can block another work unit or change its contract, not shared paths, difficulty, unfamiliarity, green validation, or hypothetical ordinary bugs. Implementing, activating, widening, narrowing, deliberately retaining, or removing such gate behavior requires the decision record and review before normative mutation; deliberate retention means an affirmative in-scope decision and not passive inheritance. Bounded preparation remains under [p], [u] is used only when authority action is the sole next step, and this scope review neither proves implementation correctness nor fulfills Task acceptance or the mandatory integration checkpoint.
- **Waiver:** `none`

## Implementation opening condition

The Architect is distinct from the future Implementer and returned `supports`.
The selected alternative therefore opens only the bounded normative implementation
of `0040-05`. The Task remains `[p]`; its mandatory integration review remains
reserved for the current user's participation after implementation evidence is
complete.
