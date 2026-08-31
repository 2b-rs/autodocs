# Management decision — Feature 0033 / 0033-02 through 0033-04 recovery strategy

**Authority:** Management (current user), decision routed and resolved through the
structured `decision_request` tool as `decision-1787966578186-b32fcd6e`
(item `0033-chain`, requester Project Lead `jadzia`), resolved `option-a` at
`2026-08-29T01:49:27Z`. Durable archive:
`logs/agent-inbox/decision-requests/decision-1787966578186-b32fcd6e.json`.

**Recorder:** `agent:kathryn:0033-chain:20260830T1100Z` (Project Lead, Team Voyager,
`privileged`). Records the decision, does not make it (`DEC-ROLE-001`). Mailbox and
the agent-inbox decision archive coordinate and durably store the decision; this
canonical record is the `docs/pipeline/decision-record.md` `decision-record@v1`
projection required as gate 1 of the *Cross-item gate-scope review exception*
(`AGENTS.md`) before any `0033-02`/`03`/`04` mutation. Gap found and reported by
Dispatcher `chakotay` (thread `0033-chain`, 2026-08-30T10:58Z): the required
`decision-record@v1` did not exist on `main` even though the underlying Management
decision had already been resolved — only the informal `decision_request` JSON
existed, and the Architect scope review (`0033-02-04-architect-scope-review.md`,
gate 2) explicitly disclaims being this record.

**Identifier:** `DEC-0033-002`, checked against `main` `1bc5ca6f8e4934c6fe5fb5fa55795541100da94c`
(highest allocated Feature-0033 number there: `DEC-0033-001`) and against every
branch reachable at allocation time (`git grep DEC-0033-002` across all refs:
no hit). No collision.

---

### `DEC-0033-002` — Adopt Option A (reconstruct on current baseline) for the 0033-02/03/04 recovery

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-30T11:05:00+02:00`
- **Deciding identity:** `authority:current-user:autodocs:2026-08-29`
- **Role:** `Management`
- **Authority reference:** `decision-1787966578186-b32fcd6e` (agent-inbox decision-request archive, resolved `option-a`, `2026-08-29T01:49:27Z`)
- **Subject:** Which recovery strategy governs reintroducing the historical `0033-02`/`0033-03`/`0033-04` candidate suite (process reconciliation, package/envelope redesign, UX contract) into the current Feature `0033` plan, given the candidates modify binding `docs/pipeline/` paths, declare gates affecting 19 downstream Tasks, diverge materially from current `main`/`TODO.md`, carry no current Task lifecycle or Acceptance state, and (`0033-04` specifically) inherit foreign `0039-05.01` Acceptance-policy ancestry.
- **Decision:** Adopt **Option A**: keep the historical branches (`0033-02`, `0033-03`, `0033-04`, `0033-03.01`, and related) immutable as evidence only. After a distinct Management-instantiated Architect binds the exact cross-item scope (gate 2 of the exception; delivered as `docs/dossiers/0033-02-04-architect-scope-review.md`), create new bounded Task work from current `main`. Recover reviewed content by deliberate reconstruction — not history merge, not cherry-pick: reconcile process/privacy choices, then schema/identity/trust choices, then UX/storage/no-JS choices against both, approve the combined suite through the current authorized gate (`0033-04.01`), and only then update binding `docs/pipeline/` documents and downstream implementation contracts through their own current branches/checkpoints.
- **Technical justification:** Option A is the only option that preserves the historical suite's substantial useful analysis, fixtures, canonical vectors, migration cases, and accessibility/no-JS scenario maps while respecting current governance placement (`DEC-0044-012`/`-010`/`-015`: mutation only in item-owned worktrees, governance changes only via their authorized route) and avoiding import of obsolete `TODO.md` bookkeeping or the foreign `0039-05.01` ancestry braided into historical `0033-04`. Option B (adopt the old branches substantially as written) was rejected: it would overwrite materially changed pipeline governance, make unapproved content appear binding, and bypass the cross-item gate-scope procedure entirely. Option C (retire and redesign from scratch) was rejected as available but not preferred: it discards exhaustive already-solved process, schema, and UX decisions and risks recreating already-resolved contradictions, with no compensating benefit over reconstruction. Full comparative analysis: `docs/dossiers/0033-02-04-recovery-decision-packet.md@2e8649b410` §3.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  - **ALT-01 (Option A):** Reconstruct selected candidates on the current baseline.
    - **Disposition:** `selected`
    - **Reason:** Preserves useful analysis and fixtures, respects current governance placement, avoids importing obsolete history or foreign `0039-05.01` ancestry, makes the proposal-to-operative transition explicit and independently reviewable.
  - **ALT-02 (Option B):** Adopt the old branches substantially as written.
    - **Disposition:** `rejected`
    - **Reason:** High risk of overwriting pipeline governance, importing unapproved content as binding, inheriting conflicting foreign ancestry, and bypassing the cross-item gate-scope procedure.
  - **ALT-03 (Option C):** Retire the historical suite and redesign from current requirements.
    - **Disposition:** `rejected`
    - **Reason:** Cleanest design but discards substantial solved work (process decisions, canonical vectors, migration cases, accessibility scenarios) with material risk of recreating already-resolved contradictions; viable only if the candidate architecture itself were rejected, which Management did not find.
- **Consequences:**
  - **CON-01:** Reconstruction requires fresh current-baseline reconciliation and validation; historical test results are evidence, not proof against current code.
  - **CON-02:** Every selected policy axis (packet §4, `PROC-0033-02-01`..`17`) needs explicit authority and traceability before it becomes operative.
  - **CON-03:** A distinct Architect scope review is required before implementation start (delivered: `docs/dossiers/0033-02-04-architect-scope-review.md`, award `1788082770141-bdcbc5f9`); it in turn found the packet's factual premise (all three Tasks `[ ]`/reopened) had been invalidated by an intervening false bulk marker-flip, requiring a separate append-only `TODO.md` repair (`fce918a6a`) before reconstruction has a lawful target.
  - **CON-04 (residual risk, accepted):** The historical branches remain reachable and unpruned as read-only evidence; they are not deleted, only never merged/cherry-picked directly.
- **Affected work units:**
  - `task:0033-02`
  - `task:0033-03`
  - `task:0033-04`
  - `task:0033-04.01`
  - `task:0033-05`
  - `task:0033-06`
  - `task:0033-07`
  - `task:0033-07.01`
  - `task:0033-07.02`
  - `task:0033-07.03`
  - `task:0033-07.04`
  - `task:0033-08`
  - `task:0033-09`
  - `task:0033-10`
  - `task:0033-11`
  - `task:0033-12`
  - `task:0033-13`
  - `task:0033-14`
  - `task:0033-15`
  - `task:0033-15.01`
  - `task:0033-15.02`
  - `task:0033-16`
  - `task:0033-16.01`
  - `path:docs/pipeline/`
- **Affected gates:**
  - `task-start:0033-02`
  - `integration:0033-04.01`
  - `integration:0033-07.02`
  - `integration:0033-16.01`
- **Review participation:** `none`
  - **No-review reason:** The decision was resolved directly by Management (current user) through the structured `decision_request`/`decision_status` channel rather than a specialist review round; the required independent technical check on scope, reach, and authority is instead satisfied by the separate, distinct-Architect scope review mandated as gate 2 of the same cross-item exception (`docs/dossiers/0033-02-04-architect-scope-review.md`, Architect `seven`, distinct from Implementer `chakotay`).
- **Waiver:** `none`
