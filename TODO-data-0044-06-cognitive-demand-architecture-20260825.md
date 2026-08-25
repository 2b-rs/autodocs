# Architect governance coordination — `0044-06` cognitive-demand calibration

record_kind: governance-coordination
task_id: 0044-06
request_id: cognitive-demand-20260825T214726Z-0d41a19f
owner_token: agent:data:0044-06:cognitive-demand-20260825T214726Z-0d41a19f
base_commit: 8a364e000fed6e826a1e7d49c4b1c014c849eece
capability_class: privileged
execution_authority: direct
state: [ ]
coordination_state: complete
architect_work_product_status: [x]
write_scope: ["TODO-data-0044-06-cognitive-demand-architecture-20260825.md", "docs/dossiers/dec-0044-026-cognitive-demand-scope.md", "docs/dossiers/0044-06-cognitive-demand-scope-review.md"]

## Assignment and separation

Project Lead Jean-Luc issued the corrected exact Architect assignment under
`agent-inbox:1787694446375-0d41a19f`, following the collision report for the
superseded `DEC-0044-025` briefing. Data owns only the pre-mutation decision and
scope review. This record does not claim Task implementation or change the open
Task marker. Data must not implement `0044-06` or later review, accept, or
integrate this product.

## Baseline and allocation

- Fresh current `main` before worktree creation:
  `8a364e000fed6e826a1e7d49c4b1c014c849eece`.
- `DEC-0044-001` through `DEC-0044-025` were allocated; `DEC-0044-026` had no
  occurrence on current `main` and no committed-history hit at allocation.
- Branch: `gov-0044-06-cognitive-demand-data-20260825`.
- Worktree:
  `/Users/tobias.anton/devel/autodocs/.worktrees/0044-06-cognitive-demand-governance-data-20260825`.
- The root checkout was read-only and no authoritative marker was changed.

## Intended write scope

- `TODO-data-0044-06-cognitive-demand-architecture-20260825.md`
- `docs/dossiers/dec-0044-026-cognitive-demand-scope.md`
- `docs/dossiers/0044-06-cognitive-demand-scope-review.md`

## Delivered architecture

`DEC-0044-026` preserves the existing `low | medium | high | critical`
vocabulary, bounds the method to explainable repository-local calibration and
shadow predictions, and prevents estimates from independently granting or
withholding authority. The supporting review specifies the five-dimension
rubric, historical selection and falsification evidence, two-channel
nondeterminism protocol, affected work units/gates, staged activation, rollback,
and Implementer/Acceptance/Integrator separation.

Substantive governance REF:
`66878d88d24f401696ac1c7fb83f38a9eb57d000`.

## Intended validation and handoff

Hand the exact candidate containing the substantive REF and final validation
evidence to Jean-Luc for a separately assigned governance integration. Do not
advance `main` or begin implementation.
