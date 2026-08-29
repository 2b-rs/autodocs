# Feature `0028` architecture breakdown

**Status:** governance candidate; non-operative until separately reviewed and
integrated to `main`. Feature implementation remains gated by its declared
prerequisites and the fail-closed SYS.1 activation contract.

**Current-main reconstruction:** The source-owned candidate at
`8aff32728d427e65342345a5a0e7d881583722a6` was reconstructed without unrelated
history on exact `main@21bea51f3ff340e8125dfb6530430df388f7a5ba` under atomic
award `1788046717031-ed4daf2d`. Historical derivation pins below remain the
original architecture evidence; this reconstruction changes no decision or
scope-review substance. `DEC-0028-001` `PART-01 Participation` is the closed
value `reviewed`.

## Sources and normalized requirements

| Source | Pin/class | Derivation |
| --- | --- | --- |
| `TODO.md` Features `0028`/`0029` | `main@d30b27ab1`; authoritative | Feature goal, current prerequisites, conditional consumer text |
| `decision-1788029989734-71b1345c` | resolved Management option A | Data appointment and decomposition authority only |
| `DEC-0020-001`, `req-0020-03`, `req-0020-04`, `req-0020-09` | authoritative decisions/products | software-only boundary; SYS.1 external/not-rated; selected-profile gate |
| `DEC-0022-001`, `0022-feature-breakdown-proposal.md` | authoritative conditional SYS interface | named authority/baseline activation; `0029-01` conditional input selection |
| `DEC-0027-001` | authoritative MAN.3 gate architecture | operative plan boundary and no implicit SYS activation |
| `req-0013-02-stakeholder-requirements-baseline.md` | evidentiary candidate | reusable source/requirement fields; explicitly unapproved and not SYS.1 credit |
| `docs/pipeline/feature-breakdown.md` | normative | record fields, A1/A2, profiles, test derivation, terminal integration floor |

- **RQ-0028-01:** activate SYS.1 only from explicit responsibility and authority.
- **RQ-0028-02:** control every stakeholder/source identity and applicability.
- **RQ-0028-03:** elicit and analyze intended use, environments, needs,
  priorities, conflicts, assumptions, changes, impacts, and risks.
- **RQ-0028-04:** agree and baseline atomic stakeholder requirements with
  acceptance, validation, status, communication, and traceability.
- **RQ-0028-05:** integrate the Feature without claiming unsupported process
  performance, rating, or downstream execution.

## Shared interfaces and prerequisite graph

`0028-04` produces `SYS1-stakeholder-baseline-interface@v1` with the exact
fields in `DEC-0028-001 CON-03`. `0028-05` pins its accepted composition and
handoff. `0029-01` consumes that interface only on the internal/shared SYS.1
path; otherwise it validates the existing external/shared interface. This is a
use-path branch, not a new unconditional TODO prerequisite.

```text
0020-09 + 0022-01 + 0027-01
              |
          0028-01  activation/input authority [checkpoint]
              |
          0028-02  stakeholder/source register
              |
          0028-03  elicitation and conflict analysis
              |
          0028-04  agreed controlled baseline/handoff [checkpoint]
              |
          0028-05  terminal Feature integration [checkpoint]
              :
              : conditional use only
          0029-01
```

## Task contracts

### `0028-01` — SYS.1 activation and input-authority baseline

```yaml
task_id: "0028-01"
feature_id: "0028"
role: implementer
architecture_decisions:
  - decision: "Fail closed until selected-profile, performer, agreement/acceptance authority, process boundary, and exact input baseline are authorized."
    derives_from:
      requirements: ["RQ-0028-01"]
      decision_records: ["DEC-0028-001", "DEC-0022-001", "DEC-0020-001"]
      existing_architecture: ["docs/dossiers/req-0020-09-execution-register.md", "docs/dossiers/req-0020-03-responsibility-authority-matrix.md"]
      repository_evidence: ["TODO.md@d30b27ab1"]
    authority_or_assumption: authority
prerequisites:
  - task_id: "0020-09"
    derives_from: "selected-profile execution authority"
  - task_id: "0022-01"
    derives_from: "typed SYS.1 responsibility/input/output interface"
  - task_id: "0027-01"
    derives_from: "operative plan authority and assigned resources"
planned_order:
  position: 1
  order: ["0028-01", "0028-02", "0028-03", "0028-04", "0028-05"]
  order_matters_because: "No SYS.1 evidence may be produced or credited before responsibility and source authority exist."
test_scope:
  derives_from: ["activation authority", "selected-profile boundary", "wrong-origin risk"]
  kind: manual_inspection
  evidence: "five negative cases (not-rated, unnamed performer, unnamed authority, stale baseline, undefined assessed-unit outcomes) and one complete positive record"
capability_profile:
  capability_class: unprivileged
  rights: ["read repository", "write exact dossier and own claim"]
  data: ["controlled repository authority records", "no external source adoption"]
  tools: ["Git", "stdlib Python"]
  execution_needs: direct
  cognitive_demand: critical
  independence: "Implementer distinct from Architect Data and checkpoint Integrator"
branch:
  parent: "0028"
  name: "0028-01"
  create: "pre-provision from current Feature branch"
```

Write scope: `docs/dossiers/req-0028-01-sys1-activation-and-input-contract.md`,
own canonical claim, own `TODO.md` bookkeeping. DoD: controlled activation and
input-authority record with exact sources, all negative dispositions, findings,
validation evidence, recovery, and REF; no external adoption or SYS.1 credit.
Demand: breadth high, depth critical, context high, ambiguity high,
verification high; estimator `0044-06`, peak `critical`; 60–120 minutes, CPU
under 2 minutes, no network/credentials, uncertainty ±40%, risk critical.

