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

## ID scheme

- *Feature names* are kept consistent in English (translate on introduction if needed).

- Every *Feature* gets a unique **feature ID**: a 4-digit number with leading zeroes, e.g. `0001`. Feature headings are written as `## Feature: XXXX — <name>`.

- Every *Task* within a feature gets a **task ID** `XXXX-YY`, where `XXXX` is the feature ID and `YY` is a 2-digit task number, unique within that feature (e.g. `0001-01`, `0001-02`). Task IDs are rendered in bold right after the checkbox marker, e.g. `- [ ] **0001-01** ...`.

- A *Task* may be split into **subtasks**, identified as `XXXX-YY.ZZ`, where `ZZ` is a 2-digit subtask number unique within that task (e.g. `0001-01.01`, `0001-01.02`).

- *Tasks* and *Features* may declare **prerequisites** — other tasks/features that must be done first. A prerequisite is written as:

  `XXXX(-YY)?:AAAA(-BB)?`

  - `XXXX` — feature ID of the dependent item (the one that has the prerequisite)
  - `-YY` — optional task number of the dependent item; omitted means the whole feature `XXXX` depends on it
  - `AAAA` — feature ID of the prerequisite (the one depended on)
  - `-BB` — optional task number of the prerequisite; omitted means the dependency is on the whole feature `AAAA`

  Examples:
  - `0002:0001` — Feature `0002` as a whole depends on Feature `0001` as a whole.
  - `0002-09:0001` — Task `0002-09` depends on Feature `0001` as a whole.
  - `0002-09:0001-08` — Task `0002-09` depends specifically on Task `0001-08`.
  - `0006-04.02:0006-04.01` — Subtask `0006-04.02` depends on sibling Subtask `0006-04.01`.

  Prerequisites are noted inline in the task/feature text, e.g. `PREREQ: 0002-09:0001-08`.

## Feature: 0001 — Traceable Build Reports for i18n and HTML

- [ ] **0001-01** define one canonical build-report schema for i18n + HTML publication runs, covering inputs, commands, timestamps, durations, exit codes, changed artifacts, fallback counts, reject counts, and validation findings
- [ ] **0001-02** decide where build reports live in source control vs generated output (`_src/`, `output/`, published HTML), and document retention/overwrite/archive rules
- [ ] **0001-03** extend the i18n pipeline so each `i18n_translate.py merge <lang>` run emits a machine-readable report with batch files consumed, accepted/rejected counts, `fehler.json` summary, and resulting register changes
- [ ] **0001-04** extend `i18n_diagrams.py` so each run emits a report of diagram sources considered, translated outputs written, unchanged outputs skipped, and stale translated SVGs deleted
- [ ] **0001-05** extend the HTML build/publication path so each `generate.py` run emits a machine-readable report with generated page counts per language, fallback-to-German counts, changed target files, and wall-clock duration
- [ ] **0001-06** PREREQ: 0001-06:0004-01, 0001-06:0006-13 — extend `validate.py` so each run emits a structured report with all checks performed, all findings grouped by category, and an explicit success/failure summary usable from automation
- [ ] **0001-07** PREREQ: 0001-07:0001-01, 0001-07:0001-03, 0001-07:0001-04, 0001-07:0001-05, 0001-07:0001-06 — add a runner-side orchestration step (via `run.sh` archive flow) that combines merge/diagram/build/validate subreports into one end-to-end publication report for a release/build run
- [ ] **0001-08** PREREQ: 0001-08:0001-07 — publish the combined build report into the generated HTML tree as a browsable report page with links to archived logs and referenced artifacts
- [ ] **0001-09** ensure the published report page links back to the corresponding `run.sh` archive (`run-<timestamp>-n<seq>.sh` + `.log`) so every generated artifact can be traced to its exact execution log
- [ ] **0001-10** add tests/fixtures for report generation and schema stability, including failure cases (rejects, stale diagrams, fallback translations, validate findings)
- [ ] **0001-11** update `_src/WARTUNG.md`, `docs/pipeline/actions.md`, `docs/pipeline/reports.md`, and `docs/pipeline/tools.md` so the build-report process is documented as a required part of i18n/HTML publication

## Feature: 0002 — Process Description in Published HTML

