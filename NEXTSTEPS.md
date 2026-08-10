# Next steps: significantly improve PDF extraction quality

## Objective

Build a reproducible, evidence-driven extraction pipeline that captures complete AUTOSAR requirement records from both supported PDF backends, compares their output side by side, and iteratively improves both implementations rather than treating one as merely a fallback.

The desired result is not just a higher record count. Each extracted requirement should have reliable boundaries, preserved reading order, complete field text, a canonical ID, precise page provenance, and machine-readable quality evidence. Persisting upstream full text into the record database is allowed only after the extraction quality gates below pass.

## Scope and principles

- Improve both principal backends extensively:
  - `pypdf`: improve layout-aware reconstruction, reading order, glyph normalization, record continuation, and field parsing.
  - `builtin`: improve PDF object/font decoding, text positioning, spacing, reading order, stream handling, and record continuation.
- Keep backend extraction independent until comparison. Shared cleanup may operate only after raw backend output has been saved, so common code cannot hide matching backend defects.
- Treat `auto` as policy, not as a third source. It may select a backend only after both concrete backends have been evaluated.
- Preserve raw evidence at every stage. Never overwrite raw page text with normalized or repaired text.
- Compare semantically meaningful fields, not only ID counts.
- Do not silently merge disagreements. Preserve both candidates and record why a winner was selected.
- Do not rebuild `_src/spec/records/` until the guarded acceptance phase.

## Target data model

Create a canonical upstream-requirement source store under `_src/spec/upstream/` rather than duplicating full requirement text in every SWS record. Existing SWS records keep their `upstream` references and can resolve the content by ID.

Each canonical requirement should contain at least:

```json
{
  "id": "RS_AP_00127",
  "heading": "Usage of ara::core types",
  "text_raw": "...",
  "text_en": "...",
  "fields": {
    "description": "...",
    "rationale": "...",
    "applies_to": ["AP"],
    "dependencies": [],
    "use_case": "...",
    "supporting_material": "..."
  },
  "source": {
    "document": "AUTOSAR_AP_RS_General.pdf",
    "pages": [2],
    "backend": "pypdf",
    "release": "R25-11"
  },
  "alternatives": [],
  "quality": {
    "status": "verified",
    "backend_agreement": "exact|normalized|field-level|conflict",
    "complete_start": true,
    "complete_end": true,
    "warnings": []
  },
  "traceability": []
}
```

Store backend-specific observations separately from the canonical decision, for example under `_src/spec/upstream/evidence/<document>/<id>/<backend>.json`. This keeps full provenance and allows re-evaluation after parser improvements.

## Phase 1 — Baseline corpus

Create a fixed benchmark corpus before changing extraction logic.

- Include all 18 canonical AP/FO RS documents in `RS_DOCS`.
- Add difficult SWS documents that exercise tables, syntax blocks, columns, ligatures, embedded fonts, and page-spanning records.
- Stratify requirements by shape:
  - Single-page records.
  - Records spanning two or more pages.
  - Dense property tables.
  - Bullet and numbered lists.
  - Multiple requirements on one page.
  - IDs with mixed-case namespace tokens.
  - Hyphenation, ligatures, Unicode punctuation, and unusual fonts.
  - Empty fields and explicit dash values.
- Select at least 200 manually reviewed requirements, with at least 25 from each major difficult shape and examples from every canonical RS document.
- Save expected record boundaries, headings, fields, and page ranges as fixtures under `_src/tests/fixtures/spec_extraction/`.
- Include negative fixtures containing references and table-of-contents entries that must not become definitions.

Baseline metrics for each backend:

- Definition precision and recall.
- Exact ID set agreement.
- Record start/end boundary accuracy.
- Field completeness by field.
- Heading accuracy.
- Reading-order accuracy.
- Page-range accuracy.
- Truncation rate.
- Label spillover rate.
- Replacement-character and undecoded-glyph rate.
- Normalized text similarity.
- Backend disagreement count by category.

## Phase 2 — Reproducible run harness

