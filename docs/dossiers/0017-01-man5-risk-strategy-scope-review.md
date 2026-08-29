# Independent Architect scope review — `0017-01` MAN.5 option A

## Review identity and verdict

- **Verdict:** `scope-ok-with-conditions`
- **Reviewed at:** `2026-08-29T03:22:27Z`
- **Reviewer:** `agent:data:0017-01:1787973576019-d6c3b9ea`
- **Role:** management-instantiated Architect, Team Enterprise
- **Capability class:** `privileged`
- **Atomic award:** `1787973576019-d6c3b9ea`
- **Implementer:** `agent:tasha:0017-01:1787970918817-51821969`
- **Project Lead / decision requester:** `jean-luc`
- **Review type:** independent pre-mutation cross-item gate-scope review
- **Not:** implementation, Task Acceptance, integration review, integration
  verdict, residual-risk acceptance, release approval, specialist approval,
  ECU execution, Feature closure, `TODO.md` mutation, or `main` advancement

I support the exact candidate and Management option A subject to every condition
in section 7. This is the supporting Architect review required before the first
qualifying activation mutation. Green validation cannot substitute for it.

Companion decision: `DEC-0017-001` in
`docs/dossiers/dec-0017-001-man5-risk-strategy.md`.

## 1. Pinned baseline and inputs

| Input | Immutable reference / SHA-256 |
|---|---|
| Governance target | `main@8b966a2f85ca517029ed516ed496d4cc3287c15c` |
| Strategy candidate | `fe645c415c498a4fd83ccc6b5371c6ba28d2aba1` |
| `docs/dossiers/req-0017-01-risk-strategy.md` | `a2202fde9a63aaae6ec88f1c9ad9efcdb5f096693d0bf75adb0356b2493b712b` |
| Management decision | `decision-1787972295293-da9db52e`, option A, resolved `2026-08-29T03:17:26Z` |
| Resolution notice | `agent-inbox:1787973446577-7e3616ba` |
| `docs/pipeline/decision-record.md` | `dea2c93ad046d67a129d6b30b7715609a49afde26f47e5039cc2c2159cdb66c0` |
| `docs/pipeline/process-roles.md` | `a142e8885751c1c8a97faabfae7b6c579f1599333d3fd3e11ed869831191fc43` |
| `AGENTS.md` | `0aa1aaf6d0b219ef0cfddc90cc0dba3a26c920743fa1c6807fa1d8331fc5522f` |
| `REQ-0020-06` safety/cybersecurity boundary | `574704bf995c07d0664a4a2a70858add3e4a448bbb2fb667556acf4b0c898f1c` |
| Backlog contract | `TODO.md` SHA-256 `aaf5bce22370dcbd13a64044c5d6490cb017408ecc26a98124d2187923e4d8e2` |

`DEC-0017-001` was absent from current `main` immediately before allocation.
The reviewed candidate changes only its requirements dossier and implementer
claim; this Architect does not edit either candidate path.

## 2. Independence and authority boundary

Data is distinct from Implementer Tasha and Project Lead Jean-Luc. The resolved
Management choice supplies the product/authority decision; Data records it and
independently tests its reach. Privilege permits this bounded review and direct
execution, but does not create Acceptance, integration, release, specialist,
residual-risk, or Management authority.

Context used: the atomic award, exact candidate, durable decision-request record,
resolution notice reference, current governance, Feature `0017` / `0024` /
`0027` backlog contracts, and the approved safety/cybersecurity applicability
boundary. No private deliberation, desired verdict, implementation change, or
release authorization was supplied.

## 3. Canonical predicate and cross-item reach

The selected strategy qualifies under `cross-item-blast-radius`: its actual
declared behavior can block the start or validation of another work unit and can
block baseline use, verification conclusions, release readiness, external
action, and Feature closure.

| Consumer / gate | Reach and finding |
|---|---|
| `0017-02` | Existing start prerequisite on `0017-01`; the approved strategy becomes the register's scoring, authority, escalation, retention, and recovery contract. |
| `0017-03` | Consumes the `0017-02` register and must apply treatment, monitoring, effectiveness, escalation, acceptance, closure, and reopening semantics. |
| `0017-07` | Existing prerequisite on `0017-03`; management review must expose stale, High/Critical, unaccepted, or ineffectively treated risks rather than smoothing them into readiness. |
| `0027-03` | Instantiates real ECU MAN.5. The strategy definition is an input, never evidence that ECU risk management was performed. |
| Baselines and verification | High/Critical or authority/evidence uncertainty can invalidate baseline use or a verification conclusion until reduced or durably decided. |
| `0024-02` release | Existing prerequisite on `0027-03`; the release package consumes risk status, but this strategy does not grant release authority. |
| External/irreversible action | Critical requires immediate containment/stop; High remains blocked until reduced or durably decided under the approved authority. |

The decision adds no new `TODO.md` prerequisite edge. These are use-time and
validation/release semantics of the selected strategy plus existing backlog
dependencies.

## 4. Scoring and escalation finding

