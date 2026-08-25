# Managemententscheidung — Discovery-Runtime Cursor; Grok dekommissioniert

**Autorität:** Management (aktueller User), Beschluss in der Michael-Cursor-Session
2026-08-25 14:03 +02. Wortlaut:

> Was ist das Overlay? Cursor ist ab sofort die Runtime, grok ist dekommissioniert
> und wird bei rekommissionierung ein anderes Team bekommen.

**Protokollant:** `agent:michael:0037-11.01-authority:20260825T112400Z` (Project Lead
Discovery, `privileged`). Protokolliert die Entscheidung, trifft sie nicht
(`DEC-ROLE-001`). Mailbox is not authority.

**Identifier:** `DEC-0044-022`, geprüft gegen `main` `28d7a00918498685b1fc13b711840df415142ecf`
(höchste belegte Nummer dort `DEC-0044-021`). Keine Kollision in
`docs/dossiers/` zum Zeitpunkt der Zuteilung.

---

### `DEC-0044-022` — Team Discovery runtime is Cursor; grok is decommissioned

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-25T14:03:00+02:00`
- **Deciding identity:** `authority:current-user:autodocs:2026-08-25`
- **Role:** `Management`
- **Authority reference:** `path:docs/pipeline/agent-roster.md` (live Management instruction in the Michael Cursor session, 2026-08-25 14:03 +02; no agent-inbox ID)
- **Subject:** Authoritative Discovery team runtime/provider heading in `docs/pipeline/agent-roster.md`, and disposal of the uncommitted grok→cursor overlay that had blocked repository hygiene
- **Decision:** Cursor is the Discovery runtime and provider. Grok is decommissioned. If grok is recommissioned, it receives a different team and does not return as Discovery. The committed roster heading must match that fact. The uncommitted overlay in the shared root checkout is transferred onto a branch cut from `main` and then cleared from the root so hygiene can run.
- **Technical justification:** `docs/pipeline/agent-roster.md` on `main` still said `(Runtime: grok, Provider: grok)` while Discovery already ran on Cursor. That one-line uncommitted overlay in the shared root made `check_integration_hygiene.py` report `MAIN_WORKTREE_DIRTY` and blocked Feature merges (including `0037-11.01` and `0037-17` into `0037`) as well as `main` advances. Management named Cursor as the runtime; keeping grok on `main` would be a false directory, and leaving the overlay dirty would keep every integration stopped.
- **Triggers:**
  - `material-architecture-or-repository-behavior`
  - `cross-item-blast-radius`
- **Considered alternatives:**
  - **ALT-01:** Commit Cursor as Discovery runtime/provider; decommission grok; if grok returns, assign a different team; capture the overlay on a branch from `main` and restore the shared root.
    - **Disposition:** `selected`
    - **Reason:** Matches the Management instruction and removes the hygiene blocker without writing the shared root as the authoring surface.
  - **ALT-02:** Discard the overlay and keep committed grok.
    - **Disposition:** `rejected`
    - **Reason:** Management stated Cursor is the runtime and grok is decommissioned.
  - **ALT-03:** Leave the shared root dirty.
    - **Disposition:** `rejected`
    - **Reason:** `MAIN_WORKTREE_DIRTY` continues to block unrelated Feature merges and `main` advances.
- **Consequences:**
  - **CON-01:** `docs/pipeline/agent-roster.md` on this branch records Cursor as Discovery runtime/provider and states the grok decommission rule.
  - **CON-02:** After this commit is reachable, the shared root overlay at that path is restored to `HEAD` so the dirty line is no longer the only copy and no longer blocks hygiene.
  - **CON-03:** Advancing `refs/heads/main` remains the Discovery Integrator's act after hygiene; this record does not authorize a Project Lead merge.
  - **CON-04:** Recommissioning grok later requires a new Management decision and a different team assignment; it is not a silent roster edit.
- **Affected work units:**
  - `path:docs/pipeline/agent-roster.md`
  - `path:docs/dossiers/dec-discovery-runtime-cursor.md`
  - `repository:autodocs`
- **Affected gates:**
  - `validation:_src/tools/check_integration_hygiene.py`
  - `integration:repository-main`
- **Review participation:** `none`
- **No-review reason:** Management decided the runtime assignment in a live session. The change is the roster heading plus this record. It does not implement, widen, or retain a gate's declared behavior; the Architect gate-scope exception therefore does not apply. Clearing the overlay is separately authorized recovery of the shared root after the content exists on a branch.
- **Waiver:** `none`
