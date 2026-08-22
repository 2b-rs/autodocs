# Worked breakdown: Feature 0043

**Application date:** 2026-08-22 (Europe/Berlin)

**Breakdown owner:** Architect role, implemented by
`agent:data-ada-20260822t150413z:0044-04:20260822T150413Z`

**Instruction:** [`docs/pipeline/feature-breakdown.md`](../../pipeline/feature-breakdown.md)

**Feature contract:** `TODO.md` Feature 0043, current baseline `418f09b79`
**Evidence purpose:** real application of the source, dependency, test,
capability, branch, A1 and A2 record shape; not an acceptance or integration
review.

## Source and architecture derivation

| Decision/input | Evidence | Derived result |
| --- | --- | --- |
| Feature goal and requirements | `docs/dossiers/re-intake-berichtswesen-build-evidenz.md`, `RQ-SRC-03`, `RQ-BR-01`…`RQ-BR-07` | Correlate runs, retain an append-only ledger, render history, detect staleness, explain report evidence |
| Policy/record boundary | `DEC-0043-001`, current `TODO.md` acceptance/DoD | Ledger is tracked and append-only; raw logs remain git-ignored; no report claim overstates capability |
| Existing architecture | `_src/tools/build_report.py`, `_src/tools/build_ledger.py`, report page generators, `docs/pipeline/build-ledger.md` | Producer/ledger/rendering contracts and the required consumer order |
| Repository evidence | Completed `0043-01`, `0043-02`, `0043-03`, `0043-05`, and now `0043-06`; current `[u]` `0043-04`; open/unclaimed `0043-07`; branches and claims inspected at baseline and corrective check | Existing work is reused; unavailable/terminal work is not presented as a fresh pilot |

Architecture decisions are therefore: preserve the hardened combine behavior;
make the ledger the source for history rendering; derive staleness from cohort
and ledger freshness; route each report through its generator; and reserve
end-to-end composition for integrating Task `0043-07`.

## Marker and ownership check

At baseline `418f09b79`, the authoritative `TODO.md` records `0044-04` as
`[p]` with the Data-Ada takeover reference, `0043-04` as `[u]`, and `0043-05`
as `[x]`. The earlier marker divergence described by A-13 is therefore not
present in this baseline. `0043-06` and `0043-07` are open and unclaimed; no
foreign claim was touched. This check is retained as evidence, not as
permission to alter another Task's marker.

### Corrective current-state check

At the corrective check (`main` `3d8467b097120302d80f5ffccfae06c1e3dd095a`),
`0043-06` is terminal on its existing branch
(`ace9066ddf737502ed7702b0974365503adb93a8`) and its implementation claim
contains no A1 field. This is a missed prospective pilot, not a branch-time
failure that can be repaired by this Task; the state is retained as a
retrospective finding only. `0043-07` has no branch, worktree, or claim and
remains `[ ]`/unclaimed. The conforming record below is consequently recorded
before any `0043-07` branch creation. This Task neither claims, starts, nor
integrates `0043-07`.

## Dependency derivation and planned order

| Task | Prerequisites and derivation | Planned order | Branch state / action |
| --- | --- | --- | --- |
| `0043-01` | Existing producer field is consumed by combine; source setter must precede consumers | 1 | terminal; retained as evidence |
| `0043-02` | Ledger consumer contract requires correlated output from `0043-01` | 2 | terminal; retained as evidence |
| `0043-03` | Consumes ledger (`0043-02`) and the report-page header work (`0043-05`); the current backlog records both edges | 3 | terminal branch already exists; no retroactive A1 certification |
| `0043-04` | Needs the run/ledger chain from `0043-01`; its own gate-scope hold remains authoritative | parallel after `0043-01` | excluded from this pilot |
| `0043-05` | Independent page-generator/header work; it is a completed predecessor for later consumers | before `0043-03` rendering and `0043-06` | terminal branch/claim history retained |
| `0043-06` | Consumes `0043-02` and `0043-05`; maps reports to ASPICE outcomes | 4 | completed branch; prospective A1 was missed, so only retrospective evidence is retained |
| `0043-07` | Requires all six product Tasks and is the single integrating checkpoint | 5 | open/unclaimed; pre-branch A1 recorded below; no branch created here, mandatory review remains |

The `0043-03:0043-05` edge is intentionally retained because the header
generator changes the exact page rendered by `0043-03`; omitting it would force
an implementer to violate the base-and-merge rule or regress the header.

## Capability and test profiles

