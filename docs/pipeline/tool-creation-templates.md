# Reusable Tool Process Templates

Use these English templates verbatim or record controlled tailoring with owner, rationale, expiry, compensating control, and approving authority.

## A. Discovery and decision record

```markdown
- Proposal ID: `TCP-<NNN>`
- Need and baseline: `<repeated friction, defect, cost, or recovery evidence>`
- Semantic signature: `<intent, schemas, effects, scope, authority, determinism, recovery>`
- Discovery searched: `<catalog/actions/code/tests/proposals/third parties>`
- Near matches: `<reuse|configure|extend|consolidate|unsuitable, reason>`
- Decision: `<reuse|extend|consolidate|create|acquire|manual|reject>`
- Productization signal: `<observed recurrence/risk/stability; not an automatic threshold>`
- Authority and evidence: `<identity, record, immutable locator>`
```

## B. Candidate and action contract

```markdown
- Tool/action ID and version/digest: `<identity>`
- Semantic owner and support route: `<one accountable owner>`
- Purpose and non-goals: `<bounded meaning>`
- Profile and lifecycle: `<candidate|qualified-for-profile|registered|...>`
- Inputs/configuration: `<typed schema, defaults, precedence, bounds>`
- Outputs/statuses: `<artifacts/findings; PASS|FAIL|SKIP|INCONCLUSIVE|...>`
- Modes: `<check, dry-run, JSON, separately authorized apply>`
- Scope: `<exact reads/writes; trusted derived expansion; temporary/external>`
- Effects/recovery: `<class, idempotency key, journal, retry/reconcile>`
- Execution/security: `<typed action, resources, concurrency, network/credential/privacy limits>`
- Evidence/compatibility: `<result schema, retention, consumers, change/requalification, retirement>`
```

## C. Qualification and independent review

```markdown
- Exact candidate/configuration/environment digests: `<identities>`
- Required tests: `<unit, hermetic, hostile, concurrency, failure injection, canary>`
- Expected effects and recovery: `<preimage, commit points, rollback/reconciliation>`
- Findings and residual limits: `<severity, disposition, owner>`
- Reviewer independence and authority: `<assignment and conflict check>`
- Decision: `<qualify stated profile|revise|reject|suspend>`
- Deployment/registration decision: `<separate explicit authority or rejection>`
```

## D. Pilot and improvement record

| Field | Required content |
|---|---|
| Pilot shape | `new-capability` or `extension-or-consolidation` |
| Matched baseline | Work unit, input snapshot, oracle, method order, exclusions |
| Measures | Safety, first-attempt success, duration, retries, context, maintenance, evidence volume; each with denominator/source/bias |
| Result | Observed values and retained failures; no automation-count claim |
| Decision | Retain, revise, consolidate, suspend, deprecate, retire, or reject |
| Follow-up | Semantic owner, compatibility/migration, requalification, authority, expiry |

## E. Retirement and emergency record

A retirement record names successor/manual fallback, consumers, registry/action/configuration/credential revocation, retained evidence, historical-result interpretation, and completion verification. An emergency record additionally names incident trigger, exact digest/action, one-use scope, specialist authorities, compensating controls, expiry, reconciliation, and re-entry/requalification; it never grants generic execution.
