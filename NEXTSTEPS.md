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
  Measured 2026-08-11 on the R25-11 corpus: TOC pages of the canonical RS documents carry no
  bracketed IDs (0 dotted-leader entries with IDs), and no `Upstream requirements:` line contains a
  bracketed ID, so neither category yields harvestable instances. The realized negatives are the 46
  change-history entries in `negative-history.json`. Re-check this assumption when difficult SWS
  documents enter the corpus, because their TOCs and traceability tables differ.

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
- [x] Order spans horizontally within lines while respecting columns and table cells. Left-to-right evidence ordering, multi-column page ordering, and stable repeated-alignment table regions with per-region cell identities are implemented. Validated on all 1,171 Diagnostics pages: 885 table regions, 2,896 table rows, and no table-region invariant violations.
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
- Recover readable characters from mixed spans that combine a few valid glyphs with unmapped codes, instead of quarantining the whole span; measured at 82 of 1,113 affected spans in CommunicationManagement.
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

- [ ] Freeze corpus and 200-record benchmark. Draft built from campaign `2026-08-11-pagespan` at `_src/tests/fixtures/spec_extraction/benchmark-draft.json`: 200 records, 18/18 canonical documents, page provenance on every record, every difficult shape at or above 25 examples. **Review status 2026-08-11:** not freezable yet, but three root-cause classes are now fixed in `_src/tools/spec_scrape.py` and require regeneration of the draft before further manual review: (1) multi-page `Document Change History` continuation leakage (fixed and verified in campaign `2026-08-11-historyfix`); (2) `Requirements Tracing` table leakage (fixed: top-of-page `N Requirements Tracing` pages now classify as `traceability` regions, so upstream IDs such as `RS_HM_09249` on `AUTOSAR_AP_RS_PlatformHealthManagement` p.17 and `RS_SAF_10037`/`RS_SAF_10040` on `AUTOSAR_AP_RS_Persistency` p.17 no longer become local definition candidates, while genuine later-page definitions like `RS_AP_00116`/`RS_AP_00119`/`RS_AP_00122` remain intact on their real pages); (3) appendix `Number Heading` continuation leakage in RS/SWS traceable-item-history tables (fixed: pages such as `AUTOSAR_AP_RS_ExecutionManagement` p.29 and `AUTOSAR_AP_RS_CommunicationManagement` p.36 are now recognized as multi-page history-table continuations when they start with `Number Heading` and also carry an `Added/Changed/Deleted Requirements|Constraints` caption, so rows like `RS_EM_00006`/`00007`/`00012`/`00013`/`00050`/`00051`/`00052` and appendix-only `RS_CM_00600`/`00601` no longer pollute the definition index). Structural coverage is still correct (`status: draft-needs-manual-review`, 200 records, 18 documents, zero duplicates), but the fixture remains unfreezable until it is regenerated from the fixed extractor and every record gets explicit manual review notes/status; all 200 records still leave `expected.complete_start = null`; 31 records still have `expected.heading = null`; 16 of those still have empty `expected.fields = {}` in the pre-fix draft. After the three extractor fixes above, the residual unresolved class appears narrower: title-line heading derivation/layout cases such as `AUTOSAR_FO_RS_LogAndTrace` (`RS_LT_00001`, `RS_LT_00002`, `RS_LT_00028`), where the human-visible requirement title is the sentence immediately above the bracketed ID rather than a separate parser-captured heading. Freeze only after the draft is regenerated, these residual records are re-reviewed, `complete_start` is filled explicitly, and each remaining headingless/fieldless case is either corrected or explicitly justified.
- [x] Emit per-record page-span provenance (`pages`, `pages_all_definitions`, `complete_end`) and observed ID spelling (`id_observed`) from `phase_props`, verified identical across both backends on all 18 RS documents (810 records each, 109 multi-page, 809/810 terminated).
- [x] Investigate `RS_SM_00201` (AUTOSAR_AP_RS_StateManagement p.22): no record terminator found within the six-page scan window. Resolved: the sole occurrence sits inside the page's "A.8.3 Deleted Requirements in 19-03" change-history table, not in body text (`[RS_SM_00002] ... [RS_SM_00201] State Management shall provide the interface over ara::com.` under `Table A.14: Deleted Requirements in 19-03`). It was still surfacing as an unterminated record in the `2026-08-11-pagespan` campaign (git revision `04b6b7ae`) because that campaign predates the change-history rejection work. Commit `6e076521` ("Reject change-history IDs per occurrence and add negative fixtures") already fixes this: re-running `python3 _src/tools/spec_scrape.py props --doc AUTOSAR_AP_RS_StateManagement --pattern '^RS_' --backend pypdf|builtin --json` at current HEAD (`96bfa89b`) confirms `RS_SM_00201` is absent from both backends' output and is correctly listed under `history_only_ids`/`history_only_evidence`. No code change needed; a fresh campaign run will no longer show this as a termination failure once `spec_extraction_campaign.py` is re-invoked at current HEAD.
- [x] Decide the canonical policy for the 269 records whose source spelling uses lowercase namespace tokens (e.g. `RS_Diag_00024` normalized to `RS_DIAG_00024`). Decision: **keep `id` uppercase-canonical for lookup/keys/traceability, and keep `id_observed` as the verbatim source spelling for display/evidence.** Findings backing this: (1) both backends agree on `id_observed` for all 269 IDs across the four affected documents (`AUTOSAR_AP_RS_OperatingSystemInterface` 1, `AUTOSAR_FO_RS_Diagnostics` 181, `AUTOSAR_FO_RS_IntrusionDetectionSystem` 25, `AUTOSAR_FO_RS_NetworkManagement` 62 — zero cross-backend spelling disagreements), so this is a genuine, reproducible source-document typographic quirk (e.g. `RS_Diag_`, `RS_Ids_`, `RS_Nm_`, `RS_Main_` TitleCase namespace tokens), not an extraction artifact; (2) `phase_props` already emits both fields (`spec_scrape.py`, `id_observed = spellings[rid][0]`) and the benchmark draft already carries `mixed_case_id` as a stratification category with 25+ examples, so no schema change is required; (3) uppercase-canonical keys keep cross-document/cross-backend joins, DB keys, and traceability links stable and case-insensitive, matching how every other ID in the corpus is already keyed. No code change needed. Remaining action: when the benchmark is frozen, confirm each `mixed_case_id` fixture's `expected` block asserts both the canonical `id` and the verbatim `id_observed` so regressions in either field are caught.
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

