# Feature Definition and Breakdown Templates

Use these English templates verbatim in a new contract or record a controlled tailoring under the process.

## A. Feature contract

```markdown
# Feature `<id>` contract v`<n>`
- Intake source: `<immutable locator>`
- Authority epoch: `legacy|post-0037-cutover`, baseline `<commit or immutable record>`
- Outcome: `<observable stakeholder/system result>`
- Non-goals: `<explicit exclusions>`
- Requirements impact: `<requirement ID: new|changed|clarified|withdrawn|unaffected, owner, verification>`
- Architecture boundary: `<inherited constraint|open decision ID|no impact with rationale>`
- Scope: direct `<canonical paths/state>`; derived `<producer/output relation>`; external `<effect/authority>`; excluded `<nearby state>`
- Risks: `<ID, cause, impact, control, owner, residual authority>`
- Closure: `<integration Task, Feature gates, parent-package work>`

## Acceptance criteria
- `FD-<feature>-AC-001` — outcome: `<observable condition>`; verification: `<method>`; evidence: `<class>`; failure: `<meaning>`; implemented-by: `<Task IDs>`; verified-by: `<Task/evidence ID>`
```

## B. Task/Subtask card

| Field | Required content |
|---|---|
| Primary result | One observable deliverable, decision package, integration, or verification result |
| Inputs and baseline | Exact consumed IDs/records and freshness rule |
| Scope | Direct writes, derived producer/output, external and integration surfaces, exclusions |
| Prerequisites | `consumer:producer` edges with type and consumed result |
| Capability | Executor class, typed action/environment, resource bounds, retry/recovery |
| Verification | Positive, negative/recovery method and immutable evidence output |
| Authority | Delegated choice, required decision record, review/checkpoint rationale |
| Coverage | Implemented and verified `FD-*` criteria |
| Parent closure | Parent integration contribution or `not applicable` rationale |
| Cognitive demand | All five dimension ratings from [`feature-breakdown.md`](feature-breakdown.md) §8 — scope breadth, reasoning depth, context volume, ambiguity, verification hardness — plus evidence and estimator version. Missing evidence is `unknown`, never `low`; the highest dimension sets the class |
| Baseline pin | The exact commit each measured claim was taken against, **and** whether that baseline carried current Task Acceptance at measurement time |
| Check semantics | For every check this Task introduces or relies on: its **direction** (what it structurally cannot find), **reach** (what may not be inferred from a pass), and **effect** (observes or mutates) |

**This card renders [`feature-breakdown.md`](feature-breakdown.md) §2 and §8; it does not
redefine them.** Where the two ever disagree, that document governs and this table is the
defect.

## C. Decision records — use `decision-record@v1`, not a template here

**This section previously carried an eight-field decision-record format. It is removed, and
nothing is salvaged from it.**

A decision whose reach meets the canonical `cross-item-blast-radius` predicate is recorded as a
conforming [`decision-record@v1`](decision-record.md) — twelve fields, including `Triggers`,
`Review participation`, and `Waiver`, with closed grammars for identity, role, work-unit and
gate references. The removed format had none of those and duplicated only what `@v1` already
covers.

**Why removal rather than repair.** A second decision-record shape published inside a process
document Architects are told to follow is a competing answer to "what is a decision record",
and a partial salvage is precisely how a competing format survives. The reach question this
prevents is the one `docs/dossiers/0044-04-gate-scope-review.md` names — *"damit nicht dritte
Mechanik entsteht"*.

**Date order, stated because it decides the case.** The removed format predates
`decision-record@v1` becoming normative on `main`. Its author was not wrong to write it; the
baseline moved underneath it. That is a material-baseline change, not a quality finding
against the prior work.

For a **tailoring or exception**, record the control, its owner, rationale, expiry, and the
compensating control inside the `@v1` record's `Waiver` block. For an escalation, see the open
requirement in [`feature-definition-and-breakdown.md`](feature-definition-and-breakdown.md)
§7a.5: no conforming escalation-record shape exists yet, so an escalation is adjudicated with
quoted evidence per case and never reported as a parser result.

## D. Parent-package closure checklist

- [ ] All children have an implementation/disposition state; no marker is treated as acceptance.
- [ ] Cross-child contracts, scopes, criteria, and evidence are reconciled.
- [ ] Integrated and negative/recovery validation is recorded.
- [ ] Residual findings, risks, exceptions, and supersessions are dispositioned.
- [ ] Planned-versus-actual scope, dependency, resource, and evidence deltas feed learning.
