# Atomic implementation check-in and Acceptance-owned commit references

## Management directive — 2026-08-26

The current user, acting through the live registered Management route, stated:

> lass uns entscheidung für 0041 treffen und dokumentieren. 0041 geht dann an
> benjamin.

After receiving the complete A/B decision packet, the current user selected:

> A

Stable deciding identity: `authority:repository-owner`. This document is the
first durable repository capture of that direct decision. Project Lead mailbox
messages transported the assignment and verbatim provenance; they are not the
authority that made the decision. Recording the decision does not assign
Benjamin, authorize implementation, or activate the new completion contract.

### `DEC-0041-006` — Replace two-commit implementation closure with one atomic self-describing check-in

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-26T14:56:01+02:00`
- **Deciding identity:** `authority:repository-owner`
- **Role:** `Management`
- **Authority reference:** `docs/dossiers/dec-0041-006-atomic-implementation-checkin.md#management-directive-2026-08-26`
- **Subject:** Repository-wide implementation/disposition completion, `Task-ID` and `Base-Ref` provenance, Acceptance-owned commit references, history-reconstruction limits, migration, and atomic activation for Feature `0041`.
- **Decision:** Replace the `[p]` to `[x]`/`[w]` two-commit implementation procedure with one atomic, self-describing implementation or disposition commit. That carrying commit contains the complete deliverable/disposition, finalized claim state, and terminal marker, and carries full `Task-ID` and `Base-Ref` trailers. `Base-Ref` is the exact branch commit immediately before the first substantive change and must be an ancestor of the carrying commit. No separate implementation-bookkeeping commit is created, and `[x]`/`[w]` has no impossible requirement to contain the carrying commit's own hash as `REF`. Open work records neither implementation nor review commit identity. Later Acceptance records additively pin the exact implementation/disposition commit and the exact review-decision commit, together with the required baseline and digests. After substantive work begins, squash and rebase history rewriting are prohibited. When unavoidable reconstruction is separately authorized, it preserves the abandoned lineage as provenance and establishes a new recorded base, claim, and carrying commit rather than pretending continuity. Historical terminal evidence remains unchanged. Preparation may proceed in bounded stages, but the new rule activates atomically only when the governance text, `_src/tools/runner_transaction.py`, `_src/tools/legacy_task_doctor.py`, and matching guidance enforce one contract; `0041-05` then validates the integrated flow end to end. The current two-commit/implementation-`REF` rule remains operative until that cutover.
- **Technical justification:** The historical analysis in `docs/dossiers/0041-entscheidungen-und-base-ref-analyse.md` shows that an atomic commit cannot contain its own Git hash and that `Base-Ref` cannot be reconstructed reliably from merge-base after preintegration. Saru's independent review at `89e17a52504bd4e47375a90199d7016a4ef71f85` confirms that candidate `8b1afb933f0f9029d09c2fd3e9660aad3a8fa9a3` would activate repository-wide completion prose while the runner transaction and legacy doctor still enforce the old two-commit/`REF` contract. Historical `DEC-0041-001` through `DEC-0041-005` remain structurally nonconforming evidence and are not retroactively converted into v1 authority; this record is the current conforming renewal of the selected semantics. The selected design removes the self-reference, keeps provenance machine-checkable through trailers and ancestry, moves commit identity to the additive Acceptance stage where the hashes exist, and prevents a split-brain cutover by retaining the old rule until all normative and executable consumers agree.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
  - `material-risk-decision`
- **Considered alternatives:**
  - **ALT-01:** Stage preparation and atomically activate one self-describing implementation/disposition commit with `Task-ID` and ancestor `Base-Ref`, while Acceptance later pins implementation and review commits.
    - **Disposition:** `selected`
    - **Reason:** It removes the impossible self-reference, preserves attributable Git provenance, and prevents authority text from diverging from runner and doctor enforcement.
  - **ALT-02:** Retain the two-commit implementation closure and mandatory implementation `REF` in `[x]`/`[w]`.
    - **Disposition:** `rejected`
    - **Reason:** The second commit is structurally dependent on the first hash and can be omitted or interrupted, which is the documented pipeline-stall mechanism Feature `0041` exists to remove.
  - **ALT-03:** Activate the new governance prose before the runner transaction, legacy doctor, and guidance are aligned.
    - **Disposition:** `rejected`
    - **Reason:** It creates two contradictory completion contracts and causes conforming work under either side to fail another repository-wide gate.
  - **ALT-04:** Infer `Base-Ref` after completion from merge-base and permit squash/rebase to normalize the resulting history.
    - **Disposition:** `rejected`
    - **Reason:** Merge-base identifies ancestry inputs rather than the exact post-preintegration start state, and history rewriting destroys the provenance that the trailers are intended to bind.
  - **ALT-05:** Rewrite historical terminal records and old accepted evidence into the new representation during cutover.
    - **Disposition:** `rejected`
    - **Reason:** Historical evidence was valid under its contemporaneous contract; rewriting it would fabricate provenance, invalidate digest-bound review history, and exceed the bounded forward cutover.