### `0028-02` — controlled stakeholder and source register

Prerequisite `0028-01`; position 2. Own
`docs/dossiers/req-0028-02-stakeholder-source-register.md`, own claim and
bookkeeping. Record customer/user/regulatory/operational/manufacturing-service/
safety/cybersecurity/supplier/internal stakeholder identities, roles, remit,
source ID/revision/originator/authority/date/confidentiality/applicability/
change history, contact/communication route, and missing-source refusal.
Acceptance requires whole-population uniqueness, no unnamed authority passing,
and exact trace to the activation record. Test kind `manual_inspection` plus a
deterministic table completeness/duplicate scan. Capability `unprivileged`,
direct Git/stdlib, cognitive `high`, distinct from Data/Integrator. DoD includes
source manifest, missing-source findings, negative fixtures, digests and REF;
no agreement or process credit. Demand dimensions: high/high/high/medium/high,
peak high; 45–90 minutes, CPU under 2 minutes, no network, uncertainty ±30%,
risk high. No checkpoint: reversible evidence register; `0028-04` rejects
unauthorized/missing inputs and `0028-05` reviews composition.

### `0028-03` — elicitation, scenario, environment, and conflict analysis

Prerequisite `0028-02`; position 3. Own
`docs/dossiers/req-0028-03-elicitation-analysis.md`, own claim and bookkeeping.
For every controlled source retain elicitation method/date/participants,
normal/abnormal/out-of-use intended-use scenarios, environments/variants,
need/constraint/priority/rationale, assumptions, duplicates, conflicts and
authority-backed resolution or explicit open disposition, changes, impacts,
risks, communication, and source trace. Acceptance forbids invented resolution
and distinguishes absence from agreement. Test kind `manual_inspection` with
coverage, orphan, conflict, and prohibited-claim scans. Capability
`unprivileged`, direct, cognitive `high`, distinct roles. DoD includes coverage
matrix, unresolved-conflict register, finding disposition and REF; no baseline
agreement or SYS.1 credit. Demand high/high/high/high/high, peak high; 60–120
minutes, CPU under 2 minutes, no network, uncertainty ±35%, risk high. No
checkpoint: reversible analysis only; cannot create the consumer baseline.

### `0028-04` — agreed stakeholder-requirements baseline and handoff

Prerequisite `0028-03`; position 4. Own
`docs/dossiers/req-0028-04-stakeholder-requirements-baseline.md`, own claim and
bookkeeping. Produce `SYS1-stakeholder-baseline-interface@v1`; every atomic
requirement has the fields from `CON-03`, exact stakeholder agreement and
acceptance authority, append-only change/supersession, conflict disposition,
coverage and bidirectional source/downstream trace. Acceptance rejects
candidate/unapproved, stale, cross-product, anonymous, unresolved-conflict, or
wrong-origin content. Test kind `integration`: deterministic whole-baseline
schema/trace/coverage/authority checks plus negative fixtures and manual
agreement-record inspection. Capability `unprivileged`, direct, cognitive
`critical`, Implementer distinct from Data and mandatory-checkpoint Integrator.
DoD: exact version/digests, current authorities, all findings resolved or
explicitly non-passing, consumer handoff, recovery and REF. Demand
high/critical/critical/high/critical, peak critical; 90–180 minutes, CPU under
5 minutes, no network/credentials, uncertainty ±45%, risk critical.

### `0028-05` — terminal integration and conditional consumer readiness

Prerequisite `0028-04`; position 5 and exactly-one terminal integrating Task.
Own `docs/dossiers/0028-feature-integration.md`, own integration claim and
bookkeeping; do not edit predecessor products except through returned findings.
Pin source/decision/product/validation digests; prove consistent vocabulary,
activation authority, stakeholder/source/scenario/conflict/requirement coverage,
change/recovery behavior, and the `0029-01` internal/shared versus external
input selection. Explicitly prove no false SYS.1 performance/rating, no external
adoption, and no broad consumer edge. Test kind `end_to_end` over the complete
candidate plus negative path selection and recovery rehearsal; retain exact
commands/results. Capability `privileged` because it crosses the mandatory
terminal checkpoint; Integrator independent of all decisive authors; cognitive
`critical`. DoD: clean pinned integration candidate, findings disposition,
recovery/handoff evidence, mandatory PASS review by separate authority, REF;
no Feature closure or Acceptance unless separately assigned. Demand
critical/critical/critical/high/critical, peak critical; 90–180 minutes, CPU
under 10 minutes, no network, uncertainty ±35%, risk critical.

## A1, A2, activation, and recovery

```yaml
target_policy_check:
  field: A1-target-policy-integrability
  verdict: fits
  checked_target: main
  basis: "main@d30b27ab1 contains DEC-0020-001/002/003, DEC-0022-001, DEC-0027-001, the conditional 0029-01 consumer, and the normative exactly-one terminal integration rule; DEC-0028-001 preserves those contracts without activating SYS.1"
  checked_at: "2026-08-29T22:50:09Z"
  recorded_by: "Architect agent:data:0028-feature-breakdown:1788043592587-75bc2401"
```

Planned order is fixed above. No actual A2 deviation exists at authoring. A
later deviation is recorded when it can block/change another unit; ordinary
delay is not a gate. Governance activates only after separate integration to
`main`; implementation then still waits for prerequisites and `0028-01`
authority. Self-application is prospective with no bootstrap exemption or
implicit grandfathering. Recovery follows `DEC-0028-001 CON-06`.
