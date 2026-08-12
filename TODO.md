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
- [x] Overview page for all open reviews across the entire tree

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

- [ ] Freeze corpus and 200-record benchmark (still not freezable: `review.status = needs_review` on all 200 records, `complete_start = null`; 12 headingless-but-populated records still need fixing or manual truthing first)
  - 2026-08-12: manually truthed the two previously called-out "empty-fields" blockers in `_src/tests/fixtures/spec_extraction/benchmark-draft.json`:
    - `RS_SAF_21101` is intentionally an inline citation in prose on pages 9-10 of `AUTOSAR_AP_RS_PlatformHealthManagement.pdf`, not a formal requirement block; `heading = null`, `fields = {}`, and `complete_start = null` are correct ground truth. Added an explanatory review note.
    - `RS_DIAG_04005` on page 15 of `AUTOSAR_FO_RS_Diagnostics.pdf` is a real formal requirement block (`[RS_Diag_04005] Manage Security Access level handling`); replaced the incorrect empty expected values with the actual heading/fields and `complete_start = true`, with a review note explaining the mixed-case source ID.
  - Recount after this truthing: exactly 12 headingless-but-populated benchmark entries remain, all in `AUTOSAR_FO_RS_LogAndTrace` (`RS_LT_00001`, `00002`, `00003`, `00004`, `00008`, `00028`, `00030`, `00031`, `00032`, `00033`, `00035`, `00037`). This cleanly overlaps with the separate TODO item to model dense definition lists as an explicit record shape.

### Definition-precision follow-ups

- [ ] Treat dense definition lists (heading inline, no spec-item marker, e.g. RS_PHM_00001..00003 p.21) as an explicit record shape with its own fixtures
- [ ] Report precision/recall deltas against the previous campaign automatically; refuse check-in if recall drops without per-ID justification
- [ ] Cross-check IDs against the SWS traceability database as evidence of real requirements
- [ ] Detect release-scoped history phrasing ("revised"/"deleted"/"added" + release token like 19-03/R23-11) as a secondary rejection signal
- [ ] Measure per-document definition counts against published requirement counts as an external sanity check

### Validation debt surfaced by full-tree rebuild

- [x] Decide whether `PRS_E2E_*` records must be published on a dedicated content page or be excluded from the orphan-record validator; document the intended invariant before changing either side
  - Decision: excluded. `e2e-requirements.html` already presents all 349 `PRS_E2E_*` requirements as a flat overview table by design (no standalone C++ API, per its own intro text); wiring them individually into `rec-ref` panels would be artificial. `validate.py`'s orphan check now carries a documented, bounded exception for `spec/records/PRS_E2E/`.
