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

| Decision records | ad hoc records in dossiers | conforming [`decision-record@v1`](decision-record.md), twelve fields, closed grammars |
| Breakdown instruction | described in this package | owned by [`feature-breakdown.md`](feature-breakdown.md); cited, never restated |
| Where governance lives | wherever the item branch put it | **`main` only** (`DEC-0044-012`); a governance artifact never sits on a branch while others work against `main` |
| Where mutation happens | any checkout | item-owned worktree only; the root checkout is never written to (`DEC-0044-015`) |
| Implementation check-in | two commits, implementation `REF` | one atomic carrying commit with `Task-ID`/`Base-Ref` (`DEC-0041-006`) — **non-operative until its own cutover**; the two-commit rule remains authoritative until then |

**This table was rewritten on 2026-08-26.** Its 2026-08-19 form predated every row below the
first four: `decision-record@v1`, `feature-breakdown.md`, `DEC-0044-012`, `DEC-0044-015`, and
`DEC-0041-006` all became normative afterwards. A migration plan whose authority mapping is
stale is worse than none, because it migrates work onto a contract that no longer exists.

No migration may maintain both representations as competing sources. The authorized `0037` cutover defines the one atomic authority switch; this process consumes that decision and does not implement it.

## 3. Preservation and recovery

Migration preserves original task text, state history, claims, REFs, acceptance records, decision records, and evidence locators. It creates append-only derivation/crosswalk records instead of rewriting history. A failed conversion leaves the legacy authority untouched, retains a bounded failure report, and resumes only from a verified source digest. A conversion cannot create acceptance, close a Feature, assign a role, or approve a product/risk decision.

**Reaching `main` is part of preservation, not a later step.** This Task's own history is the
worked example: the prior `0039-01` line produced a complete three-round review chain ending in
an independent Acceptance, plus two pilots and a study reconciliation — and **none of it ever
reached `main`**. Measured from `main`, the Task and its prerequisite both read as unaccepted;
measured from the branch, both read as accepted. Two answers depending on where the reader
looks, which is precisely the condition `DEC-0044-012` exists to prevent, here reproduced with
acceptance records rather than governance text.

A migration therefore treats an artifact as preserved only when it is **reachable from `main`**.
Producing it, reviewing it, and even accepting it on a branch preserves nothing that another
agent can coordinate against; it only creates a second, invisible truth.

## 4. Adoption exit criteria

**Pilots are assessed against the contract in force at assessment time, and the assessment
records that contract's exact commit and acceptance state.** A pilot inherited from an earlier
contract version is evidence about that version, not this one — a contract may have been
extended since, and a strict prefix relationship does not make old evidence cover new criteria.

Independent review confirms two materially different pilots, complete outcome-to-Task-to-evidence coverage, executable bounded Tasks, graph and semantic-deadlock analysis, explicit authority interfaces, and findings disposition. The authority then decides adopt, revise, or reject; absent that record this remains a candidate process.