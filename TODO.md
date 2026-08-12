# TODO — Review Workflow Goal Hierarchy

## Feature: Performance

- [ ] benchmark, optimize and parallelize generate.py, validate.py, and lib_docmodel.py

## Feature: Review & Feedback:

Requirement texts in the AUTOSAR AP documentation should be reviewable and
approvable in a traceable way — directly in the published HTML documentation,
without a separate tool and without a server component.

## Level 1 — Make Review Need Visible

- [x] Open review need is visible at the top of the page as a notice
- [x] Notice states the number of affected API elements
- [x] Notice links via intra-page link directly to the review panels
- [x] Each affected function carries a review badge in the function overview
- [x] Badge links to the associated panel (`#review-<Requirement-ID>`)
- [ ] Overview page for all open reviews across the entire tree

## Level 2 — Decision Basis in the Panel

- [x] Panel explicitly states what must be approved
- [x] Panel explains in plain language why a review is needed
- [x] Technical review reasons are translated into understandable labels
- [x] Metadata: API element, requirement ID, status, confidence, provenance
- [x] Source reference: module, specification document, page, upstream
- [x] Findings: anomalies, automatic repairs, review instruction
- [x] Original text viewable when the text was changed
- [x] Text hash protects against decisions on outdated text versions

## Level 3 — Reviewer Identity

- [x] "Decided by" field removed
- [x] With GitHub token, login is taken automatically
- [x] Without token, one-time self-declaration, stored locally
- [x] Empty name structurally excluded (minimum length, button disabled)
- [x] Name is normalized (whitespace, length)
- [x] Identity mode is recorded with every decision
- [x] Authenticated = person with checkmark, fallback = struck-through person
- [x] Panel shows the currently active identity, including switch option

## Level 4 — Submission

- [x] Decisions accumulate in a local package
- [x] Authenticated path: GitHub issue with `review-package@v1`
- [x] Fallback path: JSON download, marked as self-declared
- [x] Document fallback import in GitHub (path from JSON to issue)

## Level 5 — Flow Back into Sources

- [x] `review_ingest.py` validates package schema and identity mode
- [x] Hash conflict prevents adoption of outdated decisions
- [x] Decision documentation is written into the record
- [x] `--require-authenticated` enforces authenticated packages
- [x] Verify end-to-end `--apply` run with real record write
- [x] Define behavior for partial failures in large packages


## Level 6 — Canonical RS Upstream Metadata

- [x] Map canonical RS documents in the document registry
- [x] Extract RS requirements and provide as upstream index
- [x] Consider existing requirement records during compare/rebuild
- [x] Add or update `upstream` metadata in existing records
- [x] Keep additive writing of new requirement records unchanged
- [x] Test unchanged, updated, missing, and ambiguous upstream matches
- [x] Run compare/rebuild via `run.sh` with up to eight parallel jobs
- [x] Validate that only expected record metadata is changed


## Feature: Database Quality Assurance

### Campaign A — Baseline

- [ ] Freeze corpus and 200-record benchmark (still not freezable: `review.status = needs_review` on all 200 records, `complete_start = null`; 2 empty-fields records `RS_DIAG_04005`/`RS_SAF_21101` and 15 headingless-but-populated records need fixing or manual truthing first)

### Definition-precision follow-ups

- [ ] Treat dense definition lists (heading inline, no spec-item marker, e.g. RS_PHM_00001..00003 p.21) as an explicit record shape with its own fixtures
- [ ] Report precision/recall deltas against the previous campaign automatically; refuse check-in if recall drops without per-ID justification
- [ ] Cross-check IDs against the SWS traceability database as evidence of real requirements
- [ ] Detect release-scoped history phrasing ("revised"/"deleted"/"added" + release token like 19-03/R23-11) as a secondary rejection signal
- [ ] Measure per-document definition counts against published requirement counts as an external sanity check

### Validation debt surfaced by full-tree rebuild

- [ ] Decide whether `PRS_E2E_*` records must be published on a dedicated content page or be excluded from the orphan-record validator; document the intended invariant before changing either side
- [ ] Reduce `validate.py`'s `Records ohne expliziten Namensraum` finding from 3811 to a documented, intentional rule or a bounded exception list

### Working-tree triage — 2514 modified spec records (`_src/spec/records/`)

- [ ] Determine which tool produced the change (`migriere_spec_db.py`, `spec_upstream.py`, `text_repair.py`) and record the exact command
- [ ] Re-run that command from committed tool state and diff the result (reproducibility precondition)
- [ ] Inspect a stratified sample of 20 records manually before bulk commit
- [ ] Commit as a single data-only change with the generating command in the message, separate from tool changes

### Working-tree triage — 814 modified HTML files (published tree)

- [ ] Confirm files are reproducible via `python3 _src/generate.py && python3 _src/validate.py` from current `_src/` state
- [ ] If reproducible, commit as a regeneration; if not, find the missing `_src/` change first

### Working-tree triage — unrelated tooling/docs in flight

- [ ] `_src/tests/test_geometry_schema.py`'s `BaselineFusionTests` (for `geometry_audit._is_baseline_fusion`) should be committed together with the `geometry_audit.py` change once finished
- [ ] Reconcile `_src/tests/test_spec_upstream.py`'s `from _src.tools...` import style with the `sys.path` convention used by other test modules before adding it to the suite
- [ ] Gitignore or delete untracked scratch artifacts (`graphrender.detail`, `unified-focus-controller.patch`, `_src/perplexity-*.applescript`) rather than committing them

## Next Sensible Steps

1. End-to-end test of `review_ingest.py --apply` in a writable environment
2. Global overview page of all open reviews
3. Document fallback import path
4. Then delete this file
