# TODO-perplexity-0036-01 — working claim for AGENT PERPLEXITY

owner_token: agent:perplexity:0036-01:h5w2f1re3plmz2Fq
base_commit: 6491b538f
capability_class: sandboxed/grunt
state: [p]

## Claimed Task

**0036-01** (Feature 0036 — Review-Prozess-Dokumentation: Illustriert, verlinkt, mehrsprachig)

> Normative Prozessbeschreibung fuer das Curator-Entscheidungsprotokoll (`review-package@v1`, `review.js`) in `docs/pipeline/` verfassen.

## Scope

- **Deliverable**: `docs/pipeline/curator-decision-protocol.md`
- **Criteria Addressed**:
  - Item schema (`outcome`, `decided_by`, `identity`, `rationale`, `decision_basis`).
  - Storage location (`ara-review-package-v1`, `ara-review-github-token-v1`, `ara-review-identity`).
  - Batch submit as GitHub issue and JSON fallback export.
  - Relation to `workflow-lifecycle.md` direct transition (`discovered -> applied`) and `roles.md`.

## Progress

- 2026-08-16: Created `docs/pipeline/curator-decision-protocol.md` matching `review.js` implementation and repository lifecycle contracts.
