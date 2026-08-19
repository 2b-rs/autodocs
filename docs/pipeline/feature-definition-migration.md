# Feature Definition Process Migration Plan

## 1. Controlled adoption

1. Keep the current legacy authority unchanged while the candidate process is piloted and independently reviewed.
2. Baseline the approved process version, templates, validator digest, pilot findings, tailoring rules, and responsible roles in one decision record.
3. Apply it only to newly selected Features first. Active work is not retrofitted merely to satisfy a template.
4. For an active Feature, add an additive contract/coverage record only when an owner verifies that it does not alter marker, claim, prerequisite, acceptance, or scope semantics. Record unknown historical fields rather than inventing them.
5. Measure pilot results; authorize wider adoption, revision, or withdrawal explicitly.

## 2. Authority mapping

| Concern | Before authorized `0037` cutover | After authorized cutover |
|---|---|---|
| Feature/Task contract | `TODO.md` plus committed supporting records | canonical `issues/<feature>/index.md` and item records |
| Claim | `TODO-<agent-id>.md` | item-local `claim.json` |
| Closure/evidence | backlog records and referenced immutable evidence | `closure.json`, typed provenance and artifact sets |
| Generated views | non-authoritative | non-authoritative |

No migration may maintain both representations as competing sources. The authorized `0037` cutover defines the one atomic authority switch; this process consumes that decision and does not implement it.

## 3. Preservation and recovery

Migration preserves original task text, state history, claims, REFs, acceptance records, decision records, and evidence locators. It creates append-only derivation/crosswalk records instead of rewriting history. A failed conversion leaves the legacy authority untouched, retains a bounded failure report, and resumes only from a verified source digest. A conversion cannot create acceptance, close a Feature, assign a role, or approve a product/risk decision.

## 4. Adoption exit criteria

Independent review confirms two materially different pilots, complete outcome-to-Task-to-evidence coverage, executable bounded Tasks, graph and semantic-deadlock analysis, explicit authority interfaces, and findings disposition. The authority then decides adopt, revise, or reject; absent that record this remains a candidate process.