- Compare quality metrics only against baselines that already contain the same metric fields; a missing field must be reported as unmeasured, never silently as zero.
- Attribute the remaining corpus body-word shortfall per page and confirm it is fully explained by quarantined glyph-failed spans before treating any residue as a defect.

- [x] Validate reconstructed reading order against body-only legacy text (headers and footers removed) instead of full raw text, so margin exclusion is not misreported as missing content.
- [x] Add a JSON schema for the observation artifact and validate every emitted document against it, so new geometry fields cannot silently change shape.
- [x] Run all geometry classifiers over every cached PDF, not only one canonical document, and report per-document counts for margins, bullets, indentation, wraps, and columns.
- [x] Add invariant checks that hold for any document: every span belongs to exactly one line, reading order covers body lines exactly once, and classifier outputs are pure functions of geometry.
- [x] Detect rotated or vertically written text and exclude it from horizontal line reconstruction instead of interleaving it into prose.
- [x] Emit per-document geometry quality metrics (unclassified body lines, zero-baseline fragments, single-span lines) to expose extraction degradation early.
- [x] Insert separators between adjacent spans that legacy extraction separates, so joined line text does not fuse words such as `Rationale:error`; measured as a small body word shortfall on 23 of 42 pages of AUTOSAR_AP_RS_General.

## Additional ideas from the definition-precision investigation (2026-08-11)

- [x] Reject history entries per *occurrence* instead of per page: a page can carry
  both an appendix history table and body text, so page-level classification loses
  real definitions (currently 8, all in ExecutionManagement and PlatformHealthManagement).
- [x] Persist every rejected ID as evidence (`history_only_ids`,
  `history_only_evidence` with page and region reason) so precision changes are auditable
  and reversible rather than silent.
