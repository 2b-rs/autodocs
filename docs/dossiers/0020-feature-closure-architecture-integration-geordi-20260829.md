# Integration evidence — Feature 0020 closure architecture

## Verdict and boundary

- **Verdict:** `PASS / integrable`, conditional on fresh exact-candidate hygiene,
  unchanged target equality, immediate hard root preflight, authorized root
  merge, and immediate post-merge root preflight.
- **Integrator:** `geordi`, privileged Team Enterprise Integrator.
- **Authority:** atomic award `1788030928537-0b6ec4c2`.
- **Baseline:** `main@dcaf1757ff1fc5828fec6fb2e02e019d49502aec`.
- **Source candidate:** `7fb1d110d80531563ac423817d62201b83aa48a1`.
- **Corrected substantive pin:**
  `a795e5fea4ec4735932c4dc80457352b34f76c5e`.
- **Reconciliation merge:** `e87294a1fed2aafafca726db57e2ddaf07f29e9e`.

This is an integration-boundary verdict for the governance candidate. It is not
implementation or Acceptance of `0020-10`, checkpoint crossing, Feature closure,
ECU execution evidence, a capability rating, release approval, or residual-risk
acceptance.

## Pin correction and provenance

The award initially cited non-object SHA
`a795e5fea44e0f1b16bb20d8fe3b998d41babbb2`. Claim commit `08a21b629` stopped
before candidate mutation. Project Lead correction
`agent-inbox:1788031351413-707e424b` voided that transcription only and assignment
resume `agent-inbox:1788031356505-da217701` retained the same six-path scope.
The corrected commit resolves exactly once in the candidate ancestry, has subject
`arch(0020): define terminal integration floor`, and changes the four awarded
source paths. The original stop evidence remains append-only.

The candidate was merged with explicit provenance into the exact current-main
branch. The merge had no conflict. Three source-document blobs are byte-identical
to the source candidate; `TODO.md` retains current-main drift and adds only the
exact `0020-10` block. The baseline-to-candidate scope is exactly:

1. `TODO.md`
2. `TODO-data-0020-closure-architecture-20260829.md`
3. `docs/dossiers/dec-0020-003-feature-integration-floor.md`
4. `docs/dossiers/0020-feature-closure-architecture-review.md`
5. `TODO-geordi-0020-closure-architecture-integration-20260829.md`
6. `docs/dossiers/0020-feature-closure-architecture-integration-geordi-20260829.md`

## Independent inspection

`DEC-0020-003` is a conforming append-only decision for the cross-item closure
floor. The supporting scope review is authored by management-instantiated
Architect `data`, distinct from this Integrator, and records
`scope-ok-with-conditions`. Its eight conditions preserve child products,
evidence-origin boundaries, selected-profile responsibilities, downstream edges,
separation, recovery, and the distinction between green aggregation and
Acceptance/Feature closure.

The reconciled Feature block contains ten unique Tasks (`0020-01` through
`0020-10`), exactly nine unique incoming prerequisite edges from `0020-01`
through `0020-09` to `0020-10`, and exactly one mandatory checkpoint. No byte of
the existing `0020-01` through `0020-09` contracts changes. The new Task is open,
has an unprivileged Implementer profile, and explicitly forbids child repair,
Acceptance, checkpoint crossing, Feature closure, ratings, release claims, and
changes to selected-profile responsibility.

## Validation evidence

- `git diff --check <baseline>..HEAD`: exit `0`.
- `python3 _src/tools/process_doc_doctor.py --root . --json`: exit `0`,
  `ok=true`, 34 findings, and no `0020` finding.
- `python3 _src/tools/legacy_task_doctor.py --root . --json`: diagnostic exit
  `1` with the repository's existing global findings; no finding targets
  `0020-10`. The only candidate-local findings are the known immutable owner-token
  grammar mismatch in Data's non-backlog architecture claim and the equivalent
  non-backlog item component in this exact-award integration claim. No product,
  decision, review, graph, or Task-contract finding is present.
- Focused graph check: ten unique Task IDs, nine unique prerequisite endpoints,
  one mandatory checkpoint.
- `git diff --cached --check` before the provenance merge: exit `0`; merge had
  no unmerged paths and staged exactly the four source paths.

No reviewed source was repaired. The only Integrator-authored correction was to
this Integrator's own claim metadata so the legacy diagnostic recognizes its
capability, execution authority, startup review, and next step.

## Recovery and final gate

Before root integration, abandon this branch to omit the candidate without
touching any completed child product. After integration, a change to the closure
floor requires a new append-only decision and independently reviewed backlog
correction; do not rewrite `DEC-0020-003` or this evidence.

The final candidate must pass repository-wide candidate hygiene. Immediately
before the root merge, `main` must still equal the pinned baseline and the hard
root preflight must pass. The root merge must use the authorized repository
merge operation, followed immediately by the same hard root preflight. Any
nonzero, indeterminate, drift, conflict, or scope result changes this verdict to
blocked and stops integration.

## Realized root integration — final evidence

The conditional gates above were executed against exact candidate
`bd92b0188b9ddac3e557e9edd596a2ad7fad7328` and pinned baseline
`dcaf1757ff1fc5828fec6fb2e02e019d49502aec`:

- Candidate hygiene command:
  `python3 _src/tools/check_integration_hygiene.py --repo /Users/tobias.anton/devel/autodocs/.worktrees/integrate-0020-closure-architecture-geordi-20260829 --candidate-ref bd92b0188b9ddac3e557e9edd596a2ad7fad7328`
  — exit `0`, `integration hygiene: PASS`, 79 registered worktrees.
- Immediate root preflight command:
  `python3 _src/tools/check_integration_hygiene.py --repo /Users/tobias.anton/devel/autodocs --root-preflight`
  — exit `0`, `integration hygiene: PASS`, 79 registered worktrees.
- Equality and cleanliness gates immediately before merge: root `HEAD` equaled
  `dcaf1757ff1fc5828fec6fb2e02e019d49502aec`; root tracked status and candidate
  status were empty; the baseline-to-candidate delta contained exactly six paths.
- Authorized root command:
  `git -C /Users/tobias.anton/devel/autodocs merge --ff-only bd92b0188b9ddac3e557e9edd596a2ad7fad7328`
  — exit `0`; root advanced from `dcaf1757ff1f` to `bd92b0188b`.
- Immediate post-merge root preflight: the same root-preflight command exited
  `0`, reported `integration hygiene: PASS` across 79 worktrees, and final
  `main` was `bd92b0188b9ddac3e557e9edd596a2ad7fad7328`.

**Final verdict:** `PASS / integrated`. No Task Acceptance, `0020-10`
implementation, checkpoint crossing, Feature closure, child-product mutation,
selected-profile change, ECU evidence/rating/release claim, or successor action
occurred. Rework award `1788032193461-7874178a` adds this realized evidence and
terminal claim state without altering the four reviewed source paths.