- [x] Build `_src/tools/spec_extraction_campaign.py` to orchestrate repeated experiments. Significant extraction runs must go through project-root `run.sh` according to `AGENTS.md`.

Each campaign should:

1. Create a unique directory such as `output/extraction-campaigns/2026-08-10-a/`.
2. Record Git revision, command line, Python/package versions, document hashes, backend configuration, and parser configuration.
3. Run `pypdf` and `builtin` independently for every selected document.
4. Save raw page text, normalized page text, record slices, parsed fields, warnings, timing, and failures.
5. Generate side-by-side reports in JSON, CSV, Markdown, and static HTML.
6. Produce a machine-readable scorecard against the fixed benchmark.
7. Compare the campaign with the previous best run and flag regressions.

Use `run.sh` parallelism amply:

- Run independent document/backend pairs concurrently.
- Cap active workers at eight.
- Prefer one worker per document/backend pair; avoid nested multiprocessing.
- Print progress at least every five seconds: queued, active, completed, failed, records extracted, and disagreements found.
- Keep compare/report generation as a separate phase after all extraction workers finish.
- Permit several campaigns in sequence: baseline, backend change A, backend change B, combined parser change, and final verification.
- Never install or download dependencies directly; any required installation or download belongs in a clearly described `run.sh`.

A typical campaign matrix contains 36 jobs for 18 canonical documents times two backends. Larger SWS campaigns may be split into deterministic batches while preserving a common campaign ID.

## Phase 3 — Raw backend artifacts

Add a stable backend interface returning structured page observations rather than only strings:

```python
PageObservation(
    page_number,
    raw_text,
    spans,
    warnings,
    backend,
    document_hash,
)
```

A span should preserve, where available:

- Text.
- Bounding box or text matrix.
- Font identity and size.
- Writing direction.
- Source content stream and operation index.
- Whether spacing or a line break was inferred.

Save raw output before `strip_noise`, dehyphenation, whitespace normalization, field parsing, or repair. Add deterministic serializers so repeated runs produce stable diffs.

## Phase 4 — Improve `pypdf`

Perform extensive, iterative work on the `pypdf` backend.

### Layout and reading order

- [x] Use visitor callbacks or equivalent text-fragment access to capture coordinates, matrices, font size, and orientation.
- [x] Reconstruct lines by vertical clustering with tolerances derived from font size.
- [ ] Order spans horizontally within lines while respecting columns and table cells. Left-to-right evidence ordering is implemented; column/table region classification remains open.
- [x] Detect headers, footers, and page numbers from repeated coordinates across pages, not only text regexes.
- [x] Detect multi-column pages and avoid interleaving columns.
- [x] Preserve bullets and list indentation.
- [x] Distinguish visual line wraps from paragraph boundaries.

### Fonts and glyphs

- [x] Inventory fonts and `/ToUnicode` maps by document.
- [x] Record missing mappings and replacement characters as warnings.
- Normalize known ligatures only in the normalized layer while retaining raw glyph evidence.
- Handle soft hyphens, nonbreaking spaces, en/em dashes, smart quotes, and mathematical symbols deterministically.
- Add fixtures for every observed glyph failure.
- Resolve fonts through Form XObject and inline resource dictionaries, not only page-level `/Resources`; unnamed spans currently account for half of all corpus glyph failures.
- [x] Quarantine glyph-failed spans so control-code text cannot reach normalized output or requirement fields, and report affected pages per document.

### Record continuity

- Join page-spanning definitions using ID/record delimiters and page-position evidence.
- Remove repeated headers and footers before joining, but retain page provenance for every fragment.
- Prevent the next requirement’s labels or heading from spilling into the previous record.
- Mark incomplete records instead of truncating silently.

### Iterative pypdf campaigns

Run separate campaigns after each substantial change:

1. Coordinate capture only.
2. Line reconstruction.
3. Column/table ordering.
4. Font/glyph normalization.
5. Cross-page joining.
6. Header/footer suppression.

Compare every campaign with baseline and reject changes that improve averages while regressing benchmark classes without an explicit reason.

## Phase 5 — Improve `builtin`