- [ ] **0002-01** define the target audience and scope of the published process description: curator/maintainer-facing operational documentation, not AGENT-only rules
- [ ] **0002-02** decide whether the process description should be a single static `nolang` page or a localized page family, and document the rationale
- [ ] **0002-03** design the page structure for the published process documentation: source of truth, i18n extraction/translation/merge, diagram translation, HTML generation, validation, reports, and traceability links
- [ ] **0002-04** create a dedicated page model under `_src/sources/pages/` for the process description and wire it into site navigation and indexes where appropriate
- [ ] **0002-05** describe the end-to-end i18n → diagrams → HTML → validate pipeline in the published page, including which artifacts are sources, which are generated, and which are only caches/work products
- [ ] **0002-06** describe how `run.sh` / `output/run-archive/` fit into traceability, including what can be reconstructed from archived script+log pairs and what cannot
- [ ] **0002-07** PREREQ: 0002-07:0006-09 — include a section explaining report artifacts (`fehler.json`, `i18n_translate.py status`, QA scans, validate findings, combined build reports) and where maintainers can inspect them
- [ ] **0002-08** include a section explaining failure handling: how to interpret rejects, fallback counts, stale diagrams, and validate errors without silently patching outputs
- [ ] **0002-09** PREREQ: 0002-09:0001 — add links from the published process page to the relevant repo documentation (`_src/WARTUNG.md`, `docs/pipeline/*.md`) and to representative generated report pages once Feature 1 exists
- [ ] **0002-10** ensure the published process page itself is covered by generate/validate and documented in repo-level maintenance docs

## Feature: 0003 — Dutch (nl) Translation

