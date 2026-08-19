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

## C. Decision, exception, and change record

```markdown
- ID: `<stable ID>`
- Time: `<ISO-8601 with timezone>`
- Deciding authority: `<identity and role>`
- Subject and affected IDs: `<scope>`
- Alternatives and technical rationale: `<evidence-backed comparison>`
- Consequences: `<criteria, scopes, dependencies, risks, baselines>`
- Tailoring/exception: `<control, expiry, compensating control>`
- Evidence: `<immutable locator>`
```

## D. Parent-package closure checklist

- [ ] All children have an implementation/disposition state; no marker is treated as acceptance.
- [ ] Cross-child contracts, scopes, criteria, and evidence are reconciled.
- [ ] Integrated and negative/recovery validation is recorded.
- [ ] Residual findings, risks, exceptions, and supersessions are dispositioned.
- [ ] Planned-versus-actual scope, dependency, resource, and evidence deltas feed learning.
