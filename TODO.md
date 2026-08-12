# TODO — Open Point List

HOW TO USE:

- *Features* are represented as 2nd level Headings.
- New *Features* shall normally be added to the top of list
- Features consist of *Tasks*.
- a *Feature* is considered complete once all of its *Tasks* are complete.
- Complete *Features* shall be moved to DONE.md and marked with a completion date + time. TODO.md and DONE.md must be committed after each completed feature.

- *Tasks* are dashed items, one line per task, with a completion marker. Examples see below
  [ ] - open. No work has been done w/r to this item
  [u] - unclear. Before work can proceed, the manager needs to be interviewed and make a decision.
  [p] - partially implemented - work has been done but it's not complete. open items after TODO: in the same line.
  [?] - unknown - we simply don't know. Next step is to look into the repository and decide whether to amend TODO: or promote do [x]
  [x] - executed - task has been completed. If a task is completed, the results shall be checked in and REF: xxxxxx (git hash) shall be added 
- *Tasks* shall have a granularity so that they can be implemented in one go, i.e. without further user interaction. 

## Feature: Dutch (nl) Translation

- [x] translate and merge `_src/i18n/work/nl/batch_01.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 202/202 entries completed and merged (2026-08-12), 0 rejects, no `fehler.json` produced. HTML tree regeneration still pending.
- [ ] translate and merge `_src/i18n/work/nl/batch_02.jsonl` (0/215 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_03.jsonl` (0/210 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_04.jsonl` (0/223 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_05.jsonl` (0/204 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_06.jsonl` (0/214 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_07.jsonl` (0/215 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_08.jsonl` (0/210 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_09.jsonl` (0/225 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_10.jsonl` (0/192 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_11.jsonl` (0/205 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_12.jsonl` (0/226 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_13.jsonl` (0/229 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_14.jsonl` (0/236 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_15.jsonl` (0/199 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_16.jsonl` (0/232 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.
- [ ] translate and merge `_src/i18n/work/nl/batch_17.jsonl` (0/1218 entries completed as of 2026-08-12); then run `python3 _src/i18n_translate.py merge nl` and verify no new rejects in `_src/i18n/work/nl/fehler.json`.

## Feature: Data Quality

- [ ] investigate 3811 spec records without an explicit namespace (e.g. `SWS_AIDSM_10706`, `SWS_AIDSM_10301`, `SWS_AIDSM_10602`, `SWS_AIDSM_10205`, `SWS_AIDSM_10710`), flagged by `validate.py` (2026-08-12, run.sh #252). Currently causes `validate.py` to exit 1. Determine whether namespace should be inferred/backfilled during scrape/rebuild, or whether these records are legitimately namespace-less and validate.py's check needs an allowlist/exception similar to the existing PRS_E2E carve-out.

- [x] investigate 34 remaining SWS_UCM_* records without namespace data after fixing validate.py's check_namespaces() schema mismatch (2026-08-12, run.sh #265): all 34 are 'service method' records scoped to a service interface (e.g. SWS_UCM_00348 -> PackageManagement), suggesting the namespace-assignment tooling doesn't cover service-interface-scoped methods (unlike class-scoped methods, which populate namespace_meta correctly). Determine whether these need a namespace derived from the service interface's own namespace, or whether service methods are legitimately namespace-less and belong in spec/namespaces.json's 'abweichungen' catalog instead. -- RESOLVED 2026-08-12 (run.sh #268): confirmed via AUTOSAR spec research (SWS_CM_01005, EXP_ARAComAPI.pdf) that service methods MUST inherit their enclosing service interface's namespace (this is Path A, backfill, not a legitimate exception). Backfilled namespace_meta for all 34 records with source='ai-derived-from-service-interface' and review_status='pending' for curator confirmation; namespace-assignment tooling should be extended with this rule to prevent recurrence for future service-interface-scoped records.

## Feature: Review & Feedback:

- [ ] Requirement texts in the AUTOSAR AP documentation should be reviewable and approvable in a traceable way — directly in the published HTML documentation, without a separate tool and without a server component.

## Feature: Unified Curation Platform

- [ ] From the curator's and user's perspective, review, feedback, and curation should not split into separate silos based on technical origin (scrape ambiguity vs. DB correction vs. AI amendment vs. AI-proposed new element). There should be one coherent, traceable lifecycle for "an item that needs human judgment", with stable identity across projects, full history, visible status, and both static and future dynamic presentation layers.

### Architecture decisions to make visible in code/data

- [ ] introduce a project-aware canonical identity scheme for every curatable item
  - Current gap (2026-08-12): records and queues are implicitly single-project (`_src/spec/records/<MODULE>/<ID>.json`, queue filenames = `<ID>.json`), and the docs contain no evidence of multi-project support for future AUTOSAR Classic / FOUNDATION / Eclipse S-Core expansion.
  - Decide and document a canonical key such as `project/release/kind/id` (example dimensions: `AUTOSAR/AP/R25-11/record/SWS_UCM_00348`, `AUTOSAR/FOUNDATION/R25-11/record/RS_SAF_00001`, `ECLIPSE/S-CORE/<release>/record/<id>`), then propagate it into record metadata, queue payloads, campaign manifests, and rendered HTML anchors.
  - Ensure the raw record `id` can remain human-familiar while the canonical identity becomes the cross-project stable key for queues, history, links, and reports.

- [ ] define one unified "curation item" schema that subsumes `review-flag@v1` and `curation-flag@v1`
  - Current gap: `review_flags.py` and `curation_flags.py` are near-duplicate but divergent queues with different payload shapes, different directory trees, and different semantics.
  - Design a single schema with at least: `schema`, `canonical_id`, `project`, `release`, `item_kind` (record-field / record / ai-amendment / ai-hypothesis / scrape-observation / report-entry), `origin` (tool / ai / browser / curator), `status` (open / claimed / proposed / accepted / rejected / superseded / applied), `subject`, `current_state`, `proposed_state`, `evidence`, `counter_evidence`, `decision_basis`, `campaign`, `created`, `claimed_by`, `decided_by`, `completed_at`, and `history`.
  - Make the schema expressive enough to represent: (a) scrape ambiguities, (b) DB-value corrections, (c) AI-generated amendments to existing records, (d) AI-proposed new spec elements / requirements currently only described as `hypothesized/unconfirmed` in the process docs.

- [ ] extend the record schema to carry stable provenance for curator-visible changes across all modules, not just pilot records
  - Current gap: `history[]`, `status`, and field-level states exist mostly in pilot-style records (`SWS_LOG` etc.), while many production records still only carry additive fields like `upstream` without matching lifecycle/history entries.
  - Make `status`, `history[]`, and (where applicable) field-level `fields.<name>.state/reason/trace` mandatory or mechanically backfillable for any write path (`spec_scrape.py`, `review_ingest.py`, `curation_ingest.py`, migrations, future AI-amendment tools).
  - Add explicit provenance for AI-originated proposals vs. curator-accepted DB changes so that "proposal" and "applied truth" remain distinguishable in static and dynamic views.

- [ ] add first-class support for AI-proposed NEW elements in the DB and queue model
  - Current gap: `hypothesized/unconfirmed` exists in docs as a status, but no implemented CLI or queue path creates such elements.
  - Define where hypotheses live before acceptance (separate hypothesis store vs. lightweight record stubs), how they get canonical IDs, how evidence is attached, and how acceptance promotes them into the main DB without losing history.

### Workflow / pipeline convergence

- [ ] converge browser review, queue review, AI proposals, and curator decisions into one end-to-end state machine
  - Current gap: the docs show two partially disconnected paths — queue-based (`review-queue` / `curation-queue` -> AI agent -> curator) and browser-based (`review.js` -> GitHub issue / JSON -> `*_ingest.py`).
  - Model one shared lifecycle with explicit states and transitions, including: discovered -> queued -> claimed -> proposed -> accepted/rejected -> applied -> published -> superseded.
  - Map every existing tool to that lifecycle (`review_flags.py`, `curation_flags.py`, `review_ingest.py`, `curation_ingest.py`, `spec_scrape.py`, future AI-amendment tools) and document which transitions each tool may perform.

- [ ] design a feedback loop from curator decision back into extraction/scrape/database logic
  - Current strength: `curation_flags.py` already assumes the output of a curation request is not just "data overwrite" but sometimes a code change or new residual rule.
  - Missing piece: a generalized, documented mechanism that can express whether a decision should update a DB value, create a migration, change parser logic, add an allowlist/exception, or spawn a new benchmark/fixture.
  - Add decision outcome classes and post-decision hooks so feedback scales beyond the extraction-report residual list.

- [ ] resurrect and implement campaign manifests as the versioning backbone for curation work
  - Current gap: `docs/pipeline/data-model.md` documents `_src/spec/campaigns/<id>.json`, but explicitly notes no such manifest files were found in the repo.
  - Use campaign manifests to version review/curation waves across projects/releases (source corpus hash, tool versions, queue snapshot, curator decisions, published reports) so a curator can later answer "which exact state of the corpus and tools produced this request?"

### Visibility / UX

- [ ] build a static HTML "curation report" that renders all open and recent curation items from the queue(s)
  - Current gap: open flags in `_src/spec/curation-queue/open/` and `_src/spec/review-queue/open/` are invisible unless someone browses the filesystem.
  - Implement a `curation_report.py` (or broader `workflow_report.py`) analogous to `traceability_report.py`: read the queue(s), render a page model under `_src/sources/pages/`, publish via `generate.py`, and link it from the start page.
  - Each rendered item should show canonical identity, project/release, current DB state, proposed state, rationale, evidence, status, and links to the affected record/page/report.

- [ ] design the future dynamic JS/API view around the same schema, not a second ad-hoc model
  - Static HTML is needed first, but the future JS layer should consume the same canonical curation-item schema (serialized to JSON/JS) so filter/sort/group functionality does not fork the data model.
  - Plan for filters by project, release, queue status, item kind, module, source tool, curator, and campaign.

- [ ] expose curator-visible history for each DB element in published pages
  - Current gap: record pages do not systematically surface `history[]`, status evolution, or open review/curation state to users.
  - Add a visible section/badge on record pages showing current review/curation status, latest accepted decision, and links to the relevant curation item/report entry.
  - This should work for both existing records and future AI-proposed elements, with clear labeling of "proposed", "accepted", "rejected", and "applied".

### Hardening / migration

- [ ] inventory and migrate existing queue items and special-case review surfaces into the unified model
  - Inputs to cover: `review-queue`, `curation-queue`, extraction-report `RESIDUAL` items, ad-hoc TODO-driven investigations like the 34 service-method namespace conflict, and any pilot record-level `requirement_meta.review_*` states.
  - Define which of these become first-class curation items, which remain reports only, and which are historical artifacts to archive.

- [ ] add validation and tests for the unified workflow model
  - Extend `validate.py` (or add a dedicated validator) to check canonical IDs, queue payload schema/version, allowed state transitions, referential integrity to records/pages, and history completeness.
  - Add fixtures covering at least: a scrape ambiguity, a DB correction request, an AI-generated amendment to an existing record, and a new hypothesized requirement.

- [ ] document the feature as a repo-level workflow contract before implementation spreads further
  - Update `docs/pipeline/{data-model,roles,actions,processes,reports,tools}.md` and `_src/SPEC_BUILD_PROCESS.md` so the unified curation model is the documented source of truth, not just emergent queue code.
  - Explicitly record what remains human-only, what AI may propose, and what tools may apply automatically.


## Feature: Database Quality Assurance

### Campaign A — Baseline

- [ ] Freeze corpus and 200-record benchmark (still not freezable: `review.status = needs_review` on all 200 records, `complete_start = null` on many)
  - 2026-08-12: the 12 headingless-but-populated blockers (all `RS_LT_*`) are resolved. `spec_scrape.py`'s new numbered-subsection heading fallback (commit `fdba7e28`) recovers their real headings from the source PDF; `benchmark-draft.json`'s expected values were updated to match and verified against the source (recount confirms 0 headingless-but-populated entries remain). The remaining freeze blockers are exclusively `review.status`/`complete_start` metadata, not extraction-shape gaps.
  - 2026-08-12: manually truthed the two previously called-out "empty-fields" blockers in `_src/tests/fixtures/spec_extraction/benchmark-draft.json`:
    - `RS_SAF_21101` is intentionally an inline citation in prose on pages 9-10 of `AUTOSAR_AP_RS_PlatformHealthManagement.pdf`, not a formal requirement block; `heading = null`, `fields = {}`, and `complete_start = null` are correct ground truth. Added an explanatory review note.
    - `RS_DIAG_04005` on page 15 of `AUTOSAR_FO_RS_Diagnostics.pdf` is a real formal requirement block (`[RS_Diag_04005] Manage Security Access level handling`); replaced the incorrect empty expected values with the actual heading/fields and `complete_start = true`, with a review note explaining the mixed-case source ID.
  - Recount after this truthing: exactly 12 headingless-but-populated benchmark entries remain, all in `AUTOSAR_FO_RS_LogAndTrace` (`RS_LT_00001`, `00002`, `00003`, `00004`, `00008`, `00028`, `00030`, `00031`, `00032`, `00033`, `00035`, `00037`). This cleanly overlaps with the separate TODO item to model dense definition lists as an explicit record shape.

### Definition-precision follow-ups

- [ ] Treat dense definition lists (heading inline, no spec-item marker, e.g. RS_PHM_00001..00003 p.21) as an explicit record shape with its own fixtures
  - 2026-08-12: implemented and shipped the `AUTOSAR_FO_RS_LogAndTrace` variant of this shape (numbered subsection line immediately above a bare `[RS_LT_xxxxx]` marker, e.g. `4.2.1.1.8 The LT shall ...` followed by `[RS_LT_00001] ⌈`) as `spec_scrape.py`'s new `_subsection_heading_before` fallback, commit `fdba7e28`. All 12 affected benchmark entries now have correct headings and the recount confirms 0 headingless-but-populated entries remain.
  - NOT yet verified: the originally cited `RS_PHM_00001..00003` example does not appear in `benchmark-draft.json` at all (no matching IDs found), so it's unconfirmed whether AUTOSAR_AP_RS_PlatformHealthManagement uses the exact same shape or a different one. This item stays open until that case (or another concrete instance beyond RS_LT) is located and confirmed handled.
