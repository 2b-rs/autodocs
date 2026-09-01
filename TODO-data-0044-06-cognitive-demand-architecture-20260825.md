# Architect governance coordination — `0044-06` cognitive-demand calibration

record_kind: governance-coordination
task_id: 0044-06
request_id: cognitive-demand-20260825T214726Z-0d41a19f
owner_token: agent:data:0044-06:cognitive-demand-20260825T214726Z-0d41a19f
base_commit: 433b41b04cd4b353f9681947a9e3c7897a751855
capability_class: privileged
execution_authority: direct
state: [x]
recorded_task_state: [ ]
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

## Open identity-format blocker

The exact assigned claim path ends in
`cognitive-demand-architecture-20260825.md`, while this session's already-minted
immutable request ID is `cognitive-demand-20260825T214726Z-0d41a19f`.
Consequently the legacy doctor requires the different canonical filename
`TODO-data-0044-06-cognitive-demand-20260825T214726Z-0d41a19f.md` and reports
one attributable `LTD-CLAIM-IDENTITY-MISMATCH`. The exact write-scope assignment
forbids that rename, and immutable-token rules forbid rewriting the token after
it entered committed history. All other packet diagnostics are clean. The next
action requires Project Lead direction that explicitly reconciles the assigned
path with immutable claim identity; no unassigned mutation is authorized.

## Additive historical disposition

Project Lead direction `agent-inbox:1787694795766-f8cea917` authorizes the
canonical live identity at
`TODO-data-0044-06-cognitive-demand-20260825T214726Z-0d41a19f.md`. This
originally assigned file is retained as inactive historical coordination
provenance for the exact briefing, collision discovery, architecture work, and
identity-format finding. It asserts no second lease, ownership, or live claim;
the immutable token is neither rewritten nor reassigned. The canonical file is
the sole live identity record for any later resumption and handoff.

historical_disposition: inactive-coordination-provenance
lease_active: false
canonical_claim_path: TODO-data-0044-06-cognitive-demand-20260825T214726Z-0d41a19f.md

Canonical identity repair REF:
`0442694d38a79fbfbd08928a1d2ea42e5811265c`.

## Current-main re-pin

The governance-only re-pin requested under
`agent-inbox:1787698716694-07e845be` is re-derived from
`main@433b41b04cd4b353f9681947a9e3c7897a751855` and retains exact candidate
`5ff57c7717208283c1000530b93318b633d64918` as ancestry. This record remains
inactive historical coordination provenance with `lease_active: false`; its
disclosed `LTD-CLAIM-IDENTITY-MISMATCH` remains visible because the legacy
doctor does not interpret the appended disposition. The re-pin neither rewrites
the immutable token nor represents that historical finding as clean.