Perform equally extensive work on the builtin backend; do not leave it as a simplistic fallback.

### PDF structure

- Support classic xref tables, xref streams, object streams, inherited page resources, nested Form XObjects, and multiple content streams.
- Decode all filters encountered in the corpus with explicit unsupported-filter diagnostics.
- Resolve page-tree inheritance correctly.
- Track content stream and operation provenance.

### Font decoding

- Parse and apply `/ToUnicode` CMaps, including `bfchar`, `bfrange`, multibyte codes, codespace ranges, and indirect CMap references.
- Handle simple fonts, Type0/CID fonts, encoding differences, and common built-in encodings.
- Create a font-decoding inventory and tests from real corpus subsets.
- Never silently fall back to Latin-1 without a warning and quality penalty.

### Text state and geometry

- Implement relevant text operators and state: `BT`, `ET`, `Tf`, `Tm`, `Td`, `TD`, `T*`, `Tc`, `Tw`, `Tz`, `TL`, `Ts`, `Tj`, `TJ`, single quote, and double quote.
- Compose current transformation matrices through Form XObjects.
- Infer spaces from glyph advances, word spacing, and `TJ` adjustments rather than fixed magic thresholds.
- Reconstruct lines and reading order from geometry using the same output contract as pypdf, but an independently implemented algorithm.
- Preserve superscripts, subscripts, bullets, and table alignment where relevant.

### Streams and malformed input

- Handle escaped/nested literal strings robustly.
- Decode hex strings and multibyte character codes correctly.
- Report malformed objects with document/page/object context.
- Continue extracting unaffected pages after a localized failure.

### Iterative builtin campaigns

Run focused campaigns after:

1. CMap/font support.
2. Text-state implementation.
3. Geometry and spacing.
4. XObject and inherited-resource support.
5. Reading-order reconstruction.
6. Cross-page record joining.

Use the same benchmark and scorecard as pypdf. The builtin backend should eventually be capable of independently validating the pypdf result for nearly all canonical documents.

## Phase 6 — Shared record segmentation

After raw page reconstruction, improve record segmentation independently of field parsing.

- Recognize mixed-case IDs and canonicalize IDs only in normalized output.
- Distinguish definition headers such as `[RS_Diag_04260]` from references in prose, dependency lists, indexes, and traceability tables.
- Use geometric and textual evidence for record starts.
- Use explicit end markers, the next definition, section boundaries, and page continuation evidence for record ends.
- Track `pages: [start, ..., end]`, not only the first page.
- Store the exact source fragments contributing to each record.
- Produce explicit warnings: `missing_end`, `next_record_overlap`, `page_join_uncertain`, `reference_only`, and `duplicate_definition`.

Add segmentation tests that run identically against both backends’ page-observation fixtures.

## Phase 7 — Field parser

Replace the current broad `Description` capture with a label-aware state machine.

Recognize at minimum:

- Description.
- Rationale.
- AppliesTo.
- Dependencies.
- Use Case.
- Supporting Material.
- Type and other document-specific labels.

Rules:

- A field ends at the next recognized label belonging to the same record.
- Labels split across spans or lines must be recognized.
- Repeated labels across a page break must not create duplicate content.
- Bullets and paragraph structure should be preserved.
- Explicit dash values map to an empty value plus an `explicit_none` marker rather than disappearing.
- Unknown labels are retained in `extra_fields` and generate a warning.
- `text_raw` is assembled from untouched field fragments; `text_en` receives only deterministic, logged repairs.
- No field may absorb the next requirement or footer.

Maintain document-family label profiles where necessary, but prefer a shared parser with explicit extensions over ad hoc regexes.

## Phase 8 — Side-by-side comparison

Create a report for every document and requirement with aligned columns:

| Aspect | pypdf | builtin | Decision |
|---|---|---|---|
| ID and heading | Extracted value | Extracted value | Agreement/conflict |
| Page range | Pages | Pages | Agreement/conflict |
| Description | Full candidate text | Full candidate text | Similarity and diff |
| Rationale | Candidate | Candidate | Agreement/conflict |
| AppliesTo | Parsed values | Parsed values | Agreement/conflict |
| Boundaries | Start/end evidence | Start/end evidence | Confidence |
| Warnings | Backend warnings | Backend warnings | Required action |

