# DONE — Completed Features

Completed *Features* moved here from `TODO.md` once all of their *Tasks* are
marked `[x]`. Each entry keeps its original task text and completion
evidence; a completion date and `REF:` (git hash) are added at move time.

## Feature: Performance

Completed: 2026-08-12 15:27 CEST — REF: 1723c02b

- [x] benchmark, optimize and parallelize generate.py, validate.py, and lib_docmodel.py — 2026-08-12: `generate.py` parallelizes the German page workload using `ProcessPoolExecutor`, explicit macOS `fork` context, batched `map(..., chunksize=...)`, and `WORKERS=min(12, cpu_count)`; small targeted builds stay sequential to avoid pool overhead. `validate.py` parallelizes both German `check_build()` page validation and the dominant language-tree workload across all independent languages. `lib_docmodel.py` remains the pure worker-level renderer; no shared cache was added because separate processes cannot benefit from one and most records are read once per page. Verified by run.sh #253/#254: generate.py dropped from 11.14s to 1.49s for 424 pages (7.5x), with byte-identical output (`generate.py --check`: Abweichungen 0); validate.py dropped from 44.07s to 12.98s (3.4x), with user+sys CPU 33.55s exceeding 12.98s wall time, confirming Python-level multi-core execution. Validation findings remain unchanged: 3811 namespace-less records, tracked separately below.
- [x] optimize and parallelize extraction_report.py (single ProcessPoolExecutor pass over PDFs for all 4 categories, ThreadPoolExecutor for pdftoppm screenshots, WORKERS=min(12, cpu_count) per AGENTS.md job-level parallelism guidance) — 2026-08-12, verified via run.sh (#250) exit 0, 355 deviations reproduced identically to the pre-optimization baseline
- [x] fix run.sh incident from 2026-08-12: extraction_report.py build only writes page-model JSON, never publishes HTML; run.sh must always chain `build && python3 _src/generate.py`. Also made record_version() versions-neutral for unchanged republish runs to avoid duplicate versions (v0012/v0013 dedup incident). Docs updated: _src/WARTUNG.md ("Extraktions-Berichte: Bauen vs. Publizieren") and docs/pipeline/reports.md.

## Feature: Document Coverage

Completed: 2026-08-12 15:31 CEST — REF: 83a2c2da

- [x] investigate possible missing AUTOSAR Safety RS document — resolved 2026-08-12: the authoritative source is `AUTOSAR_FO_RS_Safety.pdf` (Foundation branch, requirements document). Earlier assumption that `AUTOSAR_FO_EXP_SafetyOverview.pdf` defines the `RS_SAF_*` records was wrong; that EXP document only references Safety requirements inline. `rs-saf` is now registered in `RS_DOCS` (`spec_scrape.py`) against `AUTOSAR_FO_RS_Safety`; the PDF still needs to be downloaded into `AUTOSAR/FOUNDATION/` and then re-run through `spec_scrape.py`. Also flagged: `AUTOSAR_AP_RS_HWTestManager`, `AUTOSAR_AP_SWS_OperatingSystemInterface`, `AUTOSAR_FO_PRS_IntrusionDetectionSystem`, `AUTOSAR_FO_PRS_TimeSyncOverEthernetProtocol` are cached but not yet registered in `DOCS`/`RS_DOCS`; also `RS_SOMEIP` has orphaned traceability records with no registered source document yet — needs the same treatment.


## Feature: Review & Feedback / Level 1 — Make Review Need Visible

Completed: 2026-08-12 15:31 CEST — REF: 83a2c2da


- [x] Open review need is visible at the top of the page as a notice
- [x] Notice states the number of affected API elements
- [x] Notice links via intra-page link directly to the

## Feature: 0003 — Dutch (nl) Translation

Completed: 2026-08-13 11:10 CEST — REF: 8bb8c67e

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
- [x] **0003-15** translate and merge `_src/i18n/work/nl/batch_15.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 199/199 entries completed and merged (2026-08-13, corrected after prior mislabeling — see 2026-08-13 note above), 0 rejects, no `fehler.json` produced. `python3 _src/i18n_translate.py merge nl` reported: übernommen 4655, abgelehnt 0, offen 0 (all languages fully translated per `i18n_translate.py status`).
- [x] **0003-16** translate and merge `_src/i18n/work/nl/batch_16.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 232/232 entries completed and merged (2026-08-13, corrected from earlier mislabeling), 0 rejects, no `fehler.json` produced.
- [x] **0003-17** translate and merge `_src/i18n/work/nl/batch_17.jsonl` into `_src/i18n/nl/{segments,labels}.json`; 1218/1218 entries completed and merged (2026-08-12), 0 rejects, no `fehler.json` produced (179 German-bearing labels translated; 1039 code/identifier-only labels passed through unchanged). HTML tree regeneration still pending.

## Feature: 0010 — Performance Package 2

Completed: 2026-08-14 11:48 CEST — REF: a44164f5

- [x] **0010-01** parallelize `validate.py` -- 2026-08-14: parallelized check_client_rendered_german() (per-language Node/WebKit calls) via ThreadPoolExecutor; check_build()/check_langs() were already parallelized via ProcessPoolExecutor. Pre-existing rc=1 (30 dead links under process.html in all languages) is unrelated and tracked separately. REF: 941b73a4