- [x] **0003-01** translate and merge `_src/i18n/work/nl/batch_01.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 202/202 entries completed and merged (2026-08-12), 0 rejects, no `fehler.json` produced. HTML tree regeneration still pending.
- [x] **0003-02** translate and merge `_src/i18n/work/nl/batch_02.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 215/215 entries completed and merged (2026-08-12), 0 rejects, no `fehler.json` produced.
- [x] **0003-03** translate and merge `_src/i18n/work/nl/batch_03.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 210/210 entries completed and merged (2026-08-13 verified), 0 rejects, no `fehler.json` produced.
- [x] **0003-04** translate and merge `_src/i18n/work/nl/batch_04.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 223/223 entries completed and merged (2026-08-13 verified), 0 rejects, no `fehler.json` produced.
- [x] **0003-05** translate and merge `_src/i18n/work/nl/batch_05.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 204/204 entries completed and merged (2026-08-13 verified), 0 rejects, no `fehler.json` produced.
- [x] **0003-06** translate and merge `_src/i18n/work/nl/batch_06.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 214/214 entries completed and merged (2026-08-13), 0 rejects, no `fehler.json` produced.
- [x] **0003-07** translate and merge `_src/i18n/work/nl/batch_07.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 215/215 entries completed and merged (2026-08-13), 0 rejects, no `fehler.json` produced.
- [x] **0003-08** translate and merge `_src/i18n/work/nl/batch_08.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 210/210 entries completed and merged (2026-08-13), 0 rejects, no `fehler.json` produced.
- [x] **0003-09** translate and merge `_src/i18n/work/nl/batch_09.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 225/225 entries completed and merged (2026-08-13), 0 rejects, no `fehler.json` produced. Pre-existing `.out.jsonl` was already translated; only the merge step was pending.
- [x] **0003-10** translate and merge `_src/i18n/work/nl/batch_10.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 192/192 entries completed and merged (2026-08-13), 0 rejects, no `fehler.json` produced. Pre-existing `.out.jsonl` was already translated; only the merge step was pending.
- [x] **0003-11** translate and merge `_src/i18n/work/nl/batch_11.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 205/205 entries completed and merged (2026-08-13), 0 rejects, no `fehler.json` produced. Pre-existing `.out.jsonl` was already translated; only the merge step was pending.
- [x] **0003-12** translate and merge `_src/i18n/work/nl/batch_12.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 226/226 entries completed and merged (2026-08-13), 0 rejects, no `fehler.json` produced. Pre-existing `.out.jsonl` was already translated; only the merge step was pending.
- [x] **0003-13** translate and merge `_src/i18n/work/nl/batch_13.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 229/229 entries completed and merged (2026-08-13), 0 rejects, no `fehler.json` produced. Pre-existing `.out.jsonl` was already translated; only the merge step was pending.
- [x] **0003-14** translate and merge `_src/i18n/work/nl/batch_14.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 236/236 entries completed and merged (2026-08-13), 0 rejects, no `fehler.json` produced. Pre-existing `.out.jsonl` was already translated; only the merge step was pending.
- [x] **0003-15** translate and merge `_src/i18n/work/nl/batch_15.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 199/199 entries completed and merged (2026-08-13, corrected after prior mislabeling — see 2026-08-13 note above), 0 rejects, no `fehler.json` produced. `python3 _src/i18n_translate.py merge nl` reported: übernommen 4655, abgelehnt 0, offen 0 (all languages fully translated per `i18n_translate.py status`).
- [x] **0003-16** translate and merge `_src/i18n/work/nl/batch_16.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 232/232 entries completed and merged (2026-08-13, corrected from earlier mislabeling), 0 rejects, no `fehler.json` produced.
- [x] **0003-17** translate and merge `_src/i18n/work/nl/batch_17.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 1218/1218 entries completed and merged (2026-08-12), 0 rejects, no `fehler.json` produced (179 German-bearing labels translated; 1039 code/identifier-only labels passed through unchanged). HTML tree regeneration still pending.

## Feature: 0004 — Data Quality

- [ ] **0004-01** PREREQ: 0004-01:0006 — investigate 3811 spec records without an explicit namespace (e.g. `SWS_AIDSM_10706`, `SWS_AIDSM_10301`, `SWS_AIDSM_10602`, `SWS_AIDSM_10205`, `SWS_AIDSM_10710`), flagged by `validate.py` (2026-08-12, run.sh #252). Currently causes `validate.py` to exit 1. Determine whether namespace should be inferred/backfilled during scrape/rebuild, or whether these records are legitimately namespace-less and validate.py's check needs an allowlist/exception similar to the existing PRS_E2E carve-out.

- [x] **0004-02** investigate 34 remaining SWS_UCM_* records without namespace data after fixing validate.py's check_namespaces() schema mismatch (2026-08-12, run.sh #265): all 34 are 'service method' records scoped to a service interface (e.g. SWS_UCM_00348 -> PackageManagement), suggesting the namespace-assignment tooling doesn't cover service-interface-scoped methods (unlike class-scoped methods, which populate namespace_meta correctly). Determine whether these need a namespace derived from the service interface's own namespace, or whether service methods are legitimately namespace-less and belong in spec/namespaces.json's 'abweichungen' catalog instead. -- RESOLVED 2026-08-12 (run.sh #268): confirmed via AUTOSAR spec research (SWS_CM_01005, EXP_ARAComAPI.pdf) that service methods MUST inherit their enclosing service interface's namespace (this is Path A, backfill, not a legitimate exception). Backfilled namespace_meta for all 34 records with source='ai-derived-from-service-interface' and review_status='pending' for curator confirmation; namespace-assignment tooling should be extended with this rule to prevent recurrence for future service-interface-scoped records.

## Feature: 0005 — Review & Feedback

- [ ] **0005-01** PREREQ: 0005-01:0006 — Requirement texts in the AUTOSAR AP documentation should be reviewable and approvable in a traceable way — directly in the published HTML documentation, without a separate tool and without a server component.

## Feature: 0006 — Unified Curation Platform

- [ ] **0006-01** From the curator's and user's perspective, review, feedback, and curation should not split into separate silos based on technical origin (scrape ambiguity vs. DB correction vs. AI amendment vs. AI-proposed new element). There should be one coherent, traceable lifecycle for "an item that needs human judgment", with stable identity across projects, full history, visible status, and both static and future dynamic presentation layers.

### Architecture decisions to make visible in code/data

- [ ] **0006-02** introduce a project-aware canonical identity scheme for every curatable item
  - Current gap (2026-08-12): records and queues are implicitly single-project (`_src/spec/records/<MODULE>/<ID>.json`, queue filenames = `<ID>.json`), and the docs contain no evidence of multi-project support for future AUTOSAR Classic / FOUNDATION / Eclipse S-Core expansion.
  - Decide and document a canonical key such as `project/release/kind/id` (example dimensions: `AUTOSAR/AP/R25-11/record/SWS_UCM_00348`, `AUTOSAR/FOUNDATION/R25-11/record/RS_SAF_00001`, `ECLIPSE/S-CORE/<release>/record/<id>`), then propagate it into record metadata, queue payloads, campaign manifests, and rendered HTML anchors.
  - Ensure the raw record `id` can remain human-familiar while the canonical identity becomes the cross-project stable key for queues, history, links, and reports.

- [ ] **0006-03** PREREQ: 0006-03:0006-02 — define one unified "curation item" schema that subsumes `review-flag@v1` and `curation-flag@v1`
  - Current gap: `review_flags.py` and `curation_flags.py` are near-duplicate but divergent queues with different payload shapes, different directory trees, and different semantics.
  - Design a single schema with at least: `schema`, `canonical_id`, `project`, `release`, `item_kind` (record-field / record / ai-amendment / ai-hypothesis / scrape-observation / report-entry), `origin` (tool / ai / browser / curator), `status` (open / claimed / proposed / accepted / rejected / superseded / applied), `subject`, `current_state`, `proposed_state`, `evidence`, `counter_evidence`, `decision_basis`, `campaign`, `created`, `claimed_by`, `decided_by`, `completed_at`, and `history`.
  - Make the schema expressive enough to represent: (a) scrape ambiguities, (b) DB-value corrections, (c) AI-generated amendments to existing records, (d) AI-proposed new spec elements / requirements currently only described as `hypothesized/unconfirmed` in the process docs.

- [ ] **0006-04** PREREQ: 0006-04:0006-03 — extend the record schema to carry stable provenance for curator-visible changes across all modules, not just pilot records
  - Current gap: `history[]`, `status`, and field-level states exist mostly in pilot-style records (`SWS_LOG` etc.), while many production records still only carry additive fields like `upstream` without matching lifecycle/history entries.
  - Make `status`, `history[]`, and (where applicable) field-level `fields.<name>.state/reason/trace` mandatory or mechanically backfillable for any write path (`spec_scrape.py`, `review_ingest.py`, `curation_ingest.py`, migrations, future AI-amendment tools).
  - Add explicit provenance for AI-originated proposals vs. curator-accepted DB changes so that "proposal" and "applied truth" remain distinguishable in static and dynamic views.

- [ ] **0006-05** PREREQ: 0006-05:0006-03 — add first-class support for AI-proposed NEW elements in the DB and queue model
  - Current gap: `hypothesized/unconfirmed` exists in docs as a status, but no implemented CLI or queue path creates such elements.
  - Define where hypotheses live before acceptance (separate hypothesis store vs. lightweight record stubs), how they get canonical IDs, how evidence is attached, and how acceptance promotes them into the main DB without losing history.

### Workflow / pipeline convergence

- [ ] **0006-06** PREREQ: 0006-06:0006-03 — converge browser review, queue review, AI proposals, and curator decisions into one end-to-end state machine
  - Current gap: the docs show two partially disconnected paths — queue-based (`review-queue` / `curation-queue` -> AI agent -> curator) and browser-based (`review.js` -> GitHub issue / JSON -> `*_ingest.py`).
  - Model one shared lifecycle with explicit states and transitions, including: discovered -> queued -> claimed -> proposed -> accepted/rejected -> applied -> published -> superseded.
  - Map every existing tool to that lifecycle (`review_flags.py`, `curation_flags.py`, `review_ingest.py`, `curation_ingest.py`, `spec_scrape.py`, future AI-amendment tools) and document which transitions each tool may perform.

- [ ] **0006-07** design a feedback loop from curator decision back into extraction/scrape/database logic
  - Current strength: `curation_flags.py` already assumes the output of a curation request is not just "data overwrite" but sometimes a code change or new residual rule.
  - Missing piece: a generalized, documented mechanism that can express whether a decision should update a DB value, create a migration, change parser logic, add an allowlist/exception, or spawn a new benchmark/fixture.
  - Add decision outcome classes and post-decision hooks so feedback scales beyond the extraction-report residual list.

- [ ] **0006-08** resurrect and implement campaign manifests as the versioning backbone for curation work
  - Current gap: `docs/pipeline/data-model.md` documents `_src/spec/campaigns/<id>.json`, but explicitly notes no such manifest files were found in the repo.
  - Use campaign manifests to version review/curation waves across projects/releases (source corpus hash, tool versions, queue snapshot, curator decisions, published reports) so a curator can later answer "which exact state of the corpus and tools produced this request?"

### Visibility / UX

- [ ] **0006-09** PREREQ: 0006-09:0006-03, 0006-09:0001-08 — build a static HTML "curation report" that renders all open and recent curation items from the queue(s)
  - Current gap: open flags in `_src/spec/curation-queue/open/` and `_src/spec/review-queue/open/` are invisible unless someone browses the filesystem.
  - Implement a `curation_report.py` (or broader `workflow_report.py`) analogous to `traceability_report.py`: read the queue(s), render a page model under `_src/sources/pages/`, publish via `generate.py`, and link it from the start page.
  - Each rendered item should show canonical identity, project/release, current DB state, proposed state, rationale, evidence, status, and links to the affected record/page/report.

- [ ] **0006-10** PREREQ: 0006-10:0006-09 — design the future dynamic JS/API view around the same schema, not a second ad-hoc model
  - Static HTML is needed first, but the future JS layer should consume the same canonical curation-item schema (serialized to JSON/JS) so filter/sort/group functionality does not fork the data model.
  - Plan for filters by project, release, queue status, item kind, module, source tool, curator, and campaign.

- [ ] **0006-11** expose curator-visible history for each DB element in published pages
  - Current gap: record pages do not systematically surface `history[]`, status evolution, or open review/curation state to users.
  - Add a visible section/badge on record pages showing current review/curation status, latest accepted decision, and links to the relevant curation item/report entry.
  - This should work for both existing records and future AI-proposed elements, with clear labeling of "proposed", "accepted", "rejected", and "applied".

### Hardening / migration

- [ ] **0006-12** PREREQ: 0006-12:0006-03 — inventory and migrate existing queue items and special-case review surfaces into the unified model
  - Inputs to cover: `review-queue`, `curation-queue`, extraction-report `RESIDUAL` items, ad-hoc TODO-driven investigations like the 34 service-method namespace conflict, and any pilot record-level `requirement_meta.review_*` states.
  - Define which of these become first-class curation items, which remain reports only, and which are historical artifacts to archive.

- [ ] **0006-13** PREREQ: 0006-13:0006-03, 0006-13:0006-06 — add validation and tests for the unified workflow model
  - Extend `validate.py` (or add a dedicated validator) to check canonical IDs, queue payload schema/version, allowed state transitions, referential integrity to records/pages, and history completeness.
  - Add fixtures covering at least: a scrape ambiguity, a DB correction request, an AI-generated amendment to an existing record, and a new hypothesized requirement.

- [ ] **0006-14** document the feature as a repo-level workflow contract before implementation spreads further
  - Update `docs/pipeline/{data-model,roles,actions,processes,reports,tools}.md` and `_src/SPEC_BUILD_PROCESS.md` so the unified curation model is the documented source of truth, not just emergent queue code.
  - Explicitly record what remains human-only, what AI may propose, and what tools may apply automatically.


## Feature: 0007 — Database Quality Assurance

### Campaign A — Baseline

- [ ] **0007-01** PREREQ: 0007-01:0006 — Freeze corpus and 200-record benchmark (still not freezable: `review.status = needs_review` on all 200 records, `complete_start = null` on many)
  - 2026-08-12: the 12 headingless-but-populated blockers (all `RS_LT_*`) are resolved. `spec_scrape.py`'s new numbered-subsection heading fallback (commit `fdba7e28`) recovers their real headings from the source PDF; `benchmark-draft.json`'s expected values were updated to match and verified against the source (recount confirms 0 headingless-but-populated entries remain). The remaining freeze blockers are exclusively `review.status`/`complete_start` metadata, not extraction-shape gaps.
  - 2026-08-12: manually truthed the two previously called-out "empty-fields" blockers in `_src/tests/fixtures/spec_extraction/benchmark-draft.json`:
    - `RS_SAF_21101` is intentionally an inline citation in prose on pages 9-10 of `AUTOSAR_AP_RS_PlatformHealthManagement.pdf`, not a formal requirement block; `heading = null`, `fields = {}`, and `complete_start = null` are correct ground truth. Added an explanatory review note.
    - `RS_DIAG_04005` on page 15 of `AUTOSAR_FO_RS_Diagnostics.pdf` is a real formal requirement block (`[RS_Diag_04005] Manage Security Access level handling`); replaced the incorrect empty expected values with the actual heading/fields and `complete_start = true`, with a review note explaining the mixed-case source ID.
  - Recount after this truthing: exactly 12 headingless-but-populated benchmark entries remain, all in `AUTOSAR_FO_RS_LogAndTrace` (`RS_LT_00001`, `00002`, `00003`, `00004`, `00008`, `00028`, `00030`, `00031`, `00032`, `00033`, `00035`, `00037`). This cleanly overlaps with the separate TODO item to model dense definition lists as an explicit record shape.

### Definition-precision follow-ups

- [ ] **0007-02** Treat dense definition lists (heading inline, no spec-item marker, e.g. RS_PHM_00001..00003 p.21) as an explicit record shape with its own fixtures
  - 2026-08-12: implemented and shipped the `AUTOSAR_FO_RS_LogAndTrace` variant of this shape (numbered subsection line immediately above a bare `[RS_LT_xxxxx]` marker, e.g. `4.2.1.1.8 The LT shall ...` followed by `[RS_LT_00001] ⌈`) as `spec_scrape.py`'s new `_subsection_heading_before` fallback, commit `fdba7e28`. All 12 affected benchmark entries now have correct headings and the recount confirms 0 headingless-but-populated entries remain.
  - NOT yet verified: the originally cited `RS_PHM_00001..00003` example does not appear in `benchmark-draft.json` at all (no matching IDs found), so it's unconfirmed whether AUTOSAR_AP_RS_PlatformHealthManagement uses the exact same shape or a different one. This item stays open until that case (or another concrete instance beyond RS_LT) is located and confirmed handled.

## Feature: 0008 — Cross-language HTML chrome bugs (untranslated review banner, wrong home link)

- [ ] **0008-01** PREREQ: 0008-01:0006-09 (soft — fix independently now, but content/placement likely rebuilt once 0006 lands) — extract the hardcoded German review-notice banner (`lib_docmodel.py`, `_review_page_enhancements()`: "%d API-Element%s mit Review-Bedarf" / "Vor der Freigabe müssen Requirement-Text und Zuordnung geprüft werden.") into the i18n segment/ui.json pipeline so it renders translated in all 9 non-German language trees instead of always German (found 2026-08-13 via nl screenshot, `ara::log` namespace page)
- [ ] **0008-02** fix the header logo/home link (`lib_docmodel.py::render_page`, key `"home": prefix + "index.html"`): it reuses the site-root-relative `prefix` (correct for shared assets like `style.css` that exist once at the tree root) instead of the language-root-relative depth used by `nav_html`'s breadcrumb "Start" link, so on every non-German page the logo link jumps one level too far up into the German root `index.html` instead of staying in `<lang>/index.html` (found 2026-08-13 via nl screenshot, `ara::log` namespace page)
- [ ] **0008-03** add a regression check to `validate.py` (or a dedicated test) that asserts, for every language tree, both the breadcrumb "Start" link and the header logo link resolve to that language's own `index.html`, not the German root
- [ ] **0008-04** add a regression check (scan or test) that flags any hardcoded German UI string in generated non-German HTML output, so future chrome/banner text additions can't silently bypass the i18n pipeline again
- [ ] **0008-05** PREREQ: 0008-05:0008-01, 0008-05:0008-02 — after fixing, rebuild and `--check` all 10 language trees (not just nl) since both bugs are structural to `render_page`/`_review_page_enhancements` and are not nl-specific
- [ ] **0008-06** document the requirement in `_src/WARTUNG.md` / `docs/pipeline/actions.md` that any new page-chrome text (banners, notices, badges) must go through `ui.json`/segment registers, not literal German strings in Python