The HTML report should provide:

- Synchronized line-by-line or token-level diffs.
- Highlighted insertions, deletions, and moved fragments.
- Links to raw page artifacts and canonical PDF page locators.
- Filters for missing IDs, boundary differences, low similarity, field disagreement, glyph warnings, and page-span differences.
- Summary charts/tables by document, backend, field, and failure category.

Comparison tiers:

1. Exact raw agreement.
2. Agreement after safe Unicode/whitespace normalization.
3. Field-level semantic agreement with formatting differences.
4. One backend demonstrably complete and the other incomplete.
5. Genuine unresolved conflict requiring manual review.

Never choose a candidate only because it is longer. Prefer the candidate with complete boundaries, valid labels, page continuity, fewer decode warnings, and benchmark-supported behavior.

## Phase 9 — Consensus and review

Implement a deterministic consensus policy:

- Automatically accept when both backends agree after safe normalization and all completeness checks pass.
- Accept one backend over the other only when explicit quality rules prove the other is truncated, interleaved, undecoded, or boundary-invalid.
- Store the rejected candidate in `alternatives` with the rejection reason.
- Route genuine conflicts to a review queue with side-by-side evidence.
- Require manual review for records with missing boundaries, unsupported fonts, unknown labels, cross-page uncertainty, or substantive backend disagreement.
- Keep `RS_AP_00154` and `RS_DIAG_04005` explicitly unresolved unless a canonical definition is found; do not synthesize text.

## Phase 10 — Tests

Add test layers:

- Unit tests for PDF string decoding, CMaps, text operators, geometry, line reconstruction, normalization, segmentation, and field parsing.
- Golden-page tests for both backends using compact, legally retained fixtures or generated PDFs that reproduce observed constructs.
- Golden-record tests for the manually reviewed 200-record benchmark.
- Differential tests requiring side-by-side reports for every disagreement.
- Metamorphic tests: harmless whitespace/object ordering changes must not alter canonical records.
- Property/fuzz tests for literal strings, `TJ` arrays, malformed streams, and label wrapping.
- Integration tests over all canonical RS PDFs.
- Idempotence tests for evidence and canonical JSON serialization.
- Regression tests for every manually diagnosed defect.

No quality fix is complete until its failing corpus example is represented by a regression test.

## Phase 11 — Quality gates

Do not persist canonical full text until all mandatory gates pass:

- 100% canonical RS document extraction completes without unhandled exceptions.
- 100% expected definition IDs are accounted for as extracted, withdrawn/absent, or explicitly reviewed.
- At least 99.5% definition precision and recall on the manually reviewed benchmark.
- At least 99% exact field-boundary accuracy for Description and Rationale.
- Zero silent truncations in the benchmark.
- Zero next-record spillovers in the benchmark and full canonical corpus checks.
- Zero undecoded glyphs without warnings.
- At least 98% of canonical records reach backend agreement at tiers 1–3.
- Every tier-4 selection has a machine-readable reason.
- Every tier-5 conflict is in the review queue.
- Repeated runs with identical inputs produce byte-identical evidence and canonical JSON.
- Full unit/integration suite, `python3 _src/generate.py`, and `python3 _src/validate.py` pass.

Track both aggregate scores and worst-document scores. Averages must not hide a badly performing document.

## Phase 12 — Guarded persistence

After quality gates pass:

1. Write canonical full-text requirement records to `_src/spec/upstream/` atomically.
2. Keep backend evidence in `_src/spec/upstream/evidence/` or an equivalent durable evidence store.
3. Extend SWS `upstream` entries with a stable reference to the canonical requirement record; avoid duplicating text in thousands of files.
4. Generate derived HTML pages showing upstream ID, heading, structured fields, full extracted text, canonical source link, page range, backend agreement, and review status.
5. Run a compare-only migration first.
6. Require zero unexpected additions, removals, missing IDs, ambiguous IDs, or content regressions.
7. Run the write via `run.sh`.
8. Verify that only intended upstream source records, references, and generated HTML change.
9. Run a second compare and require zero updates to prove idempotence.
10. Regenerate and validate the complete documentation.

