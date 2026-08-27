# 0038-33 — Architect review of the AUTO010 aggregate-control scope

**Reviewer:** `Harry-Seven-20260822T153500Z`, Architect, privileged  
**Dispatcher:** `Harry`  
**Implementer:** `Harry-Bashir-20260822T152700Z`  
**Review kind:** independent pre-mutation cross-item gate-scope review, not Task acceptance  
**Baseline:** `main` at `77c4d0aee730909ba1e1284144772595ada7722d`  
**Decision-record state:** `DEC-0038-002` allocated by `kathryn` on `main`
`418f09b79` at the exact path
`docs/dossiers/dec-0038-automation-safety-aggregate-control.md`; Dispatcher
`Harry` explicitly expanded this review's write scope to that path. The
conforming record carries forward this review's exact closed-set verdict.

**Main-drift recheck:** after the initial review commit, current `main`
`9226adfdf` was merged into the review branch as `b549b5acf`. The intervening
accepted `0038-30` integration changed `TODO.md` and its own LHM035/tooling
scope only. `_src/tests/test_automation_safety.py` remained object
`ad7c9a4cedd5abd69b064175388067084c8a12a7`; `_src/tools/runner_transaction.py`
remained object `f3363db43add9a8dc8937def065a853d70daac3e`. No reviewed AUTO010 identity,
authority rule, or `0038-33` contract changed, so the verdict remains current.

## Verdict

`cross-item-blast-radius` **applies**. The failing aggregate control is shared validation behavior: its declared full-suite assertion can block validation and integration evidence for work units other than `0038-33`. Narrowing it is therefore a qualifying gate-scope mutation and remains prohibited until both this independent Architect review and a conforming `decision-record@v1` exist.

The evidence supports **stale aggregate control, not a regression in the five examined runtime operations**. I support one narrow resolution: keep `AUTO010` forbidden for `_src/tools/runner_transaction.py` generally, but encode an exact closed allow-set for the five reviewed finding identities and fail on every additional or changed `AUTO010`. This is support for scope only. It is not acceptance, an integration verdict, or permission to mutate before the decision record exists.

The provisional `Integration review: mandatory` marker on `0038-33` should be **confirmed**. The Task changes a shared safety regression control; a false relaxation could make a future destructive operation invisible to the only path-wide regression assertion. This checkpoint conclusion is distinct from the present scope review and grants no `Acceptance: ✓`.

## Canonical trigger and affected reach

The canonical predicate asks whether actual declared gate behavior can block another work unit's start, validation, acceptance, integration, publication, or closure, or alter that unit's contract. It does here:

- `_src/tests/test_automation_safety.py::AutomationSafetyFixtureTests.test_current_safe_aggregate_controls_do_not_regress` is a repository-wide regression assertion, not a Task-local check.
- `docs/pipeline/automation-safety.md` declares the focused full suite as the validation command and describes the checker as a project-validation gate.
- Existing integration reports already treat the single aggregate failure as validation evidence and explicitly disposition it as pre-existing (`docs/pipeline/approvals/0038-main-integration-20260821T000000Z.md`; `docs/pipeline/approvals/0040-feature-main-integration-review-worf-martok-20260820T121500Z.md`).

Affected work units and gates, no broader:

1. `task:0038-33`, whose product is the correction and rationale.
2. `feature:0038`, because the aggregate control belongs to its automation-safety product and the Feature integration consumes that validation.
3. `repository:autodocs` work units whose declared validation or checkpoint evidence runs the full `_src.tests.test_automation_safety` suite. The changed assertion can block those validations even when their implementation is unrelated.
4. Gate: the single aggregate regression assertion in `_src/tests/test_automation_safety.py`; target inspected by that assertion: `_src/tools/runner_transaction.py`.

Not affected and not authorized for change: the live scanner algorithm, `AUTO010` semantics/severity, `_src/validate.py` wiring, policy/dispositions, runtime transaction behavior, other files in the aggregate control, other AUTO rules, publication authority, acceptance rules, or any external system.

## Independent historical evidence

The control and each finding were reproduced with current scanner code against historical file bytes:

| Revision | Timestamp | Relevant state under current scanner |
|---|---|---|
| `ec251f2a69b18e9d90f3cac53bedfa7fa248e338` | 2026-08-17 06:12 +02:00 | aggregate control introduced; `runner_transaction.py` has **0** `AUTO010` |
| `2e688ab6c056b1e990f0c433e606601cace8966c` | 2026-08-17 16:11 +02:00 | stale-lock cleanup appears; **1** finding |
| `4231f93b24cbd9aa056305ffa5a147ac316c783c` | 2026-08-19 08:28 +02:00 | immutable create and recovery lease added; **3** findings |
| `2d510d08ed0cc86964cec4a9be99fe719edffadf` | 2026-08-20 20:21 +02:00 | branch worktree synchronization added; **4** findings on that line |
| `b70238ad0ea186fcf4c28579515b4ec695f048f1` | 2026-08-20 21:07 +02:00 | editor-candidate materialization added; branch topology at this revision yields **4** findings |
| `77c4d0aee730909ba1e1284144772595ada7722d` | review baseline | merged history carries the five identities below |