- [x] Derive the negative fixtures automatically from the confirmed rejections
  instead of hand-listing them, and fail the test suite when a known negative
  reappears as a definition.
- [x] Add a document-structure pass that labels appendix/annex regions once
  (history tables, change log, TOC, bibliography) and reuse it for extraction,
  segmentation and the benchmark instead of re-detecting per phase.
- [ ] Treat the dense definition lists (heading inline, no spec-item marker, e.g.
  RS_PHM_00001..00003 on page 21) as an explicit record shape with its own
  fixtures; it is currently the main source of false negatives.
- [ ] Report precision/recall deltas against the previous campaign automatically
  and refuse to check in a change whose recall drops without an accompanying
  per-ID justification.
- [ ] Cross-check IDs against the SWS traceability database: an ID referenced as
  upstream by an existing record is strong evidence that it is a real requirement.
- [ ] Detect release-scoped history phrasing ("revised", "deleted", "added" plus a
  release token such as 19-03 or R23-11) as a secondary rejection signal that is
  independent of table geometry.
- [ ] Measure per-document definition counts against the published requirement
  count where the document states one, as an external sanity check.

## Working-tree triage (2026-08-11)

The checkout carries a large amount of pre-existing, unrelated work. Assessment
and plan per cluster:

### Committed in this session

- `_src/tools/spec_scrape.py`, `_src/tests/test_spec_scrape_upstream.py`,
  `_src/tests/fixtures/spec_extraction/`, `NEXTSTEPS.md`: page-span provenance,
  occurrence-level history rejection, reusable page-structure classifier,
  negative fixtures. Verified by campaign `2026-08-11-defprecision` (36/36 jobs,
  both backends reject the identical 46 IDs, gate PASS) and 10 unit tests.

### Not ready: 2514 modified spec records under `_src/spec/records/`

Generated data, not hand-written source. Do not commit them mixed with tool
changes.

- [ ] Determine which tool produced the change (`migriere_spec_db.py`,
  `spec_upstream.py`, `text_repair.py`) and record the exact command.
- [ ] Re-run that command from the committed tool state and diff the result; a
  reproducible regeneration is the precondition for committing.
- [ ] Inspect a stratified sample of 20 records manually before bulk commit.
- [ ] Commit as a single data-only change with the generating command in the
  message, separate from any tool change.

### Not ready: 814 modified HTML files in the published tree

`AGENTS.md` declares the HTML tree a build artifact. Content changes belong in
`_src/`.

- [ ] Confirm the files are reproducible via `python3 _src/generate.py &&
  python3 _src/validate.py` from the current `_src/` state.
- [ ] If reproducible, commit as a regeneration; if not, find the missing `_src/`
  change first and never hand-edit the tree.

### Not ready: unrelated tooling and documentation in flight

`_src/lib_docmodel.py`, `_src/publish.sh`, `_src/validate.py`,
`_src/tools/geometry_audit.py`, `_src/tools/sync_to_devel.sh`,
`_src/templates/page.html.tmpl`, `_src/i18n/ui.json`, `AGENTS.md`,
`KONVENTIONEN.md`, `SPEC_TRACEABILITY.md`, `WARTUNG.md`, plus untracked
`spec_upstream.py`, `text_repair.py`, `review_*.py`, `BACKLOG.md`, `TODO.md`,
AppleScript helpers and `review.js`.

- [ ] Not mine; author intent unknown. Leave untouched.
- [ ] `_src/tests/test_geometry_schema.py` adds `BaselineFusionTests` for
  `geometry_audit._is_baseline_fusion` and belongs with the `geometry_audit.py`
  change; commit those two together once that work is finished.
- [ ] `_src/tests/test_spec_upstream.py` imports as `from _src.tools...`, which
  differs from the `sys.path` convention used by every other test module;
  reconcile before adding it to the suite.
- [ ] Untracked scratch artifacts (`graphrender.detail`,
  `unified-focus-controller.patch`, `_src/perplexity-*.applescript`) should be
  gitignored or deleted rather than committed.
