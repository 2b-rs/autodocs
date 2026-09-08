# `0050-07` — Independent QA verification of the Feature 0050 matrix

**Verdict: `blocking-findings-open`.** Everything that is implemented passes, and passes
convincingly. But three of the seven matrix dimensions this task is required to verify
have **no observable coverage** in the candidates. Per `0050-07`'s own acceptance
criteria — *"critical/major findings remain blocking and are not converted to Management
questions"* — those are reported as blocking, not softened.

| Field | Value |
|---|---|
| QA agent | `seven` (Team Voyager) |
| Authority | atomic AWARD on offer `1788295513369-b11d75d3` |
| Candidate repository | **`agent-inbox`** (the 0050 implementation lives there, not in autodocs) |
| Candidate repo `main` | `91f59a6` |
| Evidence repository | `autodocs`, branch `0050-07`, from `main@bbe42ad702` |

## Disclosure

I authored the `0050-00` distinct-Architect scope review (`9b6fcf2b70`) and raised finding
S-01 against `0050-02`'s missing checkpoint attribute. I implemented none of
`0050-01`…`0050-06`, so this QA verifies other agents' candidates, not my own work, and
S-01 was routed to the integrator rather than to me. Scope-reviewer and QA on one Feature
is still close enough that the coordinator was told at accept time and can reassign.

## Exact candidates pinned

All six are ancestors of `agent-inbox@91f59a6`, verified individually:

| Item | Pin |
|---|---|
| `0050-01` | `793137ad5` |
| `0050-02` | `d6bf9e213` |
| `0050-03` | `04a08ea5b` |
| `0050-04` | `8ef6f0a66` |
| `0050-05` | `0fe7b5e25` |
| `0050-06` | `91f59a6fc` |

## Executed result

`python3 -m pytest test_team_pause_phaseout.py -q` → **exit 0, 18 passed**. Exit status
checked, not inferred from output text.

## Matrix coverage — the substance of this QA

`0050-07` requires verification of the *"all-team, mixed-provider race, deadline, recovery,
privacy and abuse matrix"*, with test scope naming *"negative authorization/privacy cases"*.
Mapping each required dimension onto observed tests:

| Dimension | Coverage | Evidence |
|---|---|---|
| all-team | **covered** | `test_mixed_team_offer_delivery_and_selective_pause`, `test_team_admission_guard` |
| race | **covered** | `test_pause_versus_accept_serialization_and_rejection`, `test_stale_generation_on_accept_fails_closed` |
| deadline | **covered** | `test_supervisor_drain_escalation_lifecycle_integration`, `test_reclamation_extend_bounded_and_limits` |
| recovery | **covered** | `test_resume_and_additive_rollback_never_resurrects_cancelled_ownership`, `test_team_resume_advances_generation_and_restores_active` |
| **mixed-provider** | **none found** | 0 occurrences of `provider` in the 0050 test file |
| **privacy** | **none found** | 0 occurrences of `privacy`, `redact`, `retention`, `anonym` |
| **abuse** | **none found** | 0 occurrences of `abuse`, `quota` |

### Finding Q-01 (major, blocking) — `mixed-provider` is unverified

`provider` appears in the candidate repository only in a module docstring and the
`exhausted` quota-status enum. It is not exercised as a pause/drain dimension anywhere in
the 0050 suite. The Feature's own direction explicitly anticipates it — *"den Agenten
können auch im phase-out die Tokens ausgehen"* — so an agent exhausting quota mid-drain is
a named product scenario, not a hypothetical.

### Finding Q-02 (major, blocking) — privacy / negative-authorization cases are unverified

The task's test scope requires *"negative authorization/privacy cases"*. None are present
in the 0050 suite.

### Finding Q-03 (major, blocking) — abuse/quota matrix is unverified

No abuse or quota-boundary cases in the 0050 suite.

**What these findings are not.** They are not claims that the implementation is wrong.
Every implemented path passes, and the 18 tests are well-targeted — the race, deadline,
zero-proof and rollback cases in particular are exactly the hard ones. The finding is that
three required dimensions have no evidence, and QA cannot certify a matrix it cannot
observe.

## Measurement corrections (recorded because they nearly became false findings)

1. **Full-suite run aborted at my own 2-minute limit** (exit 143 = SIGTERM). That is my
   timeout, not a test failure. I did not report it as one; I re-ran the targeted file
   with a longer bound and checked the exit status.
2. **`grep -oE '^def test_'` returned nothing** while pytest collected 18 tests — the tests
   are methods, not module-level functions, so the `^` anchor missed all of them. Had I
   trusted it I would have reported "no tests exist."
3. **A dimension keyword scan returned an identical hit count for every term**, which is a
   malformed command rather than a result. Discarded; the coverage table above is built
   from actual test names, which is why it distinguishes
   `test_pause_versus_accept_serialization_and_rejection` as race coverage even though the
   word "race" never appears in it.

The three uncovered dimensions survived all of that: they are absent by name *and* absent
by concept, checked separately.

## What this QA does not do

Not Task Acceptance, not an integration verdict, not approval. `0050-07` is an evidence-only
node whose report is a hard prerequisite of terminal `0050-08`; findings Q-01…Q-03 are
raised for the owning implementers and the coordinator, and I neither cleared nor waived
them. I did not modify any candidate.

## Provenance

No user-authored prompt. Process-triggered by atomic AWARD on offer `1788295513369-b11d75d3`,
delivered 2026-09-01T20:45Z. Candidates measured in `agent-inbox@91f59a6`; report written in
`autodocs` branch `0050-07` from `main@bbe42ad702`. Authored 2026-09-01 (UTC).