Thus the control predates every finding; it was green when authored and was not updated as later transaction features intentionally introduced the operations.

Current exact findings independently measured:

| Line | Symbol | Evidence SHA-256 | Semantics |
|---:|---|---|---|
| 240 | `_atomic_create` | `a9585e4f1caf3113aa8a1da53260983471d1e10d5339b4a553f0fcce7a047ea2` | `finally` cleanup of an unpredictable, mode-0600 temporary name after immutable hard-link publication or failure; the target file/result is the durable product |
| 1698 | `Transaction.acquire_lock` | `bbeb1bc976b167dc0d4939d3788858124cb8cfecdc064b4c6bac40cc1f290fd8` | deletion only after the recorded PID/start-time holder is proven dead, immediately followed by exclusive lock recreation; live/unreadable holders fail closed |
| 1839 | `Transaction.materialize_editor_candidate` | `2027934680f43f964b21625c17ce86672422e5584efeaa904d49a4d17baa8d3c` | deletion inside a detached candidate after candidate verification and `materializing-editor-candidate` journal state; authoritative promotion uses the existing backup/rollback/journal machinery |
| 3295 | `BranchMergeTransaction._synchronize_worktree` | `2027934680f43f964b21625c17ce86672422e5584efeaa904d49a4d17baa8d3c` | materializes the already CAS-published commit into declared worktree paths; the commit is the durable desired state and the transaction journals `worktree-synchronized` after deterministic synchronization |
| 3922 | `_recovery_lease` | `d9bae0d944b115d54df1aa8eb1b10f982d72c3427965fb54b216068970284802` | ephemeral lease cleanup only when on-disk bytes still exactly equal this holder's payload; the recovery journal is the durable state |

The shared evidence hash for the two `destination.unlink()` calls proves why hash alone is insufficient: symbol and line are required to distinguish the two reviewed operations.

Semantic corroboration is not merely a green test. The code and focused tests establish the relevant invariants: stale lock replacement rejects live holders; immutable result failure retains journal/claim state; editor failure injection proves untouched pre-materialization state and rollback during/after promotion; post-publication recovery retains the claim; branch synchronization derives bytes/absence from the published commit. `docs/pipeline/runner-transaction.md` explicitly assigns editor materialization to the existing promote/rollback/journal machinery.

## Minimum authorized scope

After a conforming decision record exists, the Implementer may change only the aggregate test and its directly necessary test explanation/regression coverage so that:

1. `AUTO001`, `AUTO002`, and `AUTO009` remain unconditionally forbidden for `_src/tools/runner_transaction.py`.
2. `AUTO010` remains forbidden except for a closed set containing exactly the five tuples above. The binding must include at least `line`, `symbol`, and full `evidence_sha256`; path and rule are implicit in the inspected collection but may be included.
3. The test asserts equality of the observed permitted set, not a subset. A sixth finding, a changed evidence span, a moved line, or a changed symbol must fail and force re-review.
4. The rationale is adjacent and points to the Decision record plus this scope review. A blanket removal of `AUTO010` from the forbidden set is not conforming.
5. Existing controls for every other path/rule remain byte-for-byte or behaviorally unchanged, and the full suite plus focused aggregate test are run with real counts.

This deliberately creates maintenance friction on line movement. That is the smallest enforceable boundary matching Task `0038-33`'s requirement that the correction not silently widen beyond the five examined findings.

## Explicitly forbidden resolutions

- Removing `AUTO010` wholesale from `runner_transaction.py`'s forbidden rules.
- File-, directory-, glob-, symbol-prefix-, or severity-wide exemption.
- Adding a policy disposition merely to turn the suite green.
- Changing `automation_safety.py`, `AUTO010` detection/severity, or live-scan exit behavior as part of this Task.
- Changing any of the five runtime operations merely to appease the syntactic aggregate test without preserving their established transaction guarantees.
- Treating a passing suite as authority evidence, acceptance, or proof that the chosen scope is correct.
- Allowing future findings based only on the same evidence hash; the two current equal hashes already demonstrate the collision at operation-text level.

## Validation performed for this review

- Pre-mutation integration hygiene: PASS, 111 registered worktrees.
- Focused current aggregate control: **1 test, 1 failure**, exact message `_src/tools/runner_transaction.py: ['AUTO010']`.
- Current scanner extraction: exactly **5** `AUTO010` findings with the identities recorded above.
- Historical rescans under the current scanner: `0 → 1 → 3 → 4/4 → 5` along the relevant revisions/merged baseline, matching branch topology and proving all findings postdate the control.
- `git blame` independently assigns each operation to the commits/timestamps recorded above.
- Relevant code, focused transaction tests, Safety documentation, integration reports, authority rules, and decision-record contract inspected.

## Mutation status

**Blocked pending governance integration.** This review supplies the required
independent Architect support and `DEC-0038-002` supplies the conforming
decision record on the review branch. Because governance must be current on
`main`, Bashir must not mutate the qualifying gate until Kathryn integrates the
record there. The review branch itself grants no implementation authority.

The complete dispatch briefing and the context boundary are preserved verbatim in `TODO-Harry-Seven-0038-33-scope-20260822T153500Z.md`; that record is part of this review evidence.