## Recommended campaign sequence

### Campaign A — Baseline

- [ ] Freeze corpus and 200-record benchmark.
- [x] Run both current backends over all canonical documents.
- [x] Produce the first side-by-side report and initial machine-readable failure taxonomy.
- [x] Recover builtin record-boundary glyphs through ToUnicode CMap decoding and validate the improvement across all 18 RS documents.

### Campaign B — pypdf geometry

- Add span coordinates, line reconstruction, repeated-header suppression, and cross-page joining.
- Run pypdf and builtin again; compare against Campaign A and the benchmark.

### Campaign C — builtin fonts

- Implement CMaps, multibyte glyph decoding, and font diagnostics.
- Repeat the full two-backend run and side-by-side comparison.

### Campaign D — builtin geometry

- Implement text state, matrices, spacing, lines, columns, and Form XObjects.
- Repeat the full comparison and classify remaining layout failures.

### Campaign E — segmentation

- Introduce shared record-boundary logic and page-range provenance.
- Run both backends and audit all changed record boundaries.

### Campaign F — structured fields

- Introduce the field state machine and complete `text_raw`/`text_en` assembly.
- Compare all fields side by side, not only whole-record text.

### Campaign G — consensus

- Implement deterministic acceptance and review rules.
- Generate the complete disagreement queue and manually review high-impact conflicts.

### Campaign H — release candidate

- Run both backends twice from a clean output directory.
- Require deterministic results and every quality gate.
- Perform compare-only database migration.

### Campaign I — persistence

- Persist canonical upstream full text and evidence through a guarded `run.sh`.
- Generate documentation, validate, inspect diffs, and prove idempotence.

## Deliverables

- `_src/tools/spec_extraction_campaign.py` — parallel campaign runner.
- Stable `PageObservation`, span, record-evidence, comparison, and canonical schemas.
- Extensively improved pypdf and builtin implementations.
- `_src/tests/fixtures/spec_extraction/` benchmark corpus and expected results.
- Unit, golden, differential, integration, fuzz, and regression tests.
- Side-by-side JSON/CSV/Markdown/HTML comparison reports.
- Machine-readable scorecards and campaign-to-campaign regression reports.
- Durable canonical upstream store with full extracted text and provenance.
- Generated upstream-requirement documentation linked from SWS records.
- Maintenance documentation for running campaigns, reviewing conflicts, and performing guarded persistence.

## Definition of done

This work is done only when both backends have received substantial independent improvements, repeated parallel campaigns demonstrate the gains, side-by-side evidence explains every remaining disagreement, the benchmark and full-corpus quality gates pass, canonical full text is stored with provenance, generated documentation exposes it, and a second complete run is byte-stable and produces no database updates.

## Additional improvement ideas

These ideas complement the backend geometry plan and should be introduced as isolated, measurable campaigns rather than bundled into one parser rewrite.

### Definition-occurrence classification

- Classify every requirement-ID occurrence before record selection as `definition`, `toc`, `trace-table`, `changelog`, `cross-reference`, or `unknown`.
- Base classification on own-page evidence only: section context, geometric region, record delimiters, field-label density, font/size patterns, and neighboring IDs. Never let joined continuation pages change the source page's class.
- Keep all candidates and classification features in evidence artifacts; select only after classification, and record the selection reason.
- Train no opaque model initially. Start with inspectable rules and a frozen labeled fixture set containing all known multi-occurrence failures, especially `RS_LT_00062` and `RS_AP_00143`.
- Add a candidate-selection shadow mode that reports proposed changes without altering extraction, then require per-field non-regression before activation.

### Geometry diagnostics

