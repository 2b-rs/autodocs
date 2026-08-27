# Canonical Architect coordination — `0044-06` cognitive-demand calibration

record_kind: governance-coordination
task_id: 0044-06
request_id: cognitive-demand-20260825T214726Z-0d41a19f
owner_token: agent:data:0044-06:cognitive-demand-20260825T214726Z-0d41a19f
base_commit: 433b41b04cd4b353f9681947a9e3c7897a751855
capability_class: privileged
execution_authority: direct
state: [ ]
coordination_state: complete
architect_work_product_status: [x]
historical_source_path: TODO-data-0044-06-cognitive-demand-architecture-20260825.md
write_scope: ["TODO-data-0044-06-cognitive-demand-architecture-20260825.md", "TODO-data-0044-06-cognitive-demand-20260825T214726Z-0d41a19f.md", "docs/dossiers/dec-0044-026-cognitive-demand-scope.md", "docs/dossiers/0044-06-cognitive-demand-scope-review.md"]

## Identity and disposition

This is the canonical live identity for the immutable owner token minted by
this session. Project Lead direction `agent-inbox:1787694795766-f8cea917`
expanded the exact scope to this path after the fixed original filename was
shown to be incompatible with canonical claim identity. The original assigned
file remains append-only inactive coordination provenance and asserts no second
lease or ownership.

This coordination record does not change Task `0044-06`'s open marker and does
not claim implementation. Architect Data authored only `DEC-0044-026` and its
pre-mutation scope review and is excluded from later implementation, Acceptance,
checkpoint review, and integration of that product.

## Intended write scope

- `TODO-data-0044-06-cognitive-demand-architecture-20260825.md`
- `TODO-data-0044-06-cognitive-demand-20260825T214726Z-0d41a19f.md`
- `docs/dossiers/dec-0044-026-cognitive-demand-scope.md`
- `docs/dossiers/0044-06-cognitive-demand-scope-review.md`

## Evidence and status

- Baseline: `main@8a364e000fed6e826a1e7d49c4b1c014c849eece`.
- Substantive governance REF:
  `66878d88d24f401696ac1c7fb83f38a9eb57d000`.
- `DEC-0044-026` preserves `low | medium | high | critical` and bounds
  calibration to explainable shadow operation pending later authority.
- The original assigned coordination file preserves the exact briefing,
  collision, and identity-repair history without rewriting its token.
- Canonical identity repair REF:
  `0442694d38a79fbfbd08928a1d2ea42e5811265c`.

## Current-main re-pin

Project Lead Jean-Luc requested a governance-only re-pin under
`agent-inbox:1787698716694-07e845be` after `main` advanced to
`433b41b04cd4b353f9681947a9e3c7897a751855`. Branch
`gov-0044-06-cognitive-demand-data-20260825-r2` starts at that exact main
commit and merges candidate `5ff57c7717208283c1000530b93318b633d64918`
as preserved ancestry. The intervening main paths are disjoint from this
four-path packet. Decision, scope-review, identity-repair, historical-finding,
and separation semantics remain unchanged.

- Current base: `433b41b04cd4b353f9681947a9e3c7897a751855`.
- Re-pin worktree:
  `/Users/tobias.anton/devel/autodocs/.worktrees/0044-06-cognitive-demand-governance-data-20260825-r2`.
- Prior exact candidate retained as the second parent:
  `5ff57c7717208283c1000530b93318b633d64918`.
- Current-baseline validation: `process_doc_doctor.py --root . --json` exits
  `0` with 32 findings on both current main and candidate. The legacy doctor
  returns expected repository-wide exit `1`: current main has 777 findings,
  while the candidate has 778; the sole attributable delta is the already
  disclosed `LTD-CLAIM-IDENTITY-MISMATCH` on the retained inactive historical
  coordination path. The canonical claim and both dossiers add no finding.
- `git diff --check` passes; the exact net diff from current main contains only
  the four declared packet paths; `DEC-0044-026` remains absent from current
  main before integration and retains 15 fields, four alternatives with exactly
  one selected, and eight consequences.

## Next step

Validate the exact four-path candidate, claim classification, decision shape,
document diagnostics, and governance-origin trailers; then hand the immutable
candidate to Jean-Luc for separately assigned governance integration. Do not
advance `main` or begin implementation.
