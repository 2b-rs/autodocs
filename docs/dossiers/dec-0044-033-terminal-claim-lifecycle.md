# `DEC-0044-033` — Terminal claim lifecycle and validation baseline

This pre-mutation record resolves the lifecycle conflict exposed by Task
`0020-10`. It defines governance and a later implementation contract; it does
not finalize `0020-10`, implement automation, grant Acceptance, cross a
checkpoint, integrate a branch, or advance `main`.

### `DEC-0044-033` — Terminal claims remain awaiting-Acceptance provenance

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-29T21:25:47Z`
- **Deciding identity:** `agent:data:0044-20:1788038395542-d19fafda`
- **Role:** `Architekt`
- **Authority reference:** `agent-inbox:1788038395542-d19fafda`; `task:0044-20`; `docs/pipeline/decision-record.md`; `docs/pipeline/task-acceptance.md`; prerequisite `task:0044-17` at `635b9c810dc9fc2ed602116dbd13fba39c2b634d`
- **Subject:** Repository-wide meaning, transition, validation baseline, compatibility, and migration of root `TODO-*` and `DONE-*` claim artifacts when an implementation reaches `[x]` or `[w]` before current Acceptance, including the held `0020-10` terminal transition.
- **Decision:** A root `TODO-*` filename means live **or not-yet-accepted** claim provenance; it is not by itself an active lease. Active ownership is established only by the claim's nonterminal state together with its current coordination/award evidence. Implementation completion is one atomic logical transition: the Task marker becomes `[x]` or `[w]` with its real REF; every participating root claim whose canonical `task_id` or `item_id` names that exact item becomes the same terminal state; and every such claim releases its lease and records terminal coordination. A terminal, lease-free `TODO-*` whose state matches its Task is valid awaiting-Acceptance provenance. It remains at that path until a separate current Acceptance transaction renames every exact-item root claim byte-identically to `DONE-*`. `DONE-*` without current Acceptance is invalid. Validators MUST reject state divergence, a terminal claim that still asserts an active lease/current award, a missing or ambiguous participating exact-item claim, partial multi-claim finalization, and premature `DONE-*`; they MUST NOT reject a matching lease-free terminal `TODO-*` merely because the filename remains `TODO-*`. Policy-sensitive validation of a legacy candidate MUST use the canonical validator and lifecycle contract from the target integration policy, not stale branch-local bytes. No bulk rename or history rewrite is authorized. Existing accepted `DONE-*` remains valid; nonaccepted claims are reconciled only in their next authorized terminal, review, or Acceptance transaction. Governance semantics activate when this record and its scope review reach `main`; automation hardening activates only after `0044-20` implementation and mandatory review. After governance activation, `0020-10` MAY resume without waiting for automation hardening only under a fresh exact coordinator award that includes `TODO.md` and every participating exact-item root claim, proves the canonical target-policy validator/digest, and commits the whole terminal transition atomically; otherwise it remains held.
- **Technical justification:** `TODO.md`, `AGENTS.md`, `docs/pipeline/task-acceptance.md`, and `docs/pipeline/branch-workflow.md` already require claims to finalize at `[x]`/`[w]` while remaining `TODO-*` until Acceptance. Current `main` implementation `0044-17` removed the obsolete `LTD-CLAIM-TERMINAL-RETAINED` emission and makes `DONE-*` an accepted-provenance state, but older branches can execute stale doctor bytes and block the governed state. `0020-10` demonstrates the cross-item failure: substantive work exists at `b4c1874678798353bcbdbf5ad2d08ce5e3c9ad7d`, while two participating claims and the Task marker require one coordinated terminal transition. Treating filenames as leases conflates provenance with ownership; permitting partial finalization instead creates contradictory authority state. Target-policy validation and exact-set atomicity preserve both legacy reproducibility and the integration contract.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  - **ALT-01:** Keep terminal, lease-free exact-item claims at `TODO-*` until Acceptance; make state/coordination the ownership signal; finalize every participating claim and the Task marker atomically; validate with target-policy semantics.
    - **Disposition:** `selected`
    - **Reason:** This matches all current authority documents, preserves provenance, prevents partial ownership state, and gives legacy candidates a deterministic policy baseline.
  - **ALT-02:** Rename claims to `DONE-*` at implementation completion.
    - **Disposition:** `rejected`
    - **Reason:** `DONE-*` is the accepted-item bookkeeping state; early rename would manufacture Acceptance semantics and erase the visible awaiting-review boundary.
  - **ALT-03:** Leave each branch to run its own historical doctor and repair only `0020-10` by exception.
    - **Disposition:** `rejected`
    - **Reason:** A stale validator would continue to override target governance, and a one-item exception would not resolve the repository-wide lifecycle contradiction.
  - **ALT-04:** Bulk-migrate all historical claims immediately.
    - **Disposition:** `rejected`
    - **Reason:** It would rewrite unrelated coordination state without exact ownership evidence and create an unnecessary high-blast-radius migration.
- **Consequences:**
  - **CON-01:** `TODO-*` is no longer interpreted as a lease without corroborating nonterminal state and current coordination evidence; consumers must inspect typed claim content.
  - **CON-02:** Terminal bookkeeping fails closed unless Task marker, REF, all participating exact-item root claims, lease release, and terminal coordination can be committed as one set.
  - **CON-03:** Acceptance remains separate: only its authorized bookkeeping transaction performs the byte-identical exact-item `TODO-*` to `DONE-*` rename.
  - **CON-04:** Legacy candidates are reproducible against their product bytes but policy-sensitive validation is pinned to the target integration policy; validation evidence records validator provenance and digest.
  - **CON-05:** Rollback before publication is path-limited revert. After publication this append-only decision may only be superseded by a new decision; implementation can be disabled by reverting `0044-20` while retaining manual fail-closed semantics.
  - **CON-06:** Migration is lazy and backward-compatible: no bulk rename, no history rewrite, accepted `DONE-*` remains valid, and an inconsistent old claim is reconciled only by a newly authorized exact transaction.
  - **CON-07:** `0020-10` may resume after governance lands only under the bounded conditions in the Decision; this record itself changes no `0020` product, marker, claim, award, or Acceptance state.
  - **CON-08:** Task `0044-20` implements and tests the contract; `0044-08` incorporates it into the Feature review floor. Both remain separately reviewed and integrated.
- **Affected work units:**
  - `repository:autodocs`
  - `feature:0044`
  - `task:0044-17`
  - `task:0044-20`
  - `task:0044-08`
  - `feature:0020`
  - `task:0020-10`
  - `path:TODO.md`
  - `path:docs/dossiers/0044-20-terminal-claim-lifecycle-scope-review.md`
- **Affected gates:**
  - `task-start:0044-20`
  - `validation:_src/tools/legacy_task_doctor.py`
  - `integration:0020-10`
  - `feature-closure:0020`
  - `integration:0044-20`
  - `integration:0044-08`
  - `feature-closure:0044`
- **Review participation:** `none`
- **No-review reason:** Management assigned this identity as the Architect to author both the conforming decision and a separate pre-mutation scope-review artifact. That supporting artifact is not a second identity, Acceptance, or an integration verdict; the later Implementer and Integrator must be distinct from this Architect.
- **Waiver:** `none`