- Generate optional SVG or HTML page overlays showing span boxes, baselines, font IDs, inferred lines, columns, record boundaries, and reading-order arrows.
- Assign stable span and line IDs so a disagreement can be traced from parsed field text back to exact PDF operations.
- Add per-page geometry sanity checks: impossible coordinates, overlapping lines, extreme jumps, reversed baselines, out-of-page spans, and unusually dense clusters.
- Store compact geometry fingerprints per page to detect unintended layout changes even when normalized text remains equal.

### Adaptive layout inference

- Derive vertical clustering, word-gap, indentation, and column thresholds from each page's font-size and glyph-advance distributions rather than global constants.
- Detect table regions from repeated x-alignments and ruled rectangles; use a table-specific reading order only inside those regions.
- Model reading order as a directed acyclic graph of spans/lines with explicit edge reasons, then topologically sort it and report ambiguous edges.
- Separate body, margin, header, footer, and sidebar regions geometrically before text normalization.
- Preserve a confidence score and warnings for every inferred space, line break, column transition, and dehyphenation.

### Differential and metamorphic testing

- Add metamorphic fixtures where harmless PDF changes—content-stream splitting, equivalent `Tm`/`Td` positioning, reordered resource dictionaries, or alternative string encodings—must yield identical observations.
- Add mutation tests that remove a CMap, alter a matrix, inject an unsupported filter, or corrupt one object and require localized diagnostics rather than silent global degradation.
- Compare backend output at span, line, record, and field levels so the first divergence layer is visible.
- Minimize every newly found corpus failure into a small committed PDF or synthetic content-stream fixture before fixing it.
- Run deterministic-repeat checks and require byte-identical raw evidence and reports from identical inputs.

### Quality and triage metrics

- Track precision and recall for record starts, record ends, headings, and each normative field independently; aggregate agreement alone can hide shared omissions.
- Add severity-weighted gates: missing records, boundary spillover, or empty normative fields outweigh punctuation and whitespace differences.
- Report disagreement clusters by normalized edit signature, document template, font, page region, and operator sequence to prioritize fixes with the broadest impact.
- Maintain a known-exceptions file with owner, rationale, first-seen campaign, affected IDs, and expiry/review date; never encode unexplained exceptions in parser logic.
- Add automatic regression bisection support that can compare saved campaign artifacts across commits without rerunning PDF extraction.

### Performance and reproducibility

- Cache immutable page observations by PDF hash, backend version, and extractor configuration so parser-only campaigns do not repeat PDF decoding.
- Separate extraction, layout reconstruction, segmentation, field parsing, and comparison into versioned artifact stages with explicit schemas and migration checks.
- Record runtime, peak memory, warning counts, and artifact sizes per document/backend; gate pathological resource regressions.
- Add manifest checksums for every input, configuration file, tool source, and output artifact used in a campaign.
- Provide a single replay command that reconstructs any report entirely from its manifest and cached immutable observations.

### Human review workflow

- Produce a review queue ordered by severity, low confidence, and disagreement novelty rather than raw ID order.
- Show raw spans, reconstructed lines, both backend fields, source-page overlay, and candidate-selection reasons together.
- Allow review decisions to be exported as immutable fixtures and expected outcomes, not parser-specific overrides.
- Require two-source agreement or explicit human verification before marking canonical upstream content as `verified`.

### Geometry evidence hardening

- Validate reconstructed reading order against body-only legacy text (headers and footers removed) instead of full raw text, so margin exclusion is not misreported as missing content.
- [x] Add a JSON schema for the observation artifact and validate every emitted document against it, so new geometry fields cannot silently change shape.
- [x] Run all geometry classifiers over every cached PDF, not only one canonical document, and report per-document counts for margins, bullets, indentation, wraps, and columns.
- [x] Add invariant checks that hold for any document: every span belongs to exactly one line, reading order covers body lines exactly once, and classifier outputs are pure functions of geometry.
- [x] Detect rotated or vertically written text and exclude it from horizontal line reconstruction instead of interleaving it into prose.
- Emit per-document geometry quality metrics (unclassified body lines, zero-baseline fragments, single-span lines) to expose extraction degradation early.
