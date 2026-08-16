# TODO-perplexity-0036-01 — working claim for AGENT PERPLEXITY

owner_token: agent:perplexity:0036-01:h5w2f1re3plmz2Fq
base_commit: pending-discovery
capability_class: sandboxed/grunt

## Claimed Task

**0036-01** (Feature 0036 — Review-Prozess-Dokumentation: Illustriert, verlinkt, mehrsprachig)

> Normative Prozessbeschreibung fuer das Curator-Entscheidungsprotokoll (`review-package@v1`, `review.js`) in `docs/pipeline/` verfassen.

Feature context (for drift detection): Feature 0036 documents two review processes (curator decision protocol from `review.js`, and the flag-for-review request process from Feature 0021/0035) plus the meta-process for generating illustrated, i18n'd process pages, all in `docs/pipeline/`, following the existing `docs/pipeline/published-process-page.md` pattern and reusing the Cytoscape diagram infrastructure.

No Feature-level or Task-level PREREQ is declared on 0036-01 in `TODO.md`; no other active `TODO-*.md` claim references 0036-01 or 0036 at all.

## Scope

- Write scope: new/updated file(s) under `docs/pipeline/` documenting the curator decision protocol (`review-package@v1`) as implemented by `review.js`.
- Runner scope: none required yet for pure documentation authoring reachable via non-execution file tools; may need a bounded read-only runner request later to inspect `review.js` behavior if static reading is insufficient.
- No overlap with the active 0037-04.01 claim (different feature, different files).

## Progress log

- 2026-08-16: Selected via top-to-bottom scan of `TODO.md`. Feature 0037 remaining open items (0037-04 through 0037-40) all have unmet start prerequisites or are already claimed (0037-04.01, in progress by another session). 0036-01 is the first open, unclaimed task with no unmet prerequisites. Claim created; about to mark `[p]` in `TODO.md`.
