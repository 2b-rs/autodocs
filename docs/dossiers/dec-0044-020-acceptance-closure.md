# Acceptance closure and late checkpoint designation

## Management directive 2026-08-23

The current user directed that Task Acceptance must include every required
`[x]` predecessor, while preserving the distinction that an unaccepted,
unmarked predecessor ordinarily does not block implementation of a successor.
The user further directed that checkpoint placement remains exclusively within
the Architect's authority and that the statement limiting reviews to marked
checkpoints must say explicitly that an Architect may add a checkpoint to a
Task at any time while that Task has not yet received current Acceptance.

Stable authority identity: `authority:current-user:acceptance-closure:20260823`.

### `DEC-0044-020` — Separate implementation flow from prerequisite-closed Acceptance and freeze checkpoint placement at Acceptance

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-23T17:33:18Z`
- **Deciding identity:** `authority:current-user:acceptance-closure:20260823`
- **Role:** `Management`
- **Authority reference:** `docs/dossiers/dec-0044-020-acceptance-closure.md#management-directive-2026-08-23`
- **Subject:** Repository-wide relationship between implementation-start prerequisites, transitive Task Acceptance, Feature closure, and the Architect's authority to designate integration checkpoints before Acceptance.
- **Decision:** Ordinary successor implementation may begin when its required predecessor is implementation- or disposition-complete (`[x]`/`[w]`) unless an explicit acceptance-before-start edge says otherwise. Task Acceptance is nevertheless prerequisite-closed: every required transitive `[x]`/`[w]` predecessor without current valid Acceptance enters the same bottom-up Acceptance batch and receives its own decision before the dependent Task can receive current `Acceptance: ✓`. Checkpoint designation remains exclusively an Architect decision. An Architect may add `Integration review: mandatory` to a Task at any time while that Task lacks current Acceptance; a Task with current Acceptance is outside that late-designation window, without prejudice to separately authorized append-only invalidation or reopening under the existing change rules.
- **Technical justification:** Implementation throughput and Acceptance assurance are separate lifecycle concerns. Allowing `[x]`/`[w]` to satisfy the ordinary implementation-start gate avoids serializing construction behind privileged review, while prerequisite-closed Acceptance prevents a dependent accepted baseline from resting on unaccepted work. Allowing the Architect to designate a checkpoint until Acceptance preserves risk-based review when risk becomes visible after decomposition; closing that window at current Acceptance prevents a silent retroactive change to an already accepted baseline and leaves later changes to the existing invalidation and decision process.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  - **ALT-01:** Preserve non-blocking implementation starts, require transitive bottom-up Acceptance, and allow Architect checkpoint designation until current Acceptance
    - **Disposition:** `selected`
    - **Reason:** It preserves delivery concurrency while making the Acceptance boundary complete and the Architect's late-checkpoint authority explicit.
  - **ALT-02:** Require every predecessor to be accepted before successor implementation starts
    - **Disposition:** `rejected`
    - **Reason:** It serializes ordinary implementation behind scarce privileged review and contradicts the intended `[x]`/`[w]` implementation-start semantics.
  - **ALT-03:** Fix checkpoint placement permanently at initial Feature decomposition
    - **Disposition:** `rejected`
    - **Reason:** It prevents the Architect from responding to material risk discovered before Acceptance.
  - **ALT-04:** Permit checkpoint designation after current Acceptance without invalidation or reopening
    - **Disposition:** `rejected`
    - **Reason:** It would retroactively alter a digest-bound accepted baseline without the existing append-only invalidation controls.
- **Consequences:**
  - **CON-01:** Acceptance reviewers must enumerate the complete transitive prerequisite closure, stop at current valid Acceptance boundaries, and issue individual bottom-up decisions for every remaining `[x]`/`[w]` predecessor.
  - **CON-02:** Unmarked and unaccepted work remains consumable for ordinary successor implementation but cannot be silently omitted from a later Acceptance batch or Feature-closure evidence.
  - **CON-03:** A newly added checkpoint before Acceptance changes the integration-review requirement for that not-yet-accepted Task and must carry the Architect's recorded rationale and any separately required cross-item scope record/review.
  - **CON-04:** Existing current Acceptance cannot be bypassed or silently rewritten to add a checkpoint; relevant later change follows append-only invalidation, reopening, and reacceptance rules.
- **Affected work units:**
  - `repository:autodocs`
  - `feature:0038`
  - `path:TODO.md`
  - `path:AGENTS.md`
  - `path:docs/pipeline/task-acceptance.md`
- **Affected gates:**
  - `integration:0038`
  - `feature-closure:0038`
- **Review participation:** `none`
- **No-review reason:** The Management decision is recorded before implementation so the mandatory independent Architect scope review can assess an exact decision baseline; normative mutation remains prohibited until that separate review exists and supports the declared reach.
- **Waiver:** `none`
