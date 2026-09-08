# Managemententscheidung — erster bewerteter ECU-Zuschnitt (`0020-01`)

**Autorität:** Management (aktueller User), Beschluss in der Michael-Cursor-Session
2026-08-25 18:26 +02. Wortlaut:

> Wir entwickeln ausschließlich System- und Applikationssoftware für ein
> virtualisiertes Automotive-Steuergerät. Der Kernel befindet sich noch in
> Entwicklung und wird später hinzugefügt.

**Protokollant:** `agent:michael:0020-01:20260825T183100Z` (Project Lead Discovery,
`privileged`). Protokolliert die Entscheidung, trifft sie nicht (`DEC-ROLE-001`).
Mailbox is not authority.

**Identifier:** `DEC-0020-001`, geprüft gegen `main`
`6a937f8414440cc84233954012ff802eaf57924c` (kein `DEC-0020-*` dort; höchste
`DEC-0044-*` dort `DEC-0044-021`). Keine Kollision in `docs/dossiers/` auf
`main` zum Zeitpunkt der Zuteilung.

---

### `DEC-0020-001` — First assessed ECU unit is virtualized automotive ECU software, kernel later

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-25T18:26:00+02:00`
- **Deciding identity:** `authority:current-user:autodocs:2026-08-25`
- **Role:** `Management`
- **Authority reference:** live Management instruction in the Michael Cursor session, 2026-08-25 18:26 +02 (follow-up 18:31 +02 `gut, los geht's.`); no agent-inbox ID
- **Subject:** First assessed ECU product/variant and supplied-product boundary, organizational unit, intended use, lifecycle stage, increment, assessment purpose, target-profile starting point, and permitted claim wording for Feature `0020` Task `0020-01`.
- **Decision:** The assessed unit develops **only system software and application software** for a **virtualized automotive ECU**. The **kernel is still in development and is added later**; it is not in the current supplied-product boundary. The unit therefore does **not** own a complete ECU system lifecycle in this increment and does **not** currently supply the kernel. It owns software at and above the kernel interface. Permitted claim wording is exactly the Management sentence above; no kernel capability, no complete-ECU-system capability, and no hardware/manufacturing capability may be claimed from this increment. Working identifiers for later evidence metadata: `product_id=virtualized-automotive-ecu`, `project_id=autodocs-ecu-software`, `increment=software-without-kernel`. Assessment purpose remains PAM 4.0 Level 1 as stated by Feature `0020`. The starting target profile is the 14-process ECU software-delivery nucleus in `0020-04`; `SYS.1`–`SYS.5` and `VAL.1` are added only when later `0020-03`/`0020-04` show actual owned responsibility. Kernel, OS, and HWE processes are out of this increment.
- **Technical justification:** Task `0020-01` was `[u]` VERTAGT because the sponsor was unreachable; hanging Features `0011` and `0022`–`0032` were barred from autonomous pickup. Management has now given the missing scope sentence. Recording it as `[x]` with this bounded derivation unblocks successor start gates without inventing a product name, customer, or 20-process system profile that Management did not state. Treating "System- und Applikationssoftware" as software above the kernel, and "Kernel später" as a supplied-product exclusion, is the smallest reading that satisfies the Task's demand to say whether the unit owns a complete ECU system lifecycle or receives allocated software work.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
  - `authority-tailoring-or-waiver`
- **Considered alternatives:**
  - **ALT-01:** Record the Management sentence as the first assessed ECU boundary: virtualized automotive ECU; system and application software only; kernel excluded until a later increment; no complete-system-lifecycle ownership in this increment.
    - **Disposition:** `selected`
    - **Reason:** Matches the live Management instruction and supplies the observable `0020-01` result without adding unstated product, customer, or process-profile facts.
  - **ALT-02:** Keep `0020-01` `[u]` until a separately named competent assessor countersigns.
    - **Disposition:** `rejected`
    - **Reason:** Management explicitly authorized the `[x]` update with this wording in this session.
  - **ALT-03:** Treat the sentence as ownership of the complete ECU system lifecycle, including SYS and VAL, because it says "Systemsoftware".
    - **Disposition:** `rejected`
    - **Reason:** The same sentence excludes the kernel and limits the work to system and application software for a virtualized ECU; that is not complete ECU-system ownership.
  - **ALT-04:** Invent a named customer, release train, and 20-process profile to fill every 0020-01 noun.
    - **Disposition:** `rejected`
    - **Reason:** Those facts were not decided; inventing them would pre-empt `0020-03`/`0020-04` and misstate the claim.
- **Consequences:**
  - **CON-01:** Task `0020-01` may move to `[x]` with this record as the substantive deliverable; `0020-02` and other `0020-01` start-gated Tasks become implementation-eligible once this commit is reachable on their bases.
  - **CON-02:** Features `0011` and `0022`–`0032` are no longer barred solely by the 2026-08-22 VERTAGT; each Task still has its own prerequisites and must not treat this record as Feature `0020` closure or as `Acceptance: ✓`.
  - **CON-03:** Later Tasks must not claim kernel, hardware, or complete-system capability from this increment; adding the kernel requires a new Management decision and a new `DEC-0020-*` record.
  - **CON-04:** `0020-03`/`0020-04` still decide the process applicability matrix; this record only fixes the software-vs-kernel supplied-product boundary and the starting profile.
  - **CON-05:** Advancing `refs/heads/main` remains an Integrator act; this record does not authorize a Project Lead merge.
- **Affected work units:**
  - `task:0020-01`
  - `task:0020-02`
  - `task:0020-03`
  - `task:0020-04`
  - `feature:0020`
  - `feature:0011`
  - `feature:0022`
  - `feature:0027`
  - `feature:0028`
  - `feature:0029`
  - `feature:0030`
  - `feature:0031`
  - `feature:0032`
  - `repository:autodocs`
- **Affected gates:**
  - `task-start:0020-02`
  - `task-start:0020-03`
  - `task-start:0011-01`
  - `feature-closure:0020`
- **Review participation:** `none`
- **No-review reason:** Management decided the ECU supplied-product boundary in a live session and ordered the `[x]` update. The Project Lead only records it. This is the Task `0020-01` Management decision itself, not an implementer changing a gate's declared behavior; a separate Architect gate-scope review is not required to write down the authorized sentence.
- **Waiver:** `bounded`
  - **Conflict:** Task `0020-01` asked for sponsor/manager **and** competent-assessor agreement; this session named only Management.
  - **Reason:** Management explicitly authorized the `[x]` update with the quoted scope sentence and the follow-up `gut, los geht's.`
  - **Scope:** `task:0020-01` implementation marker `[x]` and this `DEC-0020-001` record only. No Feature `0020` `DONE.md` move, no `Acceptance: ✓`, no process-matrix in `0020-04`, no kernel inclusion.
  - **Duration:** `from 2026-08-25T18:26:00+02:00 until event:task-0020-01-acceptance`
  - **Compensating controls:**
    - **CTRL-01:** The Management sentence is retained verbatim in this record and in the `0020-01` history; later `0020-03`/`0020-04` and Task Acceptance may narrow, not silently widen, the claim.
    - **CTRL-02:** Kernel inclusion remains a future Management decision with a new `DEC-0020-*` identifier.
