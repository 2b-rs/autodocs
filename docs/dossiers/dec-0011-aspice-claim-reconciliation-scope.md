# Management decision — documentation-only ASPICE claim reconciliation (`0011-03`)

**Status:** Decision and supporting-scope-review candidate. No Feature `0019`
or claim-language mutation is authorized until this record and the companion
Architect review are reachable on the applicable baseline through separately
authorized integration.

**Pinned inputs:** `main@f57faba37c4c8bcc7c68becdf732e694e0f377e4`;
preparation `fb4167f203cc54d399113b600fbb5631c0c6f330`
(`docs/dossiers/0011-03-aspice-claim-reconciliation.md`, SHA-256
`40694a5b9e6a8ac003116f42ae93635721d9f70cb5f6ee770a1af00947eee23f`);
resolved Management request `decision-1787978346367-bf78a92f`, option `A`,
resolved at `2026-08-29T11:04:02Z`; supervisor resolution notice
`agent-inbox:1788001443004-91dc736f`.

`DEC-0011-001` was absent from current `main` immediately before allocation.

---

### `DEC-0011-001` — Reconcile ASPICE claims as documentation evidence without creating a new gate

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-29T11:04:02Z`
- **Deciding identity:** `authority:current-user:autodocs:2026-08-29`
- **Role:** `Management`
- **Authority reference:** `decision-1787978346367-bf78a92f`; resolution notice `agent-inbox:1788001443004-91dc736f`
- **Subject:** Scope and authority boundary for `0011-03` reconciliation of Feature `0019` documentation-campaign evidence, current ASPICE claim language, the `0010` to `0019` alias, downstream evidence-coverage use, and named-process assessment boundaries.
- **Decision:** Select option A. Authorize a documentation-only reconciliation that preserves Feature `0019` evidence as `documentation-execution`; permits only candidate associations to named documentation-process outcome categories when the exact documentation product, project, process instance, origin, baseline, limitations, and contrary evidence are retained; reserves outcome achievement and `N`/`P`/`L`/`F` or capability-level decisions to an authorized assessment of the named process instance; corrects false attribution to an open Task; and adds a current-authority overlay without rewriting the dated 2026-08-15 survey. Preserve the active `0010` to `0019` renumbering provenance and the historical completed `0010`. Add no prerequisite, default/shared validator, publication blocker, lexical claim scanner, automatic rating, or repository-wide enforcement gate. Do not resolve the separate `0011-02` CL2 aggregation conflict under this decision.
- **Technical justification:** Feature `0019` generates controlled evidence for a documentation campaign, not proof that an ECU or documentation-process outcome is achieved. Narrow candidate associations improve traceability while exact origin and limitation labels prevent cross-product substitution. Outcome achievement and capability ratings require an authorized assessment using controlled process-instance evidence. Correcting current attribution and adding a dated-survey overlay removes misleading statements without falsifying historical observations. Because the reconciliation changes another Feature's acceptance and closure wording, `cross-item-blast-radius` applies even though the selected design deliberately creates no new gate.
- **Triggers:**
  - `cross-item-blast-radius`
- **Considered alternatives:**
  - **ALT-01:** Appoint independent Architect Data and authorize the documentation-only, no-new-gate reconciliation.
    - **Disposition:** `selected`
    - **Reason:** It is the smallest intent-preserving correction: it makes evidence associations explicit while retaining assessment authority, historical provenance, and existing gate boundaries.
  - **ALT-02:** Appoint another independent Architect to review the same bounded reconciliation.
    - **Disposition:** `rejected`
    - **Reason:** Management selected Data; changing the reviewer provides no scope benefit and would prolong the existing mutation pause.
  - **ALT-03:** Decline cross-item mutation and dispose `0011-03` without reconciliation.
    - **Disposition:** `rejected`
    - **Reason:** This would leave false open-Task attribution and ambiguous “map later” language unresolved despite a bounded, recoverable correction being available.
- **Consequences:**
  - **CON-01:** Feature `0019` campaign evidence may be traced only as candidate documentation-process evidence with exact instance, origin, baseline, limitation, and contrary-evidence labels; association does not satisfy an ECU or documentation-process outcome.
  - **CON-02:** Only the authorized `0025` or `0018` assessment path may judge applicable named-process outcome achievement or assign `N`, `P`, `L`, `F`, CL1, or CL2. This decision performs no assessment and supplies no rating.
  - **CON-03:** Feature `0019` retains its five local campaign-evidence conditions, `documentation-execution` origin, existing closure semantics, and existing prerequisites. No new gate, validator registration, scanner, or publication block is created.
  - **CON-04:** The dated survey remains historical and receives only a current-authority overlay. The `0010` to `0019` alias and historical completed `0010` remain discoverable and are not reinterpreted.
  - **CON-05:** `0011-06` may consume the reconciled language for evidence-coverage analysis but cannot credit unsupported outcomes or capability. The report evidence map must stop attributing established wording or future assessment execution to an open `0011-03`.
  - **CON-06:** The separate conflict between the historical CL2 survey rule and `0011-02` remains a blocking finding for any later CL2 claim; this record neither chooses a threshold nor changes `0011-02`.
  - **CON-07:** Before mutation, recovery is to withhold the candidate. After authorized integration, correction is additive: restore the last valid wording, preserve contrary evidence and history, record impact, and re-review any widened affected-unit or gate reach.
- **Affected work units:**
  - `task:0011-03`
  - `feature:0019`
  - `task:0019-10`
  - `task:0011-06`
  - `feature:0025`
  - `feature:0018`
  - `path:docs/pipeline/aspice-report-evidence-map.md`
  - `path:docs/ASPICE/README.md`
- **Affected gates:**
  - `feature-closure:0019`
  - `validation:0011-06-evidence-coverage-language`
  - `validation:0025-named-process-pa1.1-assessment`
  - `validation:0018-named-process-cl2-assessment`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:data:0011-03:1788001830555-9fa87053`
    - **Role:** `Architekt`
    - **Participation:** `reviewed`
    - **Position:** `supports`
    - **Note:** Independent pre-mutation review supports the narrowed documentation-only reach and confirms that no new gate, rating, alias rewrite, or historical rewrite is authorized; see `docs/dossiers/0011-03-architect-scope-review-data.md`.
- **Waiver:** `none`

---

## Activation and recovery boundary

This decision and the companion review must both be current on the applicable
baseline before the first qualifying Feature `0019` or claim-language mutation.
They are not implementation, Task Acceptance, an integration verdict, Feature
closure, or assessment evidence. Any later widening to a prerequisite, shared
validator, publication blocker, scanner, automatic rating, additional work
unit, or additional gate requires additive impact analysis and a new decision
and review when a mandatory trigger applies.
