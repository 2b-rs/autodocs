# Managemententscheidung — ff-only Landung von `roster-discovery-cursor-20260825` auf `main`

**Autorität:** Management (aktueller User), Beschluss in der Michael-Cursor-Session
2026-08-25 18:49 +02. Wortlaut:

> kannst du die Entscheidung zum Mergen nicht schonmal notieren?

Vorher in derselben Session: **A** (2026-08-25 17:58 +02) additive Rekonziliation
von dann aktuellem `main` `6a937f841` in diesen Governance-Zweig; **B**
(2026-08-25 18:47 +02) Ausführung des Integrator-Auftrags noch nicht in dieser
Session.

**Protokollant:** `agent:michael:roster-discovery-cursor:20260825T140300Z`
(Project Lead Discovery, `privileged`). Protokolliert die Entscheidung, trifft
sie nicht (`DEC-ROLE-001`). Mailbox is not authority.

**Identifier:** `DEC-0044-024`, geprüft gegen `main`
`6a937f8414440cc84233954012ff802eaf57924c` (höchste belegte Nummer dort
`DEC-0044-021`) und gegen `DEC-0044-022` / `DEC-0044-023` auf Branch
`roster-discovery-cursor-20260825`. Keine Kollision `DEC-0044-024` in
`docs/dossiers/` auf `main` zum Zeitpunkt der Zuteilung.

---

### `DEC-0044-024` — Authorize ff-only landing of `roster-discovery-cursor-20260825` onto `main`; execute only in the Paul session

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-25T18:49:00+02:00`
- **Deciding identity:** `authority:current-user:autodocs:2026-08-25`
- **Role:** `Management`
- **Authority reference:** live Management instruction in the Michael Cursor session, 2026-08-25 18:49 +02 (verbatim request to record the merge decision; prior A 17:58 +02 and B 18:47 +02 in the same session); no agent-inbox ID
- **Subject:** Whether and how the Discovery Integrator may advance `refs/heads/main` to the `DEC-0044-022`/`023` governance line on `roster-discovery-cursor-20260825`, and how that landing is ordered relative to Feature `0020`.
- **Decision:** The authorized merge is a fast-forward of `refs/heads/main` to the tip of `refs/heads/roster-discovery-cursor-20260825` that contains this record (`DEC-0044-024`), performed from the shared root checkout `/Users/tobias.anton/devel/autodocs` with `git merge --ff-only`. Hygiene plus root-preflight run immediately before and after (`python3 _src/tools/check_integration_hygiene.py --repo <integration-worktree> --candidate-ref <candidate>` and `--repo <root> --root-preflight`). Checkpoint `0044-04` (`361f0ce44`, merge `6a937f841`) remains an ancestor. Do not merge stale candidate `42eb0e98b` as the landing tip. Do not land Feature `0020` / `ae7a4e93f` onto `main` before this governance landing. Do not use `git update-ref` on `refs/heads/main`. The Project Lead does not advance `main`. Mail is not the Integrator assignment. Execution remains gated on an exact assignment in the Paul session. This record authorizes that merge; it does not itself perform it.
- **Technical justification:** Management already chose additive reconciliation of current `main` into this branch (A). The remaining Integrator act is the matching ff-only landing. Recording it now, before the Paul-session assignment, prevents a second human A/B on the same already-chosen candidate kind while still keeping execution off mail and off the Project Lead. Landing `0020` first would stale this governance pin (merge-base of the two lines is current `main`). Landing `42eb0e98b` would drop the later additive merge that made ff-only possible again.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
  - `irreversible-or-external-effect`
- **Considered alternatives:**
  - **ALT-01:** Record the ff-only authorization now; keep execution until an exact assignment in the Paul session; candidate is the tip of `roster-discovery-cursor-20260825` that contains this record; `0020` waits.
    - **Disposition:** `selected`
    - **Reason:** Matches the live request to note the merge decision already, preserves `DEC-0044-015`/`021` (Integrator-only `main` advance; no `update-ref`), and keeps the previously chosen wait-on-assignment (B).
  - **ALT-02:** Wait to record anything until Paul is assigned and the merge has happened.
    - **Disposition:** `rejected`
    - **Reason:** Management asked to record the decision now, before execution.
  - **ALT-03:** Project Lead advances `refs/heads/main` from this session.
    - **Disposition:** `rejected`
    - **Reason:** `DEC-0044-015` and `DEC-0044-021` reserve that act for the assigned privileged Integrator.
  - **ALT-04:** Land `0020` / `ae7a4e93f` on `main` first.
    - **Disposition:** `rejected`
    - **Reason:** That fast-forward would stale `roster-discovery-cursor-20260825`; the two lines are siblings on `6a937f841`.
  - **ALT-05:** Treat stale `42eb0e98b` as the merge candidate.
    - **Disposition:** `rejected`
    - **Reason:** That tip is not a descendant of current `main`; ff-only is impossible and would drop the A-authorized additive merge.
- **Consequences:**
  - **CON-01:** This commit moves the Integrator candidate tip off `8931c8ffa`. Paul must remeasure the new SHA; previous pin confirmations are historically correct and stale for execution.
  - **CON-02:** After a successful ff-only landing, `main` carries `DEC-0044-022`, `DEC-0044-023`, and this record. Feature `0020` remains a sibling until it is caught onto that new `main` and then landed in a later Integrator act.
  - **CON-03:** A failing hygiene or root-preflight is a stop, not a tidy-up. Recovery is separately authorized.
  - **CON-04:** This record is not Task Acceptance, not Feature closure, not a second Integrator path, and not permission to spawn a substitute Integrator.
  - **CON-05:** Recording here does not assign Paul. The paste-ready assignment stays for the Paul session only.
- **Affected work units:**
  - `path:docs/dossiers/dec-0044-024-governance-ff-main.md`
  - `path:docs/dossiers/dec-discovery-runtime-cursor.md`
  - `path:docs/dossiers/dec-as-verify-0038-34-registration-20260825.md`
  - `path:docs/pipeline/agent-roster.md`
  - `feature:0020`
  - `feature:0037`
  - `repository:autodocs`
- **Affected gates:**
  - `validation:_src/tools/check_integration_hygiene.py`
  - `integration:repository-main`
  - `feature-closure:0020`
- **Review participation:** `none`
- **No-review reason:** Management ordered the already-chosen ff-only landing written down before execution. The Project Lead only records it. The Integrator still performs the independent hygiene verdict at execution time. This record does not implement, widen, or rewrite the hygiene checker's declared behavior.
- **Waiver:** `none`