| Pilot task | Capability profile | Test scope/kind derived from contract |
| --- | --- | --- |
| `0043-03` | `unprivileged`; read/write its item worktree and report renderer; data: ledger JSONL and generated page model; tools: Git, Python, repository test fixtures; `execution_needs: direct`; cognitive demand `medium`; no acceptance/integration authority | Unit tests for ledger parsing/rendering, hermetic regeneration with two entries, and a real generator run because the requirement is a composed page/history contract |
| `0043-06` | `unprivileged`; read/write declared paths in its item worktree; data: report pages, ledger schema, ASPICE map; tools: Git, Markdown/link validators; `execution_needs: direct`; cognitive demand `medium`; no product/acceptance authority | Direct link/structure inspection and a map completeness check; manual evidence review is required because the criterion is assessor-facing honesty and names known gaps |
| `0043-07` | `privileged` Integrator; read/write candidate branches and all Feature artifacts; tools: Git and repository tests; data: integration evidence; `execution_needs: direct`; cognitive demand `high`; mandatory checkpoint and no self-acceptance | End-to-end publication run derived from the composition failure: correlated subreports → combine → ledger append → regenerated pages → staleness validation, with retained digest/evidence |

No profile grants publication, acceptance, `DONE.md`, or Feature/main merge to
an implementer. The capability class follows execution needs and authority;
the matcher in a successor Task must explain any rejection.

## Structured A1/A2 pilot records

### A1 records

```yaml
- task_id: "0043-03"
  field: A1-target-policy-integrability
  verdict: fits
  checked_target: main
  basis: "RQ-BR contracts; DEC-0043-001; current branch-workflow policy; repository evidence at 418f09b79"
  checked_at: "2026-08-22T15:40:00+02:00"
  recorded_by: "Architect role / agent:data-ada-20260822t150413z:0044-04:20260822T150413Z"
  status: "contract recorded; branch pre-existed, so this is not retroactive proof of a branch-time check"
- task_id: "0043-07"
  field: A1-target-policy-integrability
  verdict: fits
  checked_target: main
  basis: "0043-07 is [ ] and has no branch, worktree, or claim at the corrective check; its integrating contract requires all six product Tasks; current branch-workflow policy and DEC-0044-017 require the primary target to be main; this record does not claim, start, or integrate 0043-07"
  checked_at: "2026-08-22T20:43:54Z"
  recorded_by: "Architect role / agent:data-ada-20260822t150413z:0044-04:20260822T150413Z"
  status: "conforming pre-branch A1 record; 0043-07 remains open and unclaimed"
```

The first record is deliberately qualified: a branch-time gate cannot be
proven after the branch already exists. The `0043-07` record is the one actual
pre-branch pilot record: the branch/claim absence was checked immediately
before recording it, and this Task did not create or claim that work. The
rejected candidate's `pending-at-branch-creation` entries for `0043-06` and
`0043-07` were planning placeholders, not conforming A1 records; they are not
treated as records here.

`0043-06` is therefore recorded honestly as a missed prospective pilot and a
current-state retrospective only: its branch already existed and completed
without an A1 field, so no retroactive A1 verdict is asserted. Its deterministic
profile above describes the work package for successor matching, not a claim
that the completed branch passed a branch-time gate.

### A2 record and limitation

```yaml
task_id: "0043"
field: A2-order-deviation
status: not-tested
trigger: "canonical cross-item-blast-radius predicate"
planned_order: "0043-01, 0043-02, 0043-05, 0043-03, 0043-06, 0043-07 (with declared parallelism)"
actual_deviation: null
reason: "No current 0043 deviation can block another unit's start/validation/acceptance/integration/closure or change its contract"
owner_and_time: "not applicable; next newly broken-down Feature records it at recognition"
integrator_follow_up: "may demand a missing record at the checkpoint; in doubt, record"
```

This is an explicit untested status required by `DEC-0044-017` and A-12. It is
not silently converted into a pass. A later Feature must supply the A2 case
before the project claims the instruction is fully exercised.

## Findings and retained boundaries

- `0043-04` remains `[u]` and `0043-05` is not a fresh pilot surface; neither
  was touched.
- `0043-03` is a real worked application but its existing branch means A1 is
  represented as a structured contract with an explicit evidence limitation.
- `0043-06` missed the prospective A1 pilot; its completed branch is retained
  as a retrospective current-state observation, never as retroactive proof.
- `0043-07` has the sole new conforming pre-branch A1 record above; its task
  remains open/unclaimed and this evidence does not start or integrate it.
- A2 is not tested by this Feature. This evidence does not alter `TODO.md`,
  prerequisites, claims, acceptance, or integration state for Feature 0043.
- The pilot does not authorize any branch creation, merge, publication,
  acceptance, or `DONE.md` transition.
