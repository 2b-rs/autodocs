# Independent Architect scope-review brief — `0022-01`

## Requested review

Review the non-operative proposal at
`docs/dossiers/0022-feature-breakdown-proposal.md` against the exact candidate
REF supplied by the Project Lead. Decide whether its cross-item reach, affected
work units/gates, planned Task graph, checkpoint placement, and no-broad-gate
boundary are fit for a later conforming `DEC-0022-*` record and operative
implementation.

This is a pre-mutation scope review. It is not Task Acceptance, an integration
review/verdict, implementation, Feature closure, or authority to advance
`main`.

## Required reviewer identity and separation

- management-instantiated Architect;
- identity distinct from `agent:data:0022-01:20260828T095108Z-3e883c05` and
  from the later Implementer;
- preferably assigned by Team Enterprise Project Lead `jean-luc`; because Team
  Enterprise has no second Architect seat, cross-team Architect capacity is
  expected if no new Enterprise seat is instantiated;
- capability `privileged` for the review record only; privilege does not create
  independence or Acceptance authority for this package.

## Pinned inputs to remeasure

1. current `main` and Task `0022-01` block;
2. candidate proposal and claim bytes;
3. `DEC-0020-001`, `DEC-0020-002`, and the `0020-02` scope review;
4. `0020-03`, `0020-04`, and `0020-09` predecessor contracts;
5. current contracts of `0023-11`, `0024-02`, and conditional Features
   `0028`–`0032`;
6. `docs/pipeline/decision-record.md`, `feature-breakdown.md`, and the current
   `AGENTS.md` cross-item exception.

Material baseline drift makes the review inconclusive until the proposal is
reconciled. Green tests do not establish reach or authority.

## Questions requiring an explicit verdict

1. Does `PD-0022-01-GATE-01` require a new `decision-record@v1`, or does a
   specifically identified existing record already decide every proposed gate?
2. Are `0023-11`, `0028`–`0032`, Feature `0022` closure, and `0024-02` correctly
   classified as direct or downstream affected units/gates?
3. Does `not-decided` correctly permit a definition row while failing every
   activation/use gate that needs the missing party or authority?
4. Does the proposal avoid the broad start/validation gate rejected by
   `DEC-0020-002`?
5. Is `0022-01` an appropriate intermediate mandatory checkpoint, with
   `0022-03` the exactly-one terminal integrating Task?
6. Is the split of `0022-02` into schema and validator Subtasks bounded,
   complete, and free of duplicate ownership?
7. Are recovery, no-grandfathering, self-application, A1/A2, and later
   acceptance/integration boundaries complete?

## Allowed verdicts

- `scope-ok-with-conditions`: list every binding condition and the exact
  candidate digest;
- `scope-needs-revision`: list stable findings and the smallest safe repair;
- `scope-inconclusive`: identify the missing authority/source pin.

The reviewer must not allocate or integrate a decision record unless separately
assigned that governance action. The Project Lead retains coordination and
routes any Management decision.
