### `DEC-0038-006` — Distinguish carried claim provenance from active and unreconciled claims

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-25T23:12:41+02:00`
- **Deciding identity:** `agent:data:0038-35:claim-carriage-20260825T211241Z-c86a50d2`
- **Role:** `Architekt`
- **Authority reference:** `DEC-0038-005`; `docs/campaign-evidence/0038-35/architect-terminal-integration-contract.md#roles-and-order`; `docs/pipeline/process-roles.md#architect`
- **Subject:** Claim-lifecycle semantics used by the legacy doctor, Feature integration, and the Feature 0037 claim migration
- **Decision:** A canonical Task claim whose `state` matches a terminal `[x]` or `[w]` Task inside a Feature that remains in `TODO.md` is inactive carried provenance, not a stale active lease. It remains at its tracked top-level path and travels upward until the privileged Feature integrator reconciles its durable information. A claim still present after its Feature has moved to `DONE.md` is unreconciled and remains an error. A `[p]` claim for a terminal Task, a claim/Task state divergence, a malformed or unsafe claim, and duplicate active ownership remain errors. A historical combined or non-Task coordination record is never made valid by a filename exception: it preserves its first minted immutable owner token and is classified only through an explicit versioned historical-carriage kind whose source commit, source path, exact original token, related Task IDs, inactive lifecycle, and provenance digest validate. The legacy doctor and Feature 0037 migration must keep active leases, ordinary carried Task provenance, explicit historical carriage, and unreconciled post-integration claims distinct.
- **Technical justification:** The implemented rule at `_src/tools/legacy_task_doctor.py` revision `cc99c1f27a0be1c53357b6aaef829aab8ae36770` reports every terminal Task claim as `LTD-CLAIM-TERMINAL-RETAINED`. That behavior predates the normative branch-carriage rule added by `4f5a563569f`, now stated at `AGENTS.md:69`, `AGENTS.md:210`, `docs/pipeline/branch-workflow.md:229-247` and `docs/pipeline/task-acceptance.md:183`: `[x]`/`[w]` ends the lease but does not delete the tracked claim; reconciliation/removal occurs during Feature integration. Against `main@8a364e000fed6e826a1e7d49c4b1c014c849eece`, 56 of 60 terminal-retention findings belong to Tasks whose Features are still in `TODO.md`; candidate `84ed0fab0ea8a2e3a3cae2bb9abd6e62f82af3d4` adds three more such findings while preserving required root carriage. The same candidate also rewrites the original combined record's token from `agent:paul:review-0038-33-34:20260825T195800Z` at `5b08608b0dada88e061ab8985c8f11e08cde21e9` to the Task-token used by a second file. Contextual lifecycle classification removes the false stale-lease conclusion without weakening genuine active, identity, or post-integration failures; explicit historical provenance repairs the token ambiguity without deleting, moving, hiding, or path-whitelisting the record.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  - **ALT-01:** Classify claims by Task state, Feature lifecycle, and explicit validated historical-carriage provenance.
    - **Disposition:** `selected`
    - **Reason:** This is the smallest rule that implements the current branch workflow, preserves immutable identity and root provenance, and still detects missing Feature-integration reconciliation.
  - **ALT-02:** Delete, move, or hide terminal root claims so the existing doctor no longer discovers them.
    - **Disposition:** `rejected`
    - **Reason:** This violates the explicit carriage rule and loses the visible provenance that Feature integration must reconcile.
  - **ALT-03:** Suppress `LTD-CLAIM-TERMINAL-RETAINED` for named Paul paths or downgrade it globally.
    - **Disposition:** `rejected`
    - **Reason:** A path allowlist would grandfather malformed history, while a global downgrade would conceal active divergence and unreconciled claims in completed Features.
  - **ALT-04:** Treat every terminal claim file as valid provenance regardless of Feature lifecycle.
    - **Disposition:** `rejected`
    - **Reason:** Claims left after Feature integration are a real reconciliation failure and must continue to block a final `DONE.md` candidate.
- **Consequences:**
  - **CON-01:** The future Implementer must add a closed, deterministic classification for active Task claims, ordinary carried Task provenance, explicit historical carriage, and post-integration unreconciled claims; file presence alone is never an active lease.
  - **CON-02:** The combined Paul record remains at its original root path and restores the exact token first recorded at `5b08608b0dada88e061ab8985c8f11e08cde21e9`; the two canonical per-Task records also remain at root. No record gains Acceptance, ownership, or lease authority from its historical kind.
  - **CON-03:** The final Feature-integration candidate must contain no unreconciled carried claims for a Feature moved to `DONE.md`; the correction does not defer or weaken the integrator's reconciliation duty.
  - **CON-04:** Changing accepted doctor work-product bytes or semantics requires an additive Acceptance impact analysis for `0038-04`, with propagation through affected accepted dependents including `0038-21`, `0038-23`, `0038-33`, `0038-34`, and the terminal `0038-35` batch as `task-acceptance.md` requires. This decision alone changes no Acceptance state.
  - **CON-05:** Feature 0037 migration maps only genuine active leases to active `claim.json`; terminal carriage and explicit historical carriage become append-only provenance/closure events and never duplicate active ownership.
  - **CON-06:** Activation is staged. This decision and the supporting Architect scope review must first be reachable from `main`; the separately assigned Implementer then changes code/tests under a bounded item claim, and the corrected behavior becomes operative only after that implementation and its required Acceptance/integration are current. Until then, the false-positive doctor output remains visible and is interpreted manually against current governance.
  - **CON-07:** There is no implicit grandfathering. Ordinary terminal Task claims are classified uniformly from authoritative Task/Feature state; every record using the historical-carriage kind must satisfy the same provenance fields and validation; every other noncanonical record continues to receive the existing identity or structure findings.
  - **CON-08:** Rollback reverts the later tool/schema/documentation implementation as one bounded change and restores the prior reported findings. It never deletes or rewrites root records, this decision, the scope review, prior findings, or Git history.
- **Affected work units:**
  - `task:0038-04`
  - `task:0038-21`
  - `task:0038-23`
  - `task:0038-33`
  - `task:0038-34`
  - `task:0038-35`
  - `feature:0038`
  - `feature:0037`
  - `repository:autodocs`
- **Affected gates:**
  - `validation:legacy-task-doctor-claim-lifecycle`
  - `validation:0038-35-backlog-claim-structure`
  - `validation:0037-claim-migration`
  - `integration:0038-35`
  - `feature-closure:0038`
  - `feature-closure:0037`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:data:0038-35:claim-carriage-20260825T211241Z-c86a50d2`
    - **Role:** `Architekt`
    - **Participation:** `reviewed`
    - **Position:** `supports`
    - **Note:** The separately recorded pre-mutation scope review supports this exact lifecycle boundary and constrains the future Implementer; it is not Task Acceptance or implementation authority.
- **Waiver:** `none`

#### Origin-provenance note — 2026-08-25

Candidate `add65255e5c6da9ae21616051844582c1dc0053c` was rejected before integration
because the decision artifact's path-specific last-touch commit still resolved
to its untrailed introduction commit. This append-only note binds this exact
decision artifact to the current correction commit, whose immutable commit
metadata carries `Policy-Origin-Branch: main`. The decision fields and their
effective values are unchanged; the previously rejected tips remain in history.