The proposed `1` through `5` probability and impact scales are reproducible,
the highest credible impact prevents averaging away material consequences, and
exposure `probability × impact` yields complete contiguous bands:

| Exposure | Class | Selected response boundary |
|---:|---|---|
| `1–4` | Low | Named owner and monitoring; residual decision remains Management-only. |
| `5–9` | Medium | Treatment, due date and effectiveness criterion; residual decision remains Management-only. |
| `10–15` | High | Escalate within one working day; treatment and contingency required; affected gate remains blocked until reduction or Management decision. |
| `16–25` | Critical | Immediate containment/stop and escalation; no release or irreversible/external action while unresolved. |

Unknown owner, authority, scope, baseline, recovery path, probability, impact,
or material evidence fails closed. A planned treatment does not lower exposure;
changed evidence and verified effectiveness are required.

## 5. Authority-separation finding

Option A deliberately centralizes interim human Sponsor, Process Owner, Risk
Manager, retention owner, and residual-risk authority in registered Management.
This is supportable as an explicit interim allocation, not as a transfer to the
repository role called `Management` or to an agent. Every residual decision for
every class remains an attributable decision by the registered human Management
authority.

The allocation does not combine these distinct actions:

- treatment execution and independent effectiveness verification;
- Task implementation and Task Acceptance;
- integration and implementation;
- residual-risk acceptance and release approval;
- Management risk decision and registered security/privacy/safety/cybersecurity
  specialist advice or approval.

A repository Project Lead, Dispatcher, Security Engineer, Architect,
Implementer, Integrator, QA role, or Task reviewer gains no residual-risk power
from coordination, privilege, review, or validation. If Management later
delegates any role or class, the exact human identity, scope, limits,
independence, duration/review, and recovery must be recorded additively and the
reach re-reviewed when a mandatory trigger applies.

## 6. Safety, cybersecurity, evidence, and recovery findings

- `REQ-0020-06` still excludes owned Automotive SPICE for Cybersecurity,
  ISO/SAE 21434, and ISO 26262 lifecycles for this increment. A plausible
  applicability signal is at least High and triggers the separate later
  Management decision required by `REQ-0020-06-07`; MAN.5 treatment cannot
  waive that boundary.
- No ASIL, TARA, HARA, safety case, cybersecurity case, complete ECU, kernel,
  hardware, or manufacturing claim is created.
- Strategy, decision, review, fixtures, and repository validation remain
  `process-definition` or governance evidence. Only controlled performance of
  the process instance can supply `ecu-execution` evidence.
- Recovery is additive: retain the last valid baseline and contrary evidence,
  contain the affected action, identify cause/impact/authority, restore or
  supersede under control, verify, and reopen affected risks before resumption.
  No accepted or closed risk is silently rewritten.

## 7. Binding conditions before activation

1. **C-01 — Exact baseline.** This support binds only candidate
   `fe645c415c498a4fd83ccc6b5371c6ba28d2aba1` with dossier SHA-256
   `a2202fde9a63aaae6ec88f1c9ad9efcdb5f096693d0bf75adb0356b2493b712b`.
2. **C-02 — Both products authoritative.** `DEC-0017-001` and this review must
   both reach the authoritative baseline before the strategy is operative or
   `0017-01` completion bookkeeping occurs.
3. **C-03 — Human Management only.** Every Low, Medium, High, and Critical
   residual decision requires the registered human Management authority; no
   agent or repository role receives delegation by implication.
4. **C-04 — Separations preserved.** Task Acceptance, integration, release,
   specialist approval, treatment execution, and effectiveness verification
   retain their separate authorities and independence requirements.
5. **C-05 — Gate semantics exact.** High escalates within one working day and
   blocks the affected gate until reduction or durable Management decision;
   Critical immediately contains/stops the affected action and blocks release
   and irreversible/external action while unresolved.
6. **C-06 — Safety/cybersecurity interface.** Applicability signals follow
   `REQ-0020-06-07`; neither this strategy nor ordinary treatment creates
   21434/26262 ownership or evidence.
7. **C-07 — Evidence origin.** No process definition, scenario, decision,
   review, or green repository validation is credited as ECU execution.
8. **C-08 — Drift and supersession.** Material candidate, product-boundary,
   threshold, authority, consumer, gate, or recovery drift invalidates this
   support and requires additive impact analysis plus renewed decision/review
   where triggered.
9. **C-09 — No grandfathering.** Historical or parallel strategies lacking the
   exact authority/review binding remain non-operative.

## 8. Exact verdict and handoff

**Verdict: `scope-ok-with-conditions`.** The exact option-A decision and
candidate are supported when conditions C-01 through C-09 all hold. There is no
authority for Data to activate the strategy, mutate the candidate or backlog,
perform Acceptance/integration, advance `main`/Feature refs, or accept any risk.

A separately assigned privileged Integrator may review and integrate only the
decision record, this review, and the claim from this branch. After both
governance products are authoritative, the existing Implementer may bind the
approved strategy and perform its separately authorized bookkeeping.