- **Consequences:**
  - **CON-01:** Every post-cutover implementation/disposition completion is one atomic Git transaction whose tree and message jointly establish Task identity, start baseline, deliverable/disposition, claim finalization, and terminal marker.
  - **CON-02:** The carrying commit's `Base-Ref` must be a full reachable ancestor and must equal the branch state recorded before first substantive change; missing, malformed, non-ancestor, stale, or contradictory trailers fail closed.
  - **CON-03:** Acceptance, not implementation bookkeeping, records the exact implementation/disposition commit and exact review-decision commit additively with its baseline, manifests, prerequisite state, and digests. This decision does not grant Acceptance or alter reviewer independence.
  - **CON-04:** Existing terminal and accepted history remains readable under the rule that governed it. No implicit grandfathering applies to new or materially reopened post-cutover work; a reopened item uses the new rule for its new delta while preserving earlier evidence.
  - **CON-05:** Preparation is ordered but non-operative: governance wording, runner transaction, legacy doctor, and guidance may be developed on bounded branches, but the repository-wide rule changes only at one reviewed cutover where all four agree. Until then, the current two-commit/implementation-`REF` contract remains authoritative.
  - **CON-06:** `0041-02`, `0041-03`, `0041-04`, and `0041-06` require manual re-derivation on current main under this decision rather than cherry-pick, squash, rebase, or implicit reuse of their stale lineages. `0041-05` remains the mandatory end-to-end integration/review floor.
  - **CON-07:** Unavoidable reconstruction is exceptional and separately authorized: retain the abandoned candidate/claim/base as immutable provenance, create a new branch/claim/base, and validate the new carrying commit. The exception never permits silent history rewriting.
  - **CON-08:** Rollback before atomic activation abandons staged candidates without changing the operative two-commit rule. Rollback after activation reverts governance, runner, doctor, and guidance together to one previously coherent contract, preserves all new and old evidence, and requires impact analysis for work completed under the activated rule.
  - **CON-09:** The direct Management statement that Feature `0041` later goes to Benjamin is recorded as intent only; this decision creates no assignment, claim ownership, implementation authority, review independence, Acceptance, integration authority, or activation by Benjamin.
  - **CON-10:** Historical `DEC-0041-001` through `DEC-0041-005`, terminal records, review findings, and candidate branches remain append-only evidence under their original contracts. `DEC-0041-006` supplies current v1 authority prospectively and does not rewrite, validate, accept, or integrate those lineages.
- **Affected work units:**
  - `repository:autodocs`
  - `feature:0041`
  - `task:0041-02`
  - `task:0041-03`
  - `task:0041-04`
  - `task:0041-05`
  - `task:0041-06`
  - `path:AGENTS.md`
  - `path:SANDBOX.md`
  - `path:PRIVILEGED.md`
  - `path:TODO.md`
  - `path:_src/tools/runner_transaction.py`
  - `path:_src/tools/legacy_task_doctor.py`
  - `path:docs/pipeline/branch-workflow.md`
  - `path:docs/pipeline/task-acceptance.md`
  - `path:docs/pipeline/runner-transaction.md`
- **Affected gates:**
  - `validation:_src/tools/runner_transaction.py`
  - `validation:_src/tools/legacy_task_doctor.py`
  - `validation:docs/pipeline/task-acceptance.md`
  - `integration:0041-02`
  - `integration:0041-03`
  - `integration:0041-04`
  - `integration:0041-06`
  - `integration:0041-05`
  - `feature-closure:0041`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:data:0041-02:dec-0041-006-20260826T125524Z-5086733f`
    - **Role:** `Architekt`
    - **Participation:** `reviewed`
    - **Position:** `supports`
    - **Note:** Data translated the direct Management choice into this bounded record and checked the interface, migration, activation, rollback, and separation conditions. This participation is not the independent supporting gate-scope review and excludes Data from that later review and implementation.
- **Waiver:** `none`