- [ ] Reduce `validate.py`'s `Records ohne expliziten Namensraum` finding from 3811 to a documented, intentional rule or a bounded exception list
  - Root cause confirmed: `ns.namespace` is populated for exactly one group, `SWS_LOG` (71/71 records) — every other group (`SWS_CORE` 1177, `SWS_DM` 937, `SWS_CRYPT` 352, `PRS_E2E` 349, `SWS_CM` 225, `AP_SWS` 146, `SWS_TS` 123, `SWS_RDS` 133, `SWS_PER` 129, `SWS_EM` 47, `SWS_SM` 46, `SWS_AIDSM` 61, `SWS_PHM` 35, `SWS_ANM` 30, `SWS_UCM` 21) has 0% coverage
  - This is a genuine backfill gap, not a validator scoping bug; needs a namespace-extraction pass (likely from the same spec sections `SWS_LOG`'s records were derived from) rather than a mechanical bulk-edit — use `SWS_LOG` as the reference for what a complete `ns` block looks like

### Working-tree triage — 2514 modified spec records (`_src/spec/records/`)

- [x] Determine which tool produced the change (`migriere_spec_db.py`, `spec_upstream.py`, `text_repair.py`) and record the exact command
  - `spec_upstream.py`'s `rebuild_record_files()`, called via `spec_scrape.py`'s `upstream` phase: `python3 _src/tools/spec_scrape.py upstream --rs-docs --pdf-dir _src/spec/pdf-cache/R25-11 --rebuild`
- [x] Re-run that command from committed tool state and diff the result (reproducibility precondition)
  - Rebuild + immediate re-compare reported `updated=0` (idempotent); a first attempt (run.sh #241) used a flawed pre-check comparing 'updated' to the raw git-dirty count and incorrectly aborted — corrected in run.sh #242
- [x] Inspect a stratified sample of 20 records manually before bulk commit
  - Sampled 32 files (2 per namespace group, all 16 groups) via structural JSON diff (ignoring key order/indent). 31/32 changed only the `upstream` field as expected; 2 (`SWS_LOG_00018`, `SWS_LOG_00021`) also carried bundled-in unrelated changes — investigated further below
- [x] Commit as a single data-only change with the generating command in the message, separate from tool changes
  - Committed in `caa6cef4` (amended from initial `bd550836` once the bundled-file issue below was found), with full provenance disclosed in the message
  - Follow-up finding: a full-diff grep across all 2996 committed files found exactly 71 files (all `SWS_LOG/`, matching that group's full size) that additionally bundled in pre-existing, already-dirty changes from an unrelated `2026-08-sws-log-pilot-after-tool-improvement` campaign (status/ns/legacy/history/fields backfill) plus one `legacy-desc-import` conversion. These were NOT produced by the upstream rebuild; they were already uncommitted in the working tree and got swept in because the commit staged all `_src/spec/records/*` dirty files rather than filtering to files spec_upstream.py actually touched. Disclosed explicitly in the amended commit message; content itself was not reverted since it appears to be legitimate, separately-produced backfill data — but it means this commit is not as narrowly scoped as originally intended. No further action taken here; flagging for awareness only

### Working-tree triage — 814 modified HTML files (published tree)

- [x] Confirm files are reproducible via `python3 _src/generate.py && python3 _src/validate.py` from current `_src/` state
  - Confirmed: a direct re-run of validate.py's stale-check (`iter_pages()` + `render_page()` vs. tree) reports 0 stale pages across the German tree; `generate.py --lang=alle` has run clean twice in a row via run.sh with no "Tree nicht aktuell" warning. Modified-file count has grown to ~4060 (all languages) as further _src/ edits landed in this session
- [x] If reproducible, commit as a regeneration; if not, find the missing `_src/` change first
  - Committed in `0b059142`: 4060 modified `*.html` files (8680 insertions, 4150 deletions), pure regeneration with 0 stale pages confirmed and `validate.py` showing no "Tree nicht aktuell"

### Working-tree triage — unrelated tooling/docs in flight

- [x] `_src/tests/test_geometry_schema.py`'s `BaselineFusionTests` (for `geometry_audit._is_baseline_fusion`) should be committed together with the `geometry_audit.py` change once finished
  - Already done: both landed together in `826f792e` ("Separate baseline text fusion from unexplained word shortfall"); no working-tree diff remains. Re-ran `BaselineFusionTests` directly — 3/3 pass.
- [x] Reconcile `_src/tests/test_spec_upstream.py`'s `from _src.tools...` import style with the `sys.path` convention used by other test modules before adding it to the suite
  - Stale: the file already uses `sys.path.insert(str(Path(__file__).resolve().parents[1] / "tools"))` followed by a plain `from spec_upstream import ...` — exactly the convention used by `test_geometry_schema.py` and other test modules. No `from _src...` import exists anywhere in `_src/tests/`. It was already committed as part of `1f15ba6c` ("Add spec_upstream reference resolver with tests"), so it's already in the suite.
- [x] Gitignore or delete untracked scratch artifacts (`graphrender.detail`, `unified-focus-controller.patch`, `_src/perplexity-*.applescript`) rather than committing them
  - Stale: `docs/brainstorming/graphrender.detail` and `_src/perplexity-echo.as` are already tracked and clean (no diff vs. HEAD). `unified-focus-controller.patch` doesn't exist anywhere in the tree. `_src/perplexity-loop.applescript` is also already tracked; its only diff is this session's prompt-text update (matching this very run loop's instruction), not scratch content — nothing here needs gitignoring or deleting.

## Next Sensible Steps

1. End-to-end test of `review_ingest.py --apply` in a writable environment
2. Global overview page of all open reviews
3. Document fallback import path
4. Then delete this file
