# Management decision — MAN.5 risk-strategy activation boundary (`0017-01`)

**Status:** Decision and supporting-scope-review candidate. The strategy remains
non-operative until this record and the companion Architect review reach the
authoritative baseline through separately assigned privileged integration.

**Pinned inputs:** `main@8b966a2f85ca517029ed516ed496d4cc3287c15c`;
strategy candidate `fe645c415c498a4fd83ccc6b5371c6ba28d2aba1`
(`docs/dossiers/req-0017-01-risk-strategy.md`, SHA-256
`a2202fde9a63aaae6ec88f1c9ad9efcdb5f096693d0bf75adb0356b2493b712b`);
resolved Management request `decision-1787972295293-da9db52e`, option `A`,
resolved at `2026-08-29T03:17:26Z`; resolution notice
`agent-inbox:1787973446577-7e3616ba`.

---

### `DEC-0017-001` — Adopt the MAN.5 scoring and escalation model with Management retaining interim authority

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-29T03:17:26Z`
- **Deciding identity:** `authority:current-user:autodocs:2026-08-29`
- **Role:** `Management`
- **Authority reference:** `decision-1787972295293-da9db52e`; resolution notice `agent-inbox:1787973446577-7e3616ba`
- **Subject:** Approval boundary for the review-ready `0017-01` MAN.5 strategy, including probability and impact scales, exposure bands, escalation times, interim human role allocation, residual-risk authority, retention ownership, downstream baseline/verification/release gates, and ECU instantiation under `0027-03`.
- **Decision:** Select option A. Adopt the candidate's probability and impact scales of `1` through `5`, exposure calculation `probability × impact`, and bands `1–4` Low, `5–9` Medium, `10–15` High, and `16–25` Critical. High risks require escalation within one working day; Critical risks require immediate escalation and containment/stop of the affected action. All other candidate controls for lifecycle, cadence, reporting, retention, evidence origin, safety/cybersecurity interface, and recovery are adopted unchanged. The registered Management authority is, on an interim basis, the human Management Sponsor, MAN.5 Process Owner, Risk Manager, retention owner, and sole residual-risk decision authority for Low, Medium, High, and Critical risks. No residual-risk or MAN.5 authority is delegated to agents, repository Project Leads, Dispatchers, Implementers, Integrators, Task-Acceptance reviewers, release performers, or other repository roles. This role allocation does not grant Task Acceptance, integration, release, specialist, safety, cybersecurity, privacy, legal, or credential authority. The strategy creates no ECU-execution evidence and no ISO/SAE 21434 or ISO 26262 scope. It remains non-operative until this decision and the distinct supporting Architect scope review are both integrated on the authoritative baseline.
- **Technical justification:** The candidate supplies reproducible scoring, fail-closed uncertainty handling, treatment and effectiveness separation, durable retention, and explicit recovery while preserving the `software-without-kernel` boundary. Its High and Critical classes can block baselines, verification, external action and release, so an authenticated Management decision and independent scope review are mandatory before activation. Option A is the smallest authority expansion: it avoids fabricating named delegates or transferring human residual-risk authority to repository agents, while making the interim operating burden and every unchanged separation explicit.
- **Triggers:**
  - `cross-item-blast-radius`
  - `authority-tailoring-or-waiver`
  - `material-architecture-or-repository-behavior`
  - `public-release`
  - `material-risk-decision`
- **Considered alternatives:**
  - **ALT-01:** Approve the proposed thresholds and controls; registered Management retains all interim MAN.5 roles and sole residual-risk authority.
    - **Disposition:** `selected`
    - **Reason:** Preserves the candidate's fail-closed model without inventing delegates or granting human risk authority to agents, and permits independent review of the exact reach before activation.
  - **ALT-02:** Approve the proposed thresholds and controls with separately named human MAN.5 role holders and bounded residual-risk delegations.
    - **Disposition:** `rejected`
    - **Reason:** No complete set of named human holders, class limits, independence constraints, escalation recipients, retention ownership, or expiry conditions is currently recorded.
  - **ALT-03:** Return the strategy for bounded revision and do not activate it.
    - **Disposition:** `rejected`
    - **Reason:** Management selected the proposed scales, bands, escalation times, controls, and centralized interim authority without requesting content revision.
- **Consequences:**
  - **CON-01:** `0017-01` may bind the exact candidate to this decision only after this record and the companion Architect review are authoritative; neither record is Task Acceptance or implementation completion.
  - **CON-02:** Low, Medium, High, and Critical residual-risk decisions require a durable decision by the registered Management authority. No mailbox delivery, agent role, repository privilege, score calculation, or green validation substitutes for that decision.
  - **CON-03:** High risk blocks the affected baseline, commitment, verification conclusion, release readiness, or external action until exposure is reduced or Management records a residual decision; escalation is due within one working day. Critical risk requires immediate containment/stop and escalation, with no release or irreversible/external action while unresolved.
  - **CON-04:** Centralizing the interim Sponsor, Process Owner, Risk Manager, retention owner, and residual-risk authority creates capacity and concentration risk. Treatment execution, effectiveness verification, Task Acceptance, integration, specialist advice/approval, and release decisions remain separately attributable and cannot be silently combined through this record.
  - **CON-05:** `0017-02`, `0017-03`, and `0017-07` consume the approved strategy; `0027-03` instantiates it for real ECU MAN.5 execution. Strategy text, fixtures, or repository decisions remain `process-definition`, not `ecu-execution` evidence.
  - **CON-06:** A safety/cybersecurity applicability signal is at least High and remains blocked pending the separate Management decision required by `REQ-0020-06-07`. This record adds no Automotive SPICE for Cybersecurity, ISO/SAE 21434, ISO 26262, ASIL, TARA, HARA, safety-case, or cybersecurity-case scope.
  - **CON-07:** Supersession, role delegation, changed thresholds, product-boundary drift, or altered downstream gate reach requires additive impact analysis and a new decision/review when a mandatory trigger applies. No historical or parallel risk strategy is implicitly grandfathered.
  - **CON-08:** Before activation, recovery is to withhold or reject the candidate. After activation, recovery preserves the last valid baseline, records containment and cause/impact, restores or rolls back under named authority, re-verifies, and additively reopens affected risks.
- **Affected work units:**
  - `task:0017-01`
  - `task:0017-02`
  - `task:0017-03`
  - `task:0017-07`
  - `task:0027-03`
  - `task:0024-02`
  - `feature:0017`
  - `feature:0027`
- **Affected gates:**
  - `task-start:0017-02`
  - `validation:0017-02-risk-register`
  - `validation:0017-03-treatment-and-monitoring`
  - `validation:0017-07-management-review`
  - `validation:0027-03-ecu-man5-execution`
  - `validation:baseline-risk-status`
  - `validation:verification-risk-status`
  - `release:virtualized-automotive-ecu-software-without-kernel`
  - `feature-closure:0017`
  - `feature-closure:0027`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:data:0017-01:1787973576019-d6c3b9ea`
    - **Role:** `Architekt`
    - **Participation:** `reviewed`
    - **Position:** `supports`
    - **Note:** Independent pre-mutation review supports the exact option-A scope with the activation, separation, safety/cybersecurity, drift, and recovery conditions recorded in `docs/dossiers/0017-01-man5-risk-strategy-scope-review.md`.
- **Waiver:** `none`

---

## Activation, self-application, and recovery

- **Activation:** This decision and the companion review must both be current on
  the authoritative baseline before the candidate strategy is treated as
  operative or `0017-01` completion bookkeeping is performed.
- **Self-application:** The first activated MAN.5 baseline receives no bootstrap
  exemption. Its own activation risk, authority identity, retention, and
  recovery path are subject to the selected model.
- **No implicit grandfathering:** Earlier or parallel strategy text lacking the
  exact authority and review binding is non-operative.
- **Rollback:** Before activation, withhold the candidate. After activation,
  retain prior baselines and decisions, contain the affected action, record the
  cause and impact, obtain the responsible authority, restore or supersede
  additively, and independently re-verify before resumption.
