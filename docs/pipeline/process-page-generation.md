# Process Page Generation & Publishing Protocol

Status: Normative process specification for Task **0036-03** (Feature `0036` — Review-Prozess-Dokumentation: Illustriert, verlinkt, mehrsprachig).  
Builds on: `docs/pipeline/published-process-page.md`, `docs/pipeline/curator-decision-protocol.md`, and `docs/pipeline/flag-for-review-protocol.md`.

---

## Purpose

This protocol specifies the controlled generation path for illustrated, user-facing process pages. It ensures that published explanations of the Curator Decision Protocol and Flag-for-Review Request Protocol are reproducible, localizable, link-stable, and never maintained by directly editing generated HTML.

The process page is a localized page family, not a single German-only static document. Its canonical source is German; translated variants are derived under the repository's regular i18n pipeline.

## Artifact Chain

The normative production chain is:

```text
Normative process documentation (docs/pipeline/*.md)
  -> canonical German page model (_src/sources/pages/*.json)
  -> optional AI-assisted explanatory text, illustrations, and diagram labels
  -> i18n extraction / translation / merge (protected tokens retained)
  -> per-language HTML generation (_src/generate.py)
  -> validation (_src/validate.py)
  -> published localized HTML page family
```

### Source and output boundaries

| Layer | Authoritative inputs | Derived outputs | Rules |
|---|---|---|---|
| Normative process definition | `docs/pipeline/*.md` | None | Defines roles, states, controls, and non-bypass rules. |
| Page model | `_src/sources/pages/*.json` | HTML page content | German source of the user-facing explanation. Do not edit generated HTML. |
| Diagrams and illustrations | Source assets under `_src/` | Rendered visual assets | Use existing Cytoscape/diagram generation infrastructure where appropriate; do not introduce a parallel renderer without an approved design decision. |
| Translation | Extracted i18n segments and approved translations | Language-specific page content | Preserve IDs, code spans, anchor identifiers, `[SWS_...]`/`[RS_...]` markers, and protected placeholders such as `⟦0⟧`. |
| Generation and verification | Page models, templates, translations, assets | Root and language HTML trees | Run `python3 _src/generate.py --lang=all`, then `python3 _src/validate.py`. |

## Page-Model Requirements

1. Create a canonical German model beneath `_src/sources/pages/`, with a stable filename and `file` value.
2. Make the page participate in the normal localized family; do not assign page-level `nolang` unless a documented exception requires it.
3. Keep live report widgets or repository-local operational evidence in individually marked `nolang` blocks when language-tree-relative links cannot resolve safely.
4. Put all prose, labels, diagram captions, and explanatory alternative text into the page model or registered translation sources so every user-visible string is eligible for extraction.

## Deep-Link Stability Policy

Dialog code may deep-link only to published anchors that are declared stable in the page model. Stable anchors are public interface identifiers and MUST NOT be renamed, removed, or repurposed without a compatible redirect/alias and validation update.

The initial stable anchor set for Feature `0036` is:

| Anchor | Meaning | Intended callers |
|---|---|---|
| `#curator-decision-protocol` | Overview of the curator decision flow (`review-package@v1`). | `review.js` help/documentation link |
| `#curator-decision-flow` | Step-by-step decision, package, submit, and ingestion flow. | `review.js` contextual help |
| `#flag-for-review-protocol` | Overview of the request flow (`review-request-package@v1`). | `review_request.js` help/documentation link |
| `#flag-for-review-flow` | Step-by-step request, queue, triage, and curator resolution flow. | `review_request.js` contextual help |
| `#storage-and-privacy` | Browser-local storage, authentication reuse, and privacy limits. | Both widgets |

Anchor rules:

- Anchors use lower-case ASCII kebab case and identify semantic sections, not visual layout.
- Every declared anchor must exist in German and every generated language tree.
- Dialog links must use a page-relative path that resolves from each language tree, or the generator must supply the locale-relative form.
- `validate.py` is the release gate for page-to-anchor reachability; failing or stale localized output blocks publication.

## AI-Assisted Content & Instruction Artifacts

AI assistance may draft user-friendly explanations, captions, alternative text, and diagram labels, but it cannot change normative process requirements or create a bypass around review and validation.

### Instruction source and versioning

- The collaboration and authority instruction baseline is `AGENTS.md`; sandbox and execution restrictions are in `SANDBOX.md`.
- A task-specific instruction artifact, when necessary, is stored in a version-controlled path under `docs/pipeline/` or `_src/` alongside the artifact class it constrains. It must name its scope, source inputs, allowed outputs, validation command, and invalidation trigger.
- Instruction artifacts are source artifacts: Git revision, review provenance, and the consuming build/run reference form the audit trail.

### Invalidation conditions

Regenerate AI-assisted output and repeat review when any of the following changes:

1. The authoritative normative process definition.
2. A page-model section, its stable anchor contract, or an underlying diagram source.
3. The relevant instruction artifact or model/prompt profile.
4. Translation source text or protected-token treatment.
5. Validation detects a stale page, missing translation, dead link, missing anchor, or incompatible asset.

## Build, Translation, and Release Sequence

1. Update or approve the relevant normative `docs/pipeline/` document.
2. Add or change the canonical German process-page model under `_src/sources/pages/` and diagram/illustration sources under `_src/`.
3. Extract and merge translations through the normal i18n workflow; do not hand-edit language-tree HTML.
4. Generate all language trees with `python3 _src/generate.py --lang=all`.
5. Run `python3 _src/validate.py`; resolve every stale tree, missing translation, dead link, missing anchor, orphan, and schema finding.
6. Commit sources, generated output, translation material, and validation evidence in reviewable units. Generated trees remain reproducible outputs, not manually authored pages.

## Relationship to Existing Architecture

`docs/pipeline/published-process-page.md` remains the governing structural contract for the general published process page. This document specializes that contract for Feature `0036` review-process pages: it adds the stable deep-link API, AI-instruction provenance, and explicit generated-artifact workflow without defining a competing page-generation architecture.